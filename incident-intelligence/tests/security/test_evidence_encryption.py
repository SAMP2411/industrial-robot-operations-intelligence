from __future__ import annotations

from packages.domain_models.models import Customer, DataSource, DiagnosticEngagement, Site
from packages.ingestion_core import IngestionService


def test_aes_gcm_evidence_is_not_plaintext_and_tampering_fails_closed(db_session, tmp_path):
    customer = Customer(name="Synthetic"); db_session.add(customer); db_session.flush()
    site = Site(customer_id=customer.id, name="Lab", timezone="UTC"); db_session.add(site); db_session.flush()
    engagement = DiagnosticEngagement(customer_id=customer.id, site_id=site.id, title="Encrypted"); db_session.add(engagement); db_session.flush()
    source = DataSource(engagement_id=engagement.id, name="Log", source_type="robot_log"); db_session.add(source); db_session.commit()
    content = b"event_time,event_code\n2026-01-01T00:00:00Z,DOOR_OPEN\n"
    service = IngestionService(db_session, tmp_path / "uploads", encryption_key=b"k" * 32, encryption_key_id="pilot-key-1")
    run = service.create_run(data_source_id=source.id, filename="events.csv", content=content, mime_type="text/csv", mapping={}, idempotency_key="encrypted", actor="analyst")
    preserved = __import__('pathlib').Path(run.storage_path)
    assert run.encrypted_at_rest and run.encryption_key_id == "pilot-key-1"
    assert content not in preserved.read_bytes()
    assert service.commit(run.id, actor="analyst")["events_normalized"] == 1
    data = bytearray(preserved.read_bytes()); data[-20] ^= 1; preserved.write_bytes(data)
    run.status = "previewed"; db_session.commit()
    try:
        service.commit(run.id, actor="analyst")
        assert False, "tampered ciphertext must fail"
    except ValueError as exc:
        assert "integrity verification failed" in str(exc)
