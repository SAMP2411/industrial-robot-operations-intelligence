from fastapi.testclient import TestClient

from apps.diagnostic_api.main import create_app
from packages.common.config import Settings
from packages.domain_models.database import get_session


def test_dataset_fingerprint_exposes_no_contents_and_tracks_effort(db_session, tmp_path):
    app = create_app(Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test"), initialize_schema=False)
    def session_override(): yield db_session
    app.dependency_overrides[get_session] = session_override
    client = TestClient(app)
    customer = client.post("/api/v1/customers", json={"name": "Private customer"}).json()
    site = client.post("/api/v1/sites", json={"customer_id": customer["id"], "name": "Private site"}).json()
    engagement = client.post("/api/v1/diagnostic-engagements", json={"customer_id": customer["id"], "site_id": site["id"], "title": "Private diagnostic"}).json()
    headers = {"X-Customer-ID": customer["id"], "X-Actor": "intake-analyst"}
    registration = client.post("/api/v1/datasets", headers=headers, json={
        "dataset_id": "DS-PSEUDONYM-001", "engagement_id": engagement["id"], "file_count": 2,
        "source_categories": ["robot_log", "operator_note"], "hashes": ["a" * 64, "b" * 64],
        "time_range": {"start": "2026-01-01T00:00:00Z", "end": "2026-01-01T01:00:00Z"},
        "customer_pseudonym": "CUSTOMER_7A", "access_list": ["analyst-1"],
        "private_workspace_reference": "offline-workspace://case-001", "retention_until": "2026-08-01T00:00:00Z",
    })
    assert registration.status_code == 200, registration.text
    record = registration.json(); assert record["customer_id"] == customer["id"]
    effort = client.post(f"/api/v1/datasets/{record['id']}/import-effort", headers=headers, json={
        "source_category": "robot_log", "mapping_minutes": 30, "code_change_minutes": 15,
        "manual_cleanup_minutes": 10, "unknown_fields": ["vendor_state"], "reusable_percentage": 80,
        "blocked_fields": [], "analyst_minutes": 40, "developer_minutes": 15,
    })
    assert effort.status_code == 200
    summary = client.get(f"/api/v1/datasets/{record['id']}/import-effort", headers=headers).json()
    assert summary["total_person_minutes"] == 55 and summary["average_reusable_percentage"] == 80
    listing = client.get("/api/v1/datasets", headers=headers).json()
    assert listing["contents_exposed"] is False
    assert "contents" not in listing["items"][0]
