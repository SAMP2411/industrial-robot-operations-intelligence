from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from apps.diagnostic_api.main import create_app
from packages.common.config import Settings
from packages.domain_models.database import get_session


ROOT = Path(__file__).resolve().parents[2]


def test_api_preview_commit_and_rbac(db_session, tmp_path: Path):
    settings = Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test")
    app = create_app(settings, initialize_schema=False)

    def session_override():
        yield db_session

    app.dependency_overrides[get_session] = session_override
    client = TestClient(app)
    customer = client.post("/api/v1/customers", json={"name": "Synthetic"}).json()
    site = client.post("/api/v1/sites", json={"customer_id": customer["id"], "name": "Lab"}).json()
    registry = (
        ROOT.parent
        / "src/factory_inspection_mission/config/assets/benchmark_asset_registry.yaml"
    ).read_bytes()
    registry_response = client.post(
        f"/api/v1/sites/{site['id']}/asset-registry/import",
        files={"file": ("assets.yaml", registry, "application/yaml")},
    )
    assert registry_response.status_code == 200
    assert registry_response.json()["assets_imported"] >= 1
    engagement = client.post("/api/v1/diagnostic-engagements", json={"customer_id": customer["id"], "site_id": site["id"], "title": "Door event"}).json()
    source = client.post(f"/api/v1/diagnostic-engagements/{engagement['id']}/sources", json={"name": "Robot", "source_type": "robot_log"}).json()
    content = (ROOT / "fixtures/malformed_sources/first_sprint_robot_events.csv").read_bytes()
    preview = client.post(f"/api/v1/sources/{source['id']}/uploads/preview", files={"file": ("robot.csv", content, "text/csv")})
    assert preview.status_code == 200
    assert preview.json()["total_records"] == 4
    upload = client.post(f"/api/v1/sources/{source['id']}/uploads", headers={"Idempotency-Key": "fixture-1"}, files={"file": ("robot.csv", content, "text/csv")})
    assert upload.status_code == 200
    commit = client.post(f"/api/v1/ingestion-runs/{upload.json()['id']}/commit")
    assert commit.status_code == 200
    assert commit.json()["events_normalized"] == 3
    assert client.post("/api/v1/customers", headers={"X-Role": "viewer"}, json={"name": "Denied"}).status_code == 403
