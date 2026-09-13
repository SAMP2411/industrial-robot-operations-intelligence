from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from packages.asset_mapping import match_asset
from packages.domain_models.models import (
    AuditEvent,
    CanonicalEvent,
    DataQualityIssue,
    DataSource,
    IngestionRun,
    RawRecord,
)
from packages.event_normalization import parse_timestamp
from packages.common.encryption import decrypt_file, encrypt_file


ALLOWED_EXTENSIONS = {".csv", ".json", ".jsonl", ".log", ".txt"}
ALLOWED_MIME_TYPES = {
    "text/csv", "application/csv", "application/json", "application/x-ndjson",
    "application/jsonl", "text/plain", "application/octet-stream",
}
KNOWN_SEVERITIES = {"info", "warning", "error", "critical", "unknown"}
DEFAULT_EVENT_CODES = {
    "NAVIGATION_RECOVERY",
    "BLOCKED_PATH",
    "MISSION_PAUSED",
    "MISSION_RESUMED",
    "WIFI_ROAM",
    "DOOR_RELEASE",
    "DOOR_OPEN",
    "CHARGING_STARTED",
    "CHARGING_CONTACT_LOST",
    "CHARGING_RECOVERED",
    "TASK_DELAYED",
    "TASK_RESUMED",
    "MAINTENANCE_ACTION",
}


@dataclass(frozen=True)
class MappingProfile:
    timestamp_field: str = "event_time"
    source_record_id_field: str = "record_id"
    asset_field: str = "asset_id"
    event_type_field: str = "event_type"
    event_code_field: str = "event_code"
    severity_field: str = "severity"
    message_field: str = "message"
    state_from_field: str = "state_from"
    state_to_field: str = "state_to"
    timezone: str = "UTC"
    timestamp_format: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "MappingProfile":
        value = value or {}
        timestamp = value.get("timestamp", {})
        identity = value.get("identity", {})
        asset_mapping = value.get("asset_mapping", {})
        fields = value.get("fields", {})

        def field_name(key: str, fallback: str) -> str:
            spec = fields.get(key, fallback)
            return str(spec.get("from", fallback) if isinstance(spec, dict) else spec)

        return cls(
            timestamp_field=str(timestamp.get("field", value.get("timestamp_field", "event_time"))),
            source_record_id_field=str(identity.get("source_record_id", "record_id")),
            asset_field=str(asset_mapping.get("external_asset_id_field", "asset_id")),
            event_type_field=field_name("event_type", "event_type"),
            event_code_field=field_name("event_code", "event_code"),
            severity_field=field_name("severity", "severity"),
            message_field=field_name("message", "message"),
            state_from_field=field_name("state_from", "state_from"),
            state_to_field=field_name("state_to", "state_to"),
            timezone=str(timestamp.get("timezone", value.get("timezone", "UTC"))),
            timestamp_format=timestamp.get("pattern") or value.get("timestamp_format"),
        )

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class Preview:
    format: str
    columns: tuple[str, ...]
    sample_records: tuple[dict[str, Any], ...]
    proposed_asset_mappings: tuple[dict[str, Any], ...]
    validation_errors: tuple[dict[str, Any], ...]
    records_skipped: int
    unknown_event_codes: tuple[str, ...]
    total_records: int
    detected_encoding: str
    selected_encoding: str
    encoding_confidence: float
    replacement_character_count: int
    decoding_warnings: tuple[str, ...]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_filename(filename: str) -> str:
    base = Path(filename).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    if not cleaned or cleaned.startswith(".") or Path(cleaned).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("unsupported or unsafe file name")
    return cleaned


def detect_encoding(content: bytes, override: str | None = None) -> tuple[str, str, float, tuple[str, ...]]:
    supported = {"utf-8", "utf-8-sig", "windows-1252", "cp1252", "iso-8859-1", "latin-1"}
    selected = (override or "").strip().lower()
    if selected and selected not in supported:
        raise ValueError(f"unsupported encoding override: {override}")
    if content.startswith(b"\xef\xbb\xbf"):
        detected, confidence = "utf-8-sig", 1.0
    else:
        try:
            content.decode("utf-8")
            detected, confidence = "utf-8", 1.0
        except UnicodeDecodeError:
            detected, confidence = "windows-1252", .7
    selected = selected or detected
    warnings = () if selected == detected else (f"analyst override changed {detected} to {selected}",)
    return detected, selected, confidence, warnings


