from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from packages.domain_models.models import Customer, DataSource, DiagnosticEngagement, RawRecord, Site
from packages.event_normalization import parse_timestamp
from packages.ingestion_core.service import IngestionService, sha256_bytes


ROOT = Path(__file__).resolve().parents[2]


def source(db_session):
    customer = Customer(name="Synthetic Customer")
    db_session.add(customer); db_session.flush()
    site = Site(customer_id=customer.id, name="Lab", timezone="UTC")
    db_session.add(site); db_session.flush()
    engagement = DiagnosticEngagement(customer_id=customer.id, site_id=site.id, title="Synthetic test")
    db_session.add(engagement); db_session.flush()
    item = DataSource(engagement_id=engagement.id, name="Robot export", source_type="robot_log")
    db_session.add(item); db_session.commit()
    return item


def test_file_hashing_is_stable():
    assert sha256_bytes(b"evidence") == "ee8250fb76e094b34b471f13a73dbbe51d1ae142e9df59d7c0d31ec20f0a0a8e"


@pytest.mark.parametrize(
    ("raw", "quality"),
    [("2026-04-07T09:13:02Z", "exact"), (1775553182, "converted"), ("2026-04-07 09:13:02", "converted")],
)
def test_timestamp_parsing(raw, quality):
    parsed = parse_timestamp(raw, source_timezone="Europe/Berlin")
    assert parsed.value is not None
    assert parsed.quality == quality


def test_invalid_timestamp_is_explicit():
    parsed = parse_timestamp("not-a-time")
    assert parsed.value is None
    assert "unparseable" in parsed.error


def test_preview_duplicate_detection_and_immutable_raw_record(db_session, tmp_path: Path):
    data_source = source(db_session)
    content = (ROOT / "fixtures/malformed_sources/first_sprint_robot_events.csv").read_bytes()
    service = IngestionService(db_session, tmp_path / "uploads")
    preview = service.preview(filename="robot.csv", content=content)
    assert preview.total_records == 4
    assert len(preview.validation_errors) == 1
    assert "UNRECOGNISED_VENDOR_CODE" in preview.unknown_event_codes

    run = service.create_run(data_source_id=data_source.id, filename="robot.csv", content=content, mime_type="text/csv", mapping={}, idempotency_key="same-file", actor="test")
    summary = service.commit(run.id, actor="test")
    assert summary["records_seen"] == 4
    assert summary["raw_records_created"] == 3
    assert summary["duplicates"] == 1
    assert summary["timestamp_errors"] == 1
    assert service.commit(run.id, actor="test") == summary

    raw = db_session.scalar(select(RawRecord))
    raw.payload = {"changed": True}
    with pytest.raises(ValueError, match="immutable"):
        db_session.commit()
    db_session.rollback()
