from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
import zipfile
import tracemalloc

import pytest

from apps.diagnostic_api.main import stage_upload
from packages.ingestion_core import IngestionService
from packages.ingestion_core.archive import extract_safe_zip
from packages.job_queue import DurableJobQueue


class ChunkedUpload:
    def __init__(self, chunks):
        self.chunks = iter(chunks)
        self.closed = False

    async def read(self, size):
        return next(self.chunks, b"")

    async def close(self):
        self.closed = True


class RepeatedUpload:
    def __init__(self, chunk: bytes, count: int):
        self.chunk = chunk
        self.remaining = count

    async def read(self, size):
        if not self.remaining:
            return b""
        self.remaining -= 1
        return self.chunk

    async def close(self):
        pass


def test_upload_staging_is_chunked_hashed_and_cleaned_on_limit(tmp_path):
    upload = ChunkedUpload([b"abc", b"def", b""])
    path, size, digest = asyncio.run(stage_upload(upload, tmp_path, 6))
    assert path.read_bytes() == b"abcdef"
    assert size == 6
    assert digest == hashlib.sha256(b"abcdef").hexdigest()
    assert upload.closed
    path.unlink()

    oversized = ChunkedUpload([b"1234", b"5678"])
    with pytest.raises(ValueError, match="size limit"):
        asyncio.run(stage_upload(oversized, tmp_path, 5))
    assert not list(tmp_path.glob("*.partial"))


def test_50mb_stream_peak_memory_does_not_scale_with_upload(tmp_path):
    chunk = b"x" * (1024 * 1024)
    tracemalloc.start()
    path, size, _ = asyncio.run(stage_upload(RepeatedUpload(chunk, 50), tmp_path, 60 * 1024 * 1024))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert size == 50 * 1024 * 1024
    assert peak < 8 * 1024 * 1024
    path.unlink()


def test_two_uploads_stage_concurrently_without_collision(tmp_path):
    async def both():
        return await asyncio.gather(
            stage_upload(RepeatedUpload(b"a" * 1024, 100), tmp_path, 200_000),
            stage_upload(RepeatedUpload(b"b" * 1024, 100), tmp_path, 200_000),
        )

    first, second = asyncio.run(both())
    assert first[0] != second[0]
    assert first[2] != second[2]
    first[0].unlink(); second[0].unlink()


def test_encoding_override_and_csv_edge_cases(db_session, tmp_path):
    content = (
        'event_time;message;message;asset_id\r\n'
        '2026-01-01T10:00:00Z;"door; blocked";caf\xe9;R-1\r\n'
    ).encode("windows-1252")
    preview = IngestionService(db_session, tmp_path).preview(
        filename="events.csv", content=content, encoding="windows-1252", mapping={"delimiter": ";"}
    )
    assert preview.detected_encoding == "windows-1252"
    assert preview.selected_encoding == "windows-1252"
    assert "message__2" in preview.columns
    assert preview.sample_records[0]["message"] == "door; blocked"
    assert preview.sample_records[0]["message__2"] == "café"
    assert preview.replacement_character_count == 0


def test_streaming_json_preview_supports_nested_field_paths(db_session, tmp_path):
    path = tmp_path / "nested.json"
    path.write_text(
        '[{"meta":{"time":"2026-01-01T10:00:00Z","asset":"R-1"},"event":{"code":"DOOR_OPEN"}}]',
        encoding="utf-8",
    )
    preview = IngestionService(db_session, tmp_path).preview_path(
        filename=path.name,
        path=path,
        mapping={
            "timestamp": {"field": "meta.time", "timezone": "UTC"},
            "asset_mapping": {"external_asset_id_field": "meta.asset"},
            "fields": {"event_code": {"from": "event.code"}},
        },
    )
    assert preview.total_records == 1
    assert preview.validation_errors == ()
    assert preview.unknown_event_codes == ()


def test_structured_text_pattern_reports_unmatched_lines(db_session, tmp_path):
    path = tmp_path / "events.log"
    path.write_text("2026-01-01T10:00:00Z|error|BLOCKED_PATH|R-1|stopped\nunmatched\n", encoding="utf-8")
    preview = IngestionService(db_session, tmp_path).preview_path(
        filename=path.name,
        path=path,
        mapping={
            "line_pattern": r"(?P<event_time>[^|]+)\|(?P<severity>[^|]+)\|(?P<event_code>[^|]+)\|(?P<asset_id>[^|]+)\|(?P<message>.*)"
        },
    )
    assert preview.total_records == 2
    assert preview.sample_records[1]["_normalization_issue"] == "structured text pattern did not match"


def test_safe_zip_preserves_hashes_and_rejects_traversal(tmp_path):
    archive = tmp_path / "bundle.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("robot/events.csv", "event_time,event_code\n2026-01-01T00:00:00Z,DOOR_OPEN\n")
    manifest = extract_safe_zip(archive, tmp_path / "safe")
    assert manifest["archive_sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
    assert manifest["files"][0]["relative_path"] == "robot/events.csv"

    malicious = tmp_path / "malicious.zip"
    with zipfile.ZipFile(malicious, "w") as bundle:
        bundle.writestr("../escape.csv", "bad")
    with pytest.raises(ValueError, match="unsafe archive"):
        extract_safe_zip(malicious, tmp_path / "unsafe")


def test_durable_job_queue_is_idempotent_and_audits_retry(db_session):
    queue = DurableJobQueue(db_session)
    job = queue.enqueue("ingest", {"run_id": "one"}, "same-key", max_retries=1)
    assert queue.enqueue("ingest", {"run_id": "two"}, "same-key").id == job.id
    claimed = queue.claim("worker-1")
    assert claimed.id == job.id and claimed.status == "running"
    queue.fail(claimed, RuntimeError("temporary storage outage"))
    assert claimed.status == "retrying"
    claimed.available_at = claimed.created_at
    db_session.commit()
    retry = queue.claim("worker-2")
    queue.complete(retry, {"records": 3})
    assert retry.status == "succeeded"