def _records(content: bytes, filename: str, encoding: str | None = None, mapping: dict[str, Any] | None = None) -> tuple[str, list[dict[str, Any]]]:
    suffix = Path(filename).suffix.lower()
    _, selected, _, _ = detect_encoding(content, encoding)
    text = content.decode(selected, errors="replace")
    if suffix == ".csv":
        sample = text[:65536]
        delimiter = (mapping or {}).get("delimiter")
        if not delimiter:
            try:
                delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            except csv.Error:
                delimiter = ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter, restkey="_extra_fields", restval=None)
        headers = reader.fieldnames or []
        normalized: list[str] = []
        counts: dict[str, int] = {}
        for index, header in enumerate(headers, start=1):
            base = (header or "").strip() or f"_unnamed_{index}"
            counts[base] = counts.get(base, 0) + 1
            normalized.append(base if counts[base] == 1 else f"{base}__{counts[base]}")
        reader.fieldnames = normalized
        return "csv", [dict(row) for row in reader]
    if suffix == ".json":
        value = json.loads(text)
        rows = value if isinstance(value, list) else value.get("records", [value])
        while isinstance(rows, dict) and "records" in rows:
            rows = rows["records"]
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError("JSON must contain an object, an array of objects, or a records array")
        return "json", rows
    if suffix == ".jsonl":
        return "jsonl", [json.loads(line) for line in text.splitlines() if line.strip()]
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            parts = line.split(maxsplit=4)
            row = {
                "event_time": parts[0] if parts else "",
                "severity": parts[1] if len(parts) > 1 else "unknown",
                "event_code": parts[2] if len(parts) > 2 else "UNKNOWN",
                "asset_id": parts[3] if len(parts) > 3 else "",
                "message": parts[4] if len(parts) > 4 else line,
            }
        row["_source_line_number"] = line_number
        rows.append(row)
    return "text", rows


def _field(row: dict[str, Any], path: str, default: Any = None) -> Any:
    """Read a direct key or a dotted nested path without mutating source evidence."""
    if path in row:
        return row[path]
    value: Any = row
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def _json_array(stream: io.TextIOBase, chunk_size: int = 64 * 1024) -> Iterator[dict[str, Any]]:
    """Incrementally decode a top-level JSON array so memory follows record size."""
    decoder = json.JSONDecoder()
    buffer = ""
    eof = False
    started = False
    while True:
        if not eof and len(buffer) < chunk_size:
            chunk = stream.read(chunk_size)
            eof = not chunk
            buffer += chunk
        buffer = buffer.lstrip()
        if not started:
            if not buffer and eof:
                raise ValueError("JSON input is empty")
            if not buffer:
                continue
            if buffer[0] != "[":
                raise ValueError("streaming JSON input must be a top-level array")
            buffer = buffer[1:]
            started = True
            continue
        buffer = buffer.lstrip()
        if buffer.startswith("]"):
            return
        if buffer.startswith(","):
            buffer = buffer[1:].lstrip()
        try:
            value, end = decoder.raw_decode(buffer)
        except json.JSONDecodeError:
            if eof:
                raise ValueError("invalid or truncated JSON array")
            chunk = stream.read(chunk_size)
            eof = not chunk
            buffer += chunk
            continue
        if not isinstance(value, dict):
            raise ValueError("JSON arrays must contain objects")
        yield value
        buffer = buffer[end:]


