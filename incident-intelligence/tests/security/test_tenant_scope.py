from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from apps.diagnostic_api.main import create_app
from packages.common.config import Settings
from packages.domain_models.database import get_session
from packages.domain_models.models import ReportArtifact


def _client(db_session, tmp_path):
    app = create_app(Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test"), initialize_schema=False)
    def session_override(): yield db_session
    app.dependency_overrides[get_session] = session_override
    return TestClient(app)


def test_customer_scope_is_enforced_for_lists_writes_raw_reports_audit_and_jobs(db_session, tmp_path):
    client = _client(db_session, tmp_path)
    customers = [client.post("/api/v1/customers", json={"name": name}).json() for name in ("Tenant A", "Tenant B")]
    sites = [client.post("/api/v1/sites", json={"customer_id": customer["id"], "name": "Site"}).json() for customer in customers]
    engagements = [client.post("/api/v1/diagnostic-engagements", json={"customer_id": customer["id"], "site_id": site["id"], "title": "Diagnostic"}).json() for customer, site in zip(customers, sites)]
    incidents = [client.post("/api/v1/incidents", json={"diagnostic_engagement_id": engagement["id"], "site_id": site["id"], "title": "Incident", "description": "Scope fixture", "started_at": "2026-01-01T00:00:00Z"}).json() for engagement, site in zip(engagements, sites)]
    scoped_a = {"X-Role": "analyst", "X-Customer-ID": customers[0]["id"], "X-Actor": "analyst-a"}
    partner_a = {"X-Role": "partner", "X-Customer-ID": customers[0]["id"], "X-Actor": "partner-a"}
    assert [row["id"] for row in client.get("/api/v1/customers", headers=scoped_a).json()["items"]] == [customers[0]["id"]]
    assert client.get(f"/api/v1/incidents/{incidents[1]['id']}", headers=partner_a).status_code == 404
    assert client.patch(f"/api/v1/incidents/{incidents[1]['id']}", headers=scoped_a, json={"title": "Cross-tenant edit"}).status_code == 404

    report_path = tmp_path / "tenant-b-report.json"; report_path.write_text("{}")
    artifact = ReportArtifact(incident_id=incidents[1]["id"], version=1, format="json", storage_path=str(report_path), sha256="0" * 64)
    db_session.add(artifact); db_session.commit()
    assert client.get(f"/api/v1/reports/{artifact.id}", headers=partner_a).status_code == 404
    job = client.post("/api/v1/jobs", headers=scoped_a, json={"job_type": "ingest", "idempotency_key": "tenant-job", "payload": {}}).json()
    assert job["customer_id"] == customers[0]["id"]
    audit_items = client.get("/api/v1/audit", headers={**scoped_a, "X-Role": "admin"}).json()["items"]
    assert all(item["customer_id"] in {None, customers[0]["id"]} for item in audit_items)


def test_scoped_analyst_cannot_create_records_for_another_customer(db_session, tmp_path):
    client = _client(db_session, tmp_path)
    a = client.post("/api/v1/customers", json={"name": "A"}).json(); b = client.post("/api/v1/customers", json={"name": "B"}).json()
    response = client.post("/api/v1/sites", headers={"X-Customer-ID": a["id"]}, json={"customer_id": b["id"], "name": "Forbidden"})
    assert response.status_code == 404
