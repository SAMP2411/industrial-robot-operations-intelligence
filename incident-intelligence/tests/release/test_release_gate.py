from pathlib import Path

from scripts.release_gate import REQUIRED


ROOT = Path(__file__).resolve().parents[2]


def test_release_gate_covers_required_evidence_classes():
    names = " ".join(REQUIRED)
    assert "sample_diagnostic" in names
    assert "release_checklist" in names
    assert "scorecard" in names


def test_container_runs_as_non_root_and_release_workflow_emits_sbom():
    dockerfile = (ROOT / "deployment/docker/Dockerfile").read_text()
    workflow = (ROOT / ".github/workflows/release.yml").read_text()
    assert "USER rfii" in dockerfile
    assert "sbom-action" in workflow
    assert "SHA256SUMS" in workflow