def _iter_records_path(
    path: Path,
    filename: str,
    encoding: str,
    mapping: dict[str, Any] | None = None,
) -> tuple[str, Iterator[dict[str, Any]]]:
    suffix = Path(filename).suffix.lower()
    options = mapping or {}
    if suffix == ".csv":
        def csv_rows() -> Iterator[dict[str, Any]]:
            with path.open("r", encoding=encoding, errors="replace", newline="") as stream:
                sample = stream.read(65536)
                stream.seek(0)
                delimiter = options.get("delimiter")
                if not delimiter:
                    try:
                        delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
                    except csv.Error:
                        delimiter = ","
                reader = csv.DictReader(stream, delimiter=delimiter, restkey="_extra_fields", restval=None)
                headers = reader.fieldnames or []
                counts: dict[str, int] = {}
                normalized = []
                for index, header in enumerate(headers, start=1):
                    base = (header or "").strip() or f"_unnamed_{index}"
                    counts[base] = counts.get(base, 0) + 1
                    normalized.append(base if counts[base] == 1 else f"{base}__{counts[base]}")
                reader.fieldnames = normalized
                yield from (dict(row) for row in reader)
        return "csv", csv_rows()
    if suffix == ".json":
        def json_rows() -> Iterator[dict[str, Any]]:
            with path.open("r", encoding=encoding, errors="replace") as stream:
                first = ""
                while not first:
                    character = stream.read(1)
                    if not character:
                        raise ValueError("JSON input is empty")
                    if not character.isspace():
                        first = character
                stream.seek(0)
                if first == "[":
                    yield from _json_array(stream)
                    return
                value = json.load(stream)
                rows = value if isinstance(value, list) else value.get("records", [value])
                while isinstance(rows, dict) and "records" in rows:
                    rows = rows["records"]
                if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                    raise ValueError("JSON must contain an object, an array of objects, or a records array")
                yield from rows
        return "json", json_rows()
    if suffix == ".jsonl":
        def jsonl_rows() -> Iterator[dict[str, Any]]:
            with path.open("r", encoding=encoding, errors="replace") as stream:
                for line_number, line in enumerate(stream, start=1):
                    if not line.strip():
                        continue
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError(f"JSONL line {line_number} is not an object")
                    value.setdefault("_source_line_number", line_number)
                    yield value
        return "jsonl", jsonl_rows()

    def text_rows() -> Iterator[dict[str, Any]]:
        pattern_text = options.get("line_pattern") or options.get("structured_text_pattern")
        pattern = re.compile(str(pattern_text)) if pattern_text else None
        with path.open("r", encoding=encoding, errors="replace") as stream:
            for line_number, line in enumerate(stream, start=1):
                line = line.rstrip("\r\n")
                if not line.strip():
                    continue
                row: dict[str, Any]
                if pattern:
                    matched = pattern.search(line)
                    row = matched.groupdict() if matched else {
                        "message": line, "_normalization_issue": "structured text pattern did not match"
                    }
                else:
                    try:
                        value = json.loads(line)
                        if not isinstance(value, dict):
                            raise ValueError
                        row = value
                    except (json.JSONDecodeError, ValueError):
                        parts = line.split(maxsplit=4)
                        row = {"event_time": parts[0] if parts else "", "severity": parts[1] if len(parts) > 1 else "unknown", "event_code": parts[2] if len(parts) > 2 else "UNKNOWN", "asset_id": parts[3] if len(parts) > 3 else "", "message": parts[4] if len(parts) > 4 else line}
                row["_source_line_number"] = line_number
                yield row
    return "text", text_rows()


