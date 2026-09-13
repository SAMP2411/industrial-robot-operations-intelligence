from pathlib import Path

import yaml

from apps.diagnostic_api.main import app


ROOT = Path(__file__).resolve().parents[2]


def test_startup_api_contains_no_robot_control_routes():
    forbidden = ("mission", "dispatch", "navigate", "teleop", "plc-write", "robot-control")
    paths = [route.path.casefold() for route in app.routes]
    assert not any(term in path for term in forbidden for path in paths)


def test_product_ui_exposes_no_mission_dispatch():
    ui = (ROOT / "apps/operator_console/index.html").read_text().casefold()
    assert "dispatch mission" not in ui
    assert "robot control" not in ui


def test_readme_declares_read_only_product():
    readme = (ROOT / "README.md").read_text().casefold()
    assert "read-only" in readme
    assert "not a robot-control product" in readme


def test_incident_api_does_not_import_autonomy_demo():
    source = "\n".join(path.read_text() for path in (ROOT / "apps/diagnostic_api").glob("*.py"))
    assert "autonomy_demo" not in source
    assert "rclpy" not in source


def test_synthetic_fixtures_are_visibly_labelled():
    manifests = sorted((ROOT / "fixtures").glob("incident_*/manifest.yaml"))
    assert manifests
    for manifest in manifests:
        assert yaml.safe_load(manifest.read_text()).get("simulated") is True


def test_report_requires_human_confirmation_for_causality():
    source = (ROOT / "apps/diagnostic_api/main.py").read_text()
    assert "human_approval_required" in source

