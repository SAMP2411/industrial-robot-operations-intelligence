from fastapi.testclient import TestClient

from apps.diagnostic_api.main import create_app
from packages.common.config import Settings
from packages.domain_models.database import get_session


def test_reviewer_disagreement_and_evidence_review_are_recorded(db_session, tmp_path):
    app = create_app(Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test"), initialize_schema=False)
    def session_override(): yield db_session
    app.dependency_overrides[get_session] = session_override
    client = TestClient(app)
    customer = client.post("/api/v1/customers", json={"name": "Synthetic"}).json()
    site = client.post("/api/v1/sites", json={"customer_id": customer["id"], "name": "Lab"}).json()
    engagement = client.post("/api/v1/diagnostic-engagements", json={"customer_id": customer["id"], "site_id": site["id"], "title": "Review"}).json()
    incident = client.post("/api/v1/incidents", json={"diagnostic_engagement_id": engagement["id"], "site_id": site["id"], "title": "Review", "started_at": "2026-01-01T00:00:00Z", "severity": "high"}).json()
    hypothesis = client.post(f"/api/v1/incidents/{incident['id']}/hypotheses", json={"title": "Primary", "failure_domain": "PLC/control", "analyst_owner": "analyst", "hypothesis_role": "primary"}).json()
    evidence = client.post(f"/api/v1/hypotheses/{hypothesis['id']}/evidence", json={"relation": "missing_expected", "analyst_note": "PLC export missing", "strength": "direct", "evidence_origin_group": "plc-export"}).json()["evidence"]
    review = client.post(f"/api/v1/hypotheses/{hypothesis['id']}/reviews", headers={"X-Role": "reviewer", "X-Actor": "reviewer@example"}, json={"decision": "change_confidence", "reviewer_confidence": .1, "note": "Evidence is incomplete"})
    assert review.status_code == 200 and review.json()["disagreement"] is True
    evidence_review = client.post(f"/api/v1/evidence/{evidence['id']}/review", headers={"X-Role": "reviewer"}, json={"review_status": "reviewed", "contradiction_resolution": "Missing item retained as limitation"})
    assert evidence_review.status_code == 200
    assert client.get(f"/api/v1/incidents/{incident['id']}/hypothesis-reviews").json()["items"][0]["reviewer"] == "reviewer@example"
