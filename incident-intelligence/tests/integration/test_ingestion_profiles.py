from __future__ import annotations

from fastapi.testclient import TestClient
import io
import zipfile

from apps.diagnostic_api.main import create_app
from packages.common.config import Settings
from packages.domain_models.database import get_session


def test_versioned_mapping_profile_and_encoding_metadata(db_session, tmp_path):
    app = create_app(Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test"), initialize_schema=False)

    def session_override():
        yield db_session

    app.dependency_overrides[get_session] = session_override
    client = TestClient(app)
    profile = {
        "name": "generic-semicolon",
        "version": "1.0",
        "source_type": "robot_log",
        "profile": {"name": "generic-semicolon", "profile_version": "1.0", "delimiter": ";"},
        "test_fixture": "fixtures/malformed_sources/semicolon_windows1252.csv",
        "compatibility_notes": "Generic example; not a named-vendor claim.",
    }
    assert client.post("/api/v1/mapping-profiles", json=profile).status_code == 200
    assert client.post("/api/v1/mapping-profiles", json=profile).status_code == 409
    assert client.get("/api/v1/mapping-profiles?source_type=robot_log").json()["items"][0]["version"] == "1.0"

    customer = client.post("/api/v1/customers", json={"name": "Synthetic"}).json()
    site = client.post("/api/v1/sites", json={"customer_id": customer["id"], "name": "Lab"}).json()
    engagement = client.post("/api/v1/diagnostic-engagements", json={"customer_id": customer["id"], "site_id": site["id"], "title": "Encoding"}).json()
    source = client.post(f"/api/v1/diagnostic-engagements/{engagement['id']}/sources", json={"name": "Export", "source_type": "robot_log"}).json()
    content = "event_time;event_code;message\n2026-01-01T00:00:00Z;DOOR_OPEN;café\n".encode("windows-1252")
    response = client.post(
        f"/api/v1/sources/{source['id']}/uploads",
        data={"encoding": "windows-1252", "mapping_yaml": "name: generic-semicolon\nprofile_version: '1.0'\ndelimiter: ';'"},
        files={"file": ("events.csv", content, "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["selected_encoding"] == "windows-1252"
    assert response.json()["mapping_profile_name"] == "generic-semicolon"


def test_job_error_details_are_admin_only(db_session, tmp_path):
    app = create_app(Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test"), initialize_schema=False)

    def session_override():
        yield db_session

    app.dependency_overrides[get_session] = session_override
    client = TestClient(app)
    job = client.post("/api/v1/jobs", json={"job_type": "ingest", "idempotency_key": "api-job", "payload": {}}).json()
    assert "error_details" not in client.get(f"/api/v1/jobs/{job['id']}").json()
    assert client.get(f"/api/v1/admin/jobs/{job['id']}", headers={"X-Role": "analyst"}).status_code == 403
    assert client.get(f"/api/v1/admin/jobs/{job['id']}", headers={"X-Role": "admin"}).status_code == 200


def test_safe_bundle_upload_returns_hash_manifest(db_session, tmp_path):
    app = create_app(Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test"), initialize_schema=False)

    def session_override():
        yield db_session

    app.dependency_overrides[get_session] = session_override
    client = TestClient(app)
    customer = client.post("/api/v1/customers", json={"name": "Synthetic"}).json()
    site = client.post("/api/v1/sites", json={"customer_id": customer["id"], "name": "Lab"}).json()
    engagement = client.post("/api/v1/diagnostic-engagements", json={"customer_id": customer["id"], "site_id": site["id"], "title": "Bundle"}).json()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        bundle.writestr("robot/events.csv", "event_time,event_code\n2026-01-01T00:00:00Z,DOOR_OPEN\n")
    response = client.post(
        f"/api/v1/diagnostic-engagements/{engagement['id']}/bundles",
        files={"file": ("evidence.zip", buffer.getvalue(), "application/zip")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["files"][0]["relative_path"] == "robot/events.csv"
