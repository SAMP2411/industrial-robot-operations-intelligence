from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from packages.domain_models.models import Customer, DataSource, DiagnosticEngagement, IngestionRun, Site
from packages.ingestion_core import IngestionService
from packages.job_queue import DurableJobQueue


def _source(db_session):
    customer = Customer(name="Synthetic"); db_session.add(customer); db_session.flush()
    site = Site(customer_id=customer.id, name="Lab", timezone="UTC"); db_session.add(site); db_session.flush()
    engagement = DiagnosticEngagement(customer_id=customer.id, site_id=site.id, title="Fault"); db_session.add(engagement); db_session.flush()
    source = DataSource(engagement_id=engagement.id, name="Log", source_type="robot_log"); db_session.add(source); db_session.commit(); return source


def test_storage_failure_leaves_no_partial_evidence(db_session, tmp_path, monkeypatch):
    source = _source(db_session); service = IngestionService(db_session, tmp_path / "uploads")
    def fail(*args, **kwargs): raise OSError("simulated unavailable storage")
    monkeypatch.setattr("packages.ingestion_core.service.shutil.copyfile", fail)
    with pytest.raises(ValueError, match="storage write failed"):
        service.create_run(data_source_id=source.id, filename="events.csv", content=b"a,b\n1,2\n", mime_type="text/csv", mapping={}, idempotency_key="fault", actor="test")
    assert not db_session.query(IngestionRun).all()
    assert not list((tmp_path / "uploads").rglob("*.partial"))


def test_worker_crash_becomes_retrying_with_actionable_error(db_session):
    queue = DurableJobQueue(db_session); job = queue.enqueue("ingest", {}, "worker-crash", max_retries=2)
    queue.execute_one("worker", {"ingest": lambda payload: (_ for _ in ()).throw(RuntimeError("worker crashed mid-job"))})
    assert job.status == "retrying" and "worker crashed" in job.error_summary


def test_corrupt_preserved_file_is_detected_before_normalization(db_session, tmp_path):
    source = _source(db_session); service = IngestionService(db_session, tmp_path / "uploads", encryption_key=b"z" * 32, encryption_key_id="k1")
    run = service.create_run(data_source_id=source.id, filename="events.csv", content=b"event_time,event_code\n2026-01-01T00:00:00Z,DOOR_OPEN\n", mime_type="text/csv", mapping={}, idempotency_key="corrupt", actor="test")
    path = Path(run.storage_path); payload = bytearray(path.read_bytes()); payload[-17] ^= 1; path.write_bytes(payload)
    with pytest.raises(ValueError, match="integrity verification failed"): service.commit(run.id, actor="test")
    assert run.status != "committed"
