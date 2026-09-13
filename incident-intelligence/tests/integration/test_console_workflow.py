from __future__ import annotations

from fastapi.testclient import TestClient

from apps.diagnostic_api.main import create_app
from packages.common.config import Settings
from packages.domain_models.database import get_session


def _client(db_session, tmp_path):
    settings = Settings("sqlite://", tmp_path / "storage", 1024 * 1024, ("http://localhost",), "test")
    app = create_app(settings, initialize_schema=False)

    def session_override():
        yield db_session

    app.dependency_overrides[get_session] = session_override
    return TestClient(app)


def test_engagement_intake_source_and_mapping_are_audited(db_session, tmp_path):
    client = _client(db_session, tmp_path)
    customer = client.post("/api/v1/customers", json={"name": "Example customer"}).json()
    site = client.post(
        "/api/v1/sites",
        json={"customer_id": customer["id"], "name": "Warehouse", "timezone": "Europe/London"},
    ).json()
    engagement = client.post(
        "/api/v1/diagnostic-engagements",
        json={
            "customer_id": customer["id"],
            "site_id": site["id"],
            "title": "Intermittent door block",
            "handling_basis": "customer_authorised_diagnostic",
            "intake_checklist": {
                "permission_confirmed": True,
                "expected_sources": ["robot/fleet log", "door/PLC export"],
            },
        },
    )
    assert engagement.status_code == 200
    assert engagement.json()["intake_checklist"]["permission_confirmed"] is True

    source = client.post(
        f"/api/v1/diagnostic-engagements/{engagement.json()['id']}/sources",
        json={"name": "Fleet export", "source_type": "fleet_log", "clock_offset_ms": 125},
    ).json()
    sources = client.get(f"/api/v1/diagnostic-engagements/{engagement.json()['id']}/sources").json()["items"]
    assert len(sources) == 1
    assert sources[0]["id"] == source["id"]
    assert sources[0]["clock_offset_ms"] == 125

    asset = client.post(
        "/api/v1/assets",
        json={"site_id": site["id"], "name": "Robot 7", "asset_type": "amr", "aliases": []},
    ).json()
    decision = client.post(
        "/api/v1/asset-mappings",
        json={
            "engagement_id": engagement.json()["id"],
            "external_identifier": "RBT-007",
            "target_type": "asset",
            "asset_id": asset["id"],
            "match_method": "analyst_confirmation",
            "rationale": "Serial number confirmed by the site asset register.",
        },
    )
    assert decision.status_code == 200
    assert client.get("/api/v1/assets").json()["items"][0]["aliases"] == ["RBT-007"]
    assert len(client.get(f"/api/v1/diagnostic-engagements/{engagement.json()['id']}/asset-mappings").json()["items"]) == 1


def test_console_page_exposes_full_workflow_and_role_controls(db_session, tmp_path):
    client = _client(db_session, tmp_path)
    page = client.get("/")
    assert page.status_code == 200
    for marker in (
        "Guided engagement creation",
        "Upload and preview workspace",
        "Asset and system mapping review",
        "Chronological timeline",
        "Downtime segment",
        "Hypothesis review",
        "Data-quality assessment",
        "Reviewer approval",
        "Vendor package builder",
    ):
        assert marker in page.text
    assert 'aria-live="polite"' in page.text
    assert 'data-permission="approve"' in page.text


def test_mapping_requires_a_target_for_asset_decisions(db_session, tmp_path):
    client = _client(db_session, tmp_path)
    customer = client.post("/api/v1/customers", json={"name": "Example"}).json()
    site = client.post("/api/v1/sites", json={"customer_id": customer["id"], "name": "Site"}).json()
    engagement = client.post(
        "/api/v1/diagnostic-engagements",
        json={"customer_id": customer["id"], "site_id": site["id"], "title": "Test"},
    ).json()
    response = client.post(
        "/api/v1/asset-mappings",
        json={
            "engagement_id": engagement["id"],
            "external_identifier": "UNKNOWN-1",
            "target_type": "asset",
            "match_method": "analyst_confirmation",
            "rationale": "Needs a target.",
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "asset_id_required"
