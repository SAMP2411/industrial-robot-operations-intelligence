from pathlib import Path

import pytest

from packages.domain_models.models import AuditEvent, ReportArtifact


def test_audit_events_are_append_only(db_session):
    event = AuditEvent(actor="test", action="invariant", entity_type="test", details={}); db_session.add(event); db_session.commit()
    event.details = {"changed": True}
    with pytest.raises(ValueError, match="append-only"): db_session.commit()
    db_session.rollback()


def test_approved_reports_are_immutable(db_session, tmp_path):
    artifact = ReportArtifact(incident_id="incident", version=1, format="json", storage_path=str(tmp_path / "report.json"), sha256="0" * 64, immutable=True)
    db_session.add(artifact); db_session.commit(); artifact.sha256 = "1" * 64
    with pytest.raises(ValueError, match="immutable"): db_session.commit()
    db_session.rollback()