class IngestionService:
    def __init__(self, session: Session, storage_root: Path, max_upload_bytes: int = 25 * 1024 * 1024, *, encryption_key: bytes | None = None, encryption_key_id: str = ""):
        self.session = session
        self.storage_root = storage_root
        self.max_upload_bytes = max_upload_bytes
        self.encryption_key = encryption_key
        self.encryption_key_id = encryption_key_id

    def preview(self, *, filename: str, content: bytes, mapping: dict[str, Any] | None = None, encoding: str | None = None) -> Preview:
        safe_filename(filename)
        if len(content) > self.max_upload_bytes:
            raise ValueError("upload exceeds configured size limit")
        detected, selected, confidence, decoding_warnings = detect_encoding(content, encoding)
        format_name, rows = _records(content, filename, selected, mapping)
        profile = MappingProfile.from_dict(mapping)
        errors: list[dict[str, Any]] = []
        unknown_codes: set[str] = set()
        mappings: dict[str, dict[str, Any]] = {}
        for index, row in enumerate(rows, start=1):
            parsed = parse_timestamp(
                row.get(profile.timestamp_field),
                source_timezone=profile.timezone,
                custom_format=profile.timestamp_format,
            )
            if parsed.error:
                errors.append({"line": index, "field": profile.timestamp_field, "error": parsed.error})
            event_code = str(row.get(profile.event_code_field, "UNKNOWN"))
            if event_code not in DEFAULT_EVENT_CODES:
                unknown_codes.add(event_code)
            external_id = str(row.get(profile.asset_field, "") or "")
            if external_id and external_id not in mappings:
                matched = match_asset(self.session, external_id)
                mappings[external_id] = {
                    "external_asset_id": external_id,
                    "status": matched.status,
                    "asset_id": matched.asset_id,
                    "candidates": list(matched.candidates),
                }
        columns = tuple(dict.fromkeys(key for row in rows for key in row))
        return Preview(
            format_name,
            columns,
            tuple(rows[:10]),
            tuple(mappings.values()),
            tuple(errors),
            0,
            tuple(sorted(unknown_codes)),
            len(rows),
            detected,
            selected,
            confidence,
            content.decode(selected, errors="replace").count("\ufffd"),
            decoding_warnings,
        )

    def preview_path(self, *, filename: str, path: Path, mapping: dict[str, Any] | None = None, encoding: str | None = None) -> Preview:
        safe_filename(filename)
        if path.stat().st_size > self.max_upload_bytes:
            raise ValueError("upload exceeds configured size limit")
        with path.open("rb") as stream:
            sample = stream.read(65536)
        detected, selected, confidence, decoding_warnings = detect_encoding(sample, encoding)
        format_name, rows = _iter_records_path(path, filename, selected, mapping)
        profile = MappingProfile.from_dict(mapping)
        errors: list[dict[str, Any]] = []
        unknown_codes: set[str] = set()
        mappings: dict[str, dict[str, Any]] = {}
        samples: list[dict[str, Any]] = []
        columns: dict[str, None] = {}
        replacement_count = 0
        total = 0
        for total, row in enumerate(rows, start=1):
            if len(samples) < 10:
                samples.append(row)
            columns.update({key: None for key in row})
            replacement_count += json.dumps(row, default=str).count("\ufffd")
            parsed = parse_timestamp(_field(row, profile.timestamp_field), source_timezone=profile.timezone, custom_format=profile.timestamp_format)
            if parsed.error:
                errors.append({"line": total, "field": profile.timestamp_field, "error": parsed.error})
            event_code = str(_field(row, profile.event_code_field, "UNKNOWN") or "UNKNOWN")
            if event_code not in DEFAULT_EVENT_CODES:
                unknown_codes.add(event_code)
            external_id = str(_field(row, profile.asset_field, "") or "")
            if external_id and external_id not in mappings:
                matched = match_asset(self.session, external_id)
                mappings[external_id] = {"external_asset_id": external_id, "status": matched.status, "asset_id": matched.asset_id, "candidates": list(matched.candidates)}
        return Preview(format_name, tuple(columns), tuple(samples), tuple(mappings.values()), tuple(errors), 0, tuple(sorted(unknown_codes)), total, detected, selected, confidence, replacement_count, decoding_warnings)

    def create_run(
        self,
        *,
        data_source_id: str,
        filename: str,
        content: bytes,
        mime_type: str,
        mapping: dict[str, Any] | None,
        idempotency_key: str | None,
        actor: str,
        encoding: str | None = None,
    ) -> IngestionRun:
        filename = safe_filename(filename)
        if len(content) > self.max_upload_bytes:
            raise ValueError("upload exceeds configured size limit")
        if mime_type.lower().split(";", 1)[0] not in ALLOWED_MIME_TYPES:
            raise ValueError("unsupported MIME type")
        digest = sha256_bytes(content)
        with tempfile.NamedTemporaryFile(prefix="rfii-upload-", delete=False) as staged:
            staged.write(content)
            staged_path = Path(staged.name)
        try:
            return self.create_run_from_staged(
                data_source_id=data_source_id,
                filename=filename,
                staged_path=staged_path,
                size_bytes=len(content),
                digest=digest,
                mime_type=mime_type,
                mapping=mapping,
                idempotency_key=idempotency_key,
                actor=actor,
                encoding=encoding,
            )
        finally:
            staged_path.unlink(missing_ok=True)

    def create_run_from_staged(
        self,
        *,
        data_source_id: str,
        filename: str,
        staged_path: Path,
        size_bytes: int,
        digest: str,
        mime_type: str,
        mapping: dict[str, Any] | None,
        idempotency_key: str | None,
        actor: str,
        encoding: str | None = None,
    ) -> IngestionRun:
        filename = safe_filename(filename)
        if size_bytes > self.max_upload_bytes:
            raise ValueError("upload exceeds configured size limit")
        if mime_type.lower().split(";", 1)[0] not in ALLOWED_MIME_TYPES:
            raise ValueError("unsupported MIME type")
        if sha256_file(staged_path) != digest:
            raise ValueError("staged upload hash verification failed")
        key = idempotency_key or f"{data_source_id}:{digest}"
        existing = self.session.scalar(select(IngestionRun).where(IngestionRun.idempotency_key == key))
        if existing:
            return existing
        destination = self.storage_root / data_source_id / digest / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_destination = destination.with_suffix(destination.suffix + ".partial")
        try:
            if self.encryption_key:
                encrypt_file(staged_path, temporary_destination, key=self.encryption_key, key_id=self.encryption_key_id)
            else:
                shutil.copyfile(staged_path, temporary_destination)
            os.replace(temporary_destination, destination)
        except OSError as exc:
            temporary_destination.unlink(missing_ok=True)
            raise ValueError(f"evidence storage write failed: {exc}") from exc
        with staged_path.open("rb") as staged:
            sample = staged.read(65536)
        detected, selected, confidence, warnings = detect_encoding(sample, encoding)
        profile = mapping or {}
        run = IngestionRun(
            data_source_id=data_source_id,
            idempotency_key=key,
            source_filename=filename,
            storage_path=str(destination),
            mime_type=mime_type,
            size_bytes=size_bytes,
            file_sha256=digest,
            mapping_profile=profile,
            mapping_profile_name=profile.get("name"),
            mapping_profile_version=profile.get("profile_version") or profile.get("version"),
            detected_encoding=detected,
            selected_encoding=selected,
            encoding_confidence=confidence,
            replacement_character_count=0,
            decoding_warnings=list(warnings),
            encrypted_at_rest=bool(self.encryption_key),
            encryption_key_id=self.encryption_key_id or None,
        )
        self.session.add(run)
        self.session.flush()
        self.session.add(AuditEvent(actor=actor, action="upload", entity_type="ingestion_run", entity_id=run.id, details={"sha256": digest}))
        self.session.commit()
        return run

    def read_preserved(self, run: IngestionRun) -> bytes:
        if not run.encrypted_at_rest:
            return Path(run.storage_path).read_bytes()
        if not self.encryption_key:
            raise ValueError("encrypted evidence key is unavailable")
        with tempfile.NamedTemporaryFile(prefix="rfii-decrypted-", delete=False) as decrypted:
            decrypted_path = Path(decrypted.name)
        decrypted_path.unlink(missing_ok=True)
        try:
            decrypt_file(Path(run.storage_path), decrypted_path, key=self.encryption_key, expected_key_id=run.encryption_key_id or "")
            return decrypted_path.read_bytes()
        finally:
            decrypted_path.unlink(missing_ok=True)

    @contextmanager
    def preserved_path(self, run: IngestionRun) -> Iterator[Path]:
        if not run.encrypted_at_rest:
            yield Path(run.storage_path)
            return
        if not self.encryption_key:
            raise ValueError("encrypted evidence key is unavailable")
        with tempfile.NamedTemporaryFile(prefix="rfii-decrypted-", delete=False) as decrypted:
            decrypted_path = Path(decrypted.name)
        decrypted_path.unlink(missing_ok=True)
        try:
            decrypt_file(Path(run.storage_path), decrypted_path, key=self.encryption_key, expected_key_id=run.encryption_key_id or "")
            yield decrypted_path
        finally:
            decrypted_path.unlink(missing_ok=True)

    def commit(self, run_id: str, *, actor: str) -> dict[str, int]:
        run = self.session.get(IngestionRun, run_id)
        if run is None:
            raise KeyError(run_id)
        if run.status == "committed":
            return run.summary
        source = self.session.get(DataSource, run.data_source_id)
        if source is None:
            raise ValueError("data source does not exist")
        profile = MappingProfile.from_dict(run.mapping_profile)
        summary = {
            "records_seen": 0,
            "raw_records_created": 0,
            "events_normalized": 0,
            "records_skipped": 0,
            "unknown_assets": 0,
            "ambiguous_assets": 0,
            "unknown_event_codes": 0,
            "timestamp_errors": 0,
            "duplicates": 0,
        }
        with self.preserved_path(run) as path:
            _, rows = _iter_records_path(path, run.source_filename, run.selected_encoding, run.mapping_profile)
            self._commit_rows(run, source, rows, profile, summary)
        run.status = "committed"
        run.summary = summary
        self.session.add(AuditEvent(actor=actor, action="ingestion_commit", entity_type="ingestion_run", entity_id=run.id, details=summary))
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise ValueError("ingestion conflicted with an existing immutable raw record")
        return summary

    def _commit_rows(self, run: IngestionRun, source: DataSource, rows: Iterator[dict[str, Any]], profile: MappingProfile, summary: dict[str, int]) -> None:
        for line_number, row in enumerate(rows, start=1):
            summary["records_seen"] += 1
            payload = json.loads(json.dumps(row, sort_keys=True, default=str))
            payload_hash = sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
            duplicate = self.session.scalar(
                select(RawRecord).where(
                    RawRecord.ingestion_run_id == run.id,
                    RawRecord.payload_sha256 == payload_hash,
                )
            )
            if duplicate:
                summary["duplicates"] += 1
                continue
            raw_timestamp = _field(row, profile.timestamp_field)
            raw = RawRecord(
                ingestion_run_id=run.id,
                data_source_id=run.data_source_id,
                source_record_id=str(_field(row, profile.source_record_id_field) or "") or None,
                source_filename=run.source_filename,
                source_line_number=int(row.get("_source_line_number", line_number)),
                source_timestamp_raw=None if raw_timestamp is None else str(raw_timestamp),
                payload=payload,
                payload_sha256=payload_hash,
            )
            self.session.add(raw)
            self.session.flush()
            summary["raw_records_created"] += 1
            parsed = parse_timestamp(
                raw_timestamp,
                source_timezone=profile.timezone or source.timezone,
                custom_format=profile.timestamp_format,
                clock_offset_ms=source.clock_offset_ms,
            )
            if parsed.error:
                summary["timestamp_errors"] += 1
                self.session.add(DataQualityIssue(
                    engagement_id=source.engagement_id,
                    issue_type="unparseable_timestamp",
                    severity="warning",
                    description=f"{run.source_filename}:{line_number}: {parsed.error}",
                    source_id=source.id,
                ))
            match = match_asset(self.session, str(_field(row, profile.asset_field, "") or ""))
            if match.status == "unknown":
                summary["unknown_assets"] += 1
            elif match.status == "ambiguous":
                summary["ambiguous_assets"] += 1
                self.session.add(DataQualityIssue(
                    engagement_id=source.engagement_id,
                    issue_type="ambiguous_asset_mapping",
                    severity="warning",
                    description=f"Ambiguous asset mapping for {_field(row, profile.asset_field)}",
                    source_id=source.id,
                ))
            code = str(_field(row, profile.event_code_field, "UNKNOWN") or "UNKNOWN")
            if code not in DEFAULT_EVENT_CODES:
                summary["unknown_event_codes"] += 1
            severity = str(_field(row, profile.severity_field, "unknown") or "unknown").lower()
            event = CanonicalEvent(
                raw_record_id=raw.id,
                event_type=str(_field(row, profile.event_type_field, source.source_type) or source.source_type),
                event_code=code,
                event_time=parsed.value,
                event_time_original=None if raw_timestamp is None else str(raw_timestamp),
                time_quality=parsed.quality,
                clock_offset_ms=source.clock_offset_ms,
                severity=severity if severity in KNOWN_SEVERITIES else "unknown",
                asset_id=match.asset_id,
                message=str(_field(row, profile.message_field, "") or ""),
                state_from=_field(row, profile.state_from_field),
                state_to=_field(row, profile.state_to_field),
                attributes={key: value for key, value in row.items() if key not in profile.__dict__.values()},
            )
            self.session.add(event)
            summary["events_normalized"] += 1
