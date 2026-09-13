from fastapi.testclient import TestClient

from apps.diagnostic_api.main import create_app
from packages.common.config import Settings
from packages.domain_models.database import get_session


def test_lifecycle_group_and_recovery_api(db_session, tmp_path):
    app = create_app(Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test"), initialize_schema=False)

    def session_override(): yield db_session
    app.dependency_overrides[get_session] = session_override
    client = TestClient(app)
    customer = client.post("/api/v1/customers", json={"name": "Synthetic"}).json()
    site = client.post("/api/v1/sites", json={"customer_id": customer["id"], "name": "Lab"}).json()
    engagement = client.post("/api/v1/diagnostic-engagements", json={"customer_id": customer["id"], "site_id": site["id"], "title": "Timing"}).json()
    incident = client.post("/api/v1/incidents", json={"diagnostic_engagement_id": engagement["id"], "site_id": site["id"], "title": "Timing", "started_at": "2026-07-19T08:00:00Z"}).json()
    for marker, time in (("occurred_at", "2026-07-19T08:00:00Z"), ("detected_at", "2026-07-19T08:01:34Z")):
        response = client.post(f"/api/v1/incidents/{incident['id']}/lifecycle-markers", json={"marker_type": marker, "occurred_at": time, "source": "synthetic fixture", "evidence_links": ["fixture-1"]})
        assert response.status_code == 200
    metrics = client.get(f"/api/v1/incidents/{incident['id']}/metrics").json()
    assert next(item for item in metrics["lifecycle"] if item["metric"] == "time_to_detection")["seconds"] == 94
    assert client.post(f"/api/v1/incidents/{incident['id']}/recovery-milestones", json={"milestone_type": "business_process_recovery", "occurred_at": "2026-07-19T08:20:00Z", "source": "throughput report"}).status_code == 200
    assert client.post(f"/api/v1/incidents/{incident['id']}/event-groups", json={"title": "Retry cycle", "group_type": "retry_cycle", "event_ids": ["event-1"]}).status_code == 200
    assert client.get(f"/api/v1/incidents/{incident['id']}/event-groups").json()["items"][0]["title"] == "Retry cycle"
