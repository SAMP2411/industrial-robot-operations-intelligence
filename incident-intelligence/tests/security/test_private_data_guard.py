from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_private_workspace_and_export_patterns_are_ignored():
    gitignore = (ROOT / ".gitignore").read_text()
    assert "data/private/*" in gitignore
    assert "fixtures/private/" in gitignore
    assert "*.customer-export" in gitignore
    assert (ROOT / "data/private/.gitkeep").exists()


def test_ci_and_release_gate_run_private_data_scan():
    assert "scan_private_data.py" in (ROOT / ".github/workflows/quality.yml").read_text()
    assert "scan_private_data.py" in (ROOT / "scripts/release_gate.py").read_text()
