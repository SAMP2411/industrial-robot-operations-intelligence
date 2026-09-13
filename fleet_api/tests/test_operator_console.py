from __future__ import annotations

import json
from pathlib import Path
import textwrap

from fastapi.testclient import TestClient
import yaml

from fleet_api.app.main import AppSettings, create_app


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n")


def make_settings(tmp_path: Path) -> AppSettings:
    workspace_root = tmp_path / "workspace"
    fleetwatch_root = tmp_path / "fleetwatch"
    ui_path = Path(__file__).resolve().parents[1] / "ui" / "Fleetwatch.html"
    runtime_root = tmp_path / "runtime"

    site_config = workspace_root / "site.yaml"
    asset_registry = workspace_root / "assets.yaml"
    inspection_profiles = workspace_root / "inspection_profiles.yaml"

    write_yaml(
        site_config,
        """
        schema_version: site.v1
        site_id: demo_site
        name: Demo Factory
        timezone: UTC
        map_id: nav2_warehouse
        coordinate_frame: map
        status: ACTIVE
        metadata:
          environment: simulation
        """,
    )
    write_yaml(
        asset_registry,
        """
        schema_version: asset_registry.v1
        site_id: demo_site
        assets:
          - asset_id: CNV-510
            name: Packing Conveyor Drive
            asset_type: conveyor_drive
            zone: packing_lane
            priority: 3
            criticality: HIGH
            owner_team: packaging_ops
            inspection_profile_id: conveyor_drive_standard
            status: ACTIVE
            enabled_modalities: [visual, thermal, acoustic]
            tags: [benchmark, conveyor]
            checkpoint:
              name: spawn_lane
              x: 2.12
              y: -21.30
              yaw: 1.57
              viewpoint_id: vp_spawn_lane
              position_tolerance_m: 1.75
              orientation_tolerance_rad: 0.35
        """,
    )
    write_yaml(
        inspection_profiles,
        """
        schema_version: inspection_profile.v1
        profiles:
          - inspection_profile_id: conveyor_drive_standard
            asset_type: conveyor_drive
            required_skills: [visual_condition, external_measurement]
            frequency:
              interval_seconds: 3600
            viewpoints:
              - viewpoint_id: default_conveyor_view
                position_tolerance_m: 1.75
                orientation_tolerance_rad: 0.35
            thresholds:
              acoustic_threshold_db: 72.0
            escalation_policy_id: warning_then_hold_on_critical
        """,
    )

    write_json(
        runtime_root / "scenario" / "scenario_manifest.json",
        {
            "schema_version": "benchmark_scenario_manifest.v2",
            "scenario_id": "advanced_multimodal_seed_4242",
            "run_id": "run_001",
            "site": {"site_id": "demo_site", "name": "Demo Factory"},
        },
    )
    write_json(
        runtime_root / "latest_campaign_state.json",
        {
            "schema_version": "campaign_state.v2",
            "run_id": "run_001",
            "scenario_id": "advanced_multimodal_seed_4242",
            "asset_trends": [
                {
                    "asset_id": "CNV-510",
                    "latest_label": "roller_imbalance",
                    "latest_severity": "warning",
                    "latest_health_score": 76.0,
                    "average_confidence": 0.97,
                    "outstanding": True,
                    "latest_image_path": str(runtime_root / "annotated.png"),
                    "latest_annotated_image_path": str(runtime_root / "annotated.png"),
                }
            ],
        },
    )
    write_json(
        runtime_root / "round_0001_report.json",
        {
            "schema_version": "round_report.v2",
            "round_number": 1,
            "mission_profile": "single_robot_profile_validation",
            "scenario_id": "advanced_multimodal_seed_4242",
            "run_id": "run_001",
            "timestamp_ns": 7020000000,
            "success": True,
            "action_result": "SUCCEEDED",
            "nav2_error_code": 0,
            "critical_count": 0,
            "selected_assets": ["CNV-510"],
            "follow_up_assets": ["CNV-510"],
            "mission_decision": "TARGETED_FOLLOW_UP",
            "decision_reason": "Need follow-up inspection",
            "site_alert_level": "warning",
            "checkpoints": [
                {
                    "waypoint_index": 0,
                    "checkpoint_name": "spawn_lane",
                    "asset_id": "CNV-510",
                    "asset_display_name": "Packing Conveyor Drive",
                    "asset_type": "conveyor_drive",
                    "zone": "packing_lane",
                    "asset_priority": 3,
                    "enabled_modalities": ["visual", "acoustic"],
                    "anomaly_sources": ["visual", "acoustic"],
                    "inspection_label": "roller_imbalance",
                    "inspection_severity": "warning",
                    "inspection_confidence": 0.99,
                    "review_required": False,
                    "recommended_action": "schedule_recheck",
                    "health_score": 75.6,
                    "thermal_delta_c": 10.5,
                    "acoustic_db": 74.1,
                    "gas_ppm": 0.0,
                    "thermal_alert": False,
                    "acoustic_alert": True,
                    "gas_alert": False,
                    "is_anomaly": True,
                    "image_path": str(runtime_root / "annotated.png"),
                    "raw_image_path": str(runtime_root / "raw.png"),
                    "annotated_image_path": str(runtime_root / "annotated.png"),
                    "ground_truth_label": "roller_imbalance",
                    "ground_truth_severity": "warning",
                    "matches_ground_truth": True,
                    "pose": {"x": 2.12, "y": -21.3, "yaw": 1.57},
                    "note": "Synthetic warning for regression coverage",
                }
            ],
        },
    )

    (runtime_root / "annotated.png").write_bytes(b"fake-image")
    (runtime_root / "raw.png").write_bytes(b"fake-image")
    fleetwatch_root.mkdir(parents=True, exist_ok=True)

    return AppSettings(
        workspace_root=workspace_root,
        fleetwatch_root=fleetwatch_root,
        ui_path=ui_path,
        sqlite_path=tmp_path / "fleetwatch.db",
        runtime_root=runtime_root,
        operator_queue_path=tmp_path / "operator" / "operator_mission_queue.yaml",
        site_config_path=site_config,
        asset_registry_path=asset_registry,
        inspection_profiles_path=inspection_profiles,
        influx_url="http://localhost:8086",
        influx_token="",
        influx_org="startup-robot-dashboard",
        influx_bucket="robot_fleet",
        ingest_api_key="",
        demo_email="demo@fleetwatch.io",
        demo_password="test123",
        demo_company="FleetWatch Demo",
        demo_tenant_id="tenant_demo",
        secret_key="integration-test-secret",
        cors_origins=["http://localhost:8000"],
    )


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/token",
        data={"username": "demo@fleetwatch.io", "password": "test123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_operator_console_sync_and_finding_lifecycle(tmp_path: Path):
    app = create_app(make_settings(tmp_path))
    client = TestClient(app)
    headers = auth_headers(client)

    sync_response = client.post("/api/v1/sync/benchmark/latest", headers=headers)
    assert sync_response.status_code == 200
    sync_payload = sync_response.json()
    assert sync_payload["site_imported"] == 1
    assert sync_payload["asset_imported"] == 1
    assert sync_payload["finding_imported"] == 1

    sites_response = client.get("/api/v1/sites", headers=headers)
    assert sites_response.status_code == 200
    assert sites_response.json()["sites"][0]["site_id"] == "demo_site"

    assets_response = client.get("/api/v1/assets", headers=headers)
    assert assets_response.status_code == 200
    asset = assets_response.json()["assets"][0]
    assert asset["asset_id"] == "CNV-510"
    assert asset["outstanding"] is True

    findings_response = client.get("/api/v1/findings", headers=headers)
    assert findings_response.status_code == 200
    finding = findings_response.json()["findings"][0]
    finding_id = finding["finding_id"]
    evidence_id = finding["evidence_id"]
    assert finding["status"] == "OPEN"

    detail_response = client.get(f"/api/v1/findings/{finding_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["evidence"]["evidence_id"] == evidence_id

    ack_response = client.post(
        f"/api/v1/findings/{finding_id}/acknowledge",
        headers=headers,
        json={"note": "Seen by operator"},
    )
    assert ack_response.status_code == 200
    assert ack_response.json()["status"] == "ACKNOWLEDGED"

    assign_response = client.post(
        f"/api/v1/findings/{finding_id}/assign",
        headers=headers,
        json={"assignee": "maintenance.lead", "note": "Assign for action"},
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["status"] == "ASSIGNED"
    assert assign_response.json()["assigned_to"] == "maintenance.lead"

    reinspect_response = client.post(
        f"/api/v1/findings/{finding_id}/reinspect",
        headers=headers,
        json={"note": "Need confirmation", "priority": "high"},
    )
    assert reinspect_response.status_code == 200
    assert reinspect_response.json()["finding"]["status"] == "REINSPECTION_REQUESTED"
    reinspection_mission = reinspect_response.json()["linked_mission"]
    assert reinspection_mission["mission_type"] == "reinspection"

    operator_queue = yaml.safe_load(
        app.state.settings.operator_queue_path.read_text()
    )
    queued_missions = operator_queue["missions"]
    assert queued_missions[0]["status"] == "QUEUED"
    assert queued_missions[0]["mission_source"] == "operator_requested"
    assert queued_missions[0]["selected_assets"] == ["CNV-510"]

    queued_missions[0]["status"] = "COMPLETED"
    queued_missions[0]["run_id"] = "run_operator_001"
    queued_missions[0]["scenario_id"] = "advanced_multimodal_seed_4242"
    queued_missions[0]["round_number"] = 7
    queued_missions[0]["mission_profile"] = "operator_requested"
    queued_missions[0]["mission_decision"] = "TARGETED_FOLLOW_UP"
    queued_missions[0]["decision_reason"] = "Operator-triggered reinspection confirmed warning."
    queued_missions[0]["latest_result"] = {
        "round_number": 7,
        "success": True,
        "mission_decision": "TARGETED_FOLLOW_UP",
    }
    app.state.settings.operator_queue_path.write_text(
        yaml.safe_dump(operator_queue, sort_keys=False)
    )

    resolve_response = client.post(
        f"/api/v1/findings/{finding_id}/resolve",
        headers=headers,
        json={"resolution_note": "Cleared after maintenance"},
    )
    assert resolve_response.status_code == 200
    assert resolve_response.json()["status"] == "RESOLVED"

    missions_response = client.get("/api/v1/missions", headers=headers)
    assert missions_response.status_code == 200
    refreshed_reinspection = next(
        mission
        for mission in missions_response.json()["missions"]
        if mission["mission_id"] == reinspection_mission["mission_id"]
    )
    assert refreshed_reinspection["status"] == "COMPLETED"
    assert refreshed_reinspection["mission_profile"] == "operator_requested"
    assert refreshed_reinspection["metadata"]["latest_result"]["round_number"] == 7
    mission_types = {mission["mission_type"] for mission in missions_response.json()["missions"]}
    assert "reinspection" in mission_types
    assert "routine_round" in mission_types

    evidence_response = client.get(f"/api/v1/evidence/{evidence_id}", headers=headers)
    assert evidence_response.status_code == 200
    assert evidence_response.json()["annotated_url"].endswith("/annotated")
