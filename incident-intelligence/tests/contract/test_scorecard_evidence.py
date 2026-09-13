from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_scorecard_is_evidence_backed_and_totals_current_91():
    result = subprocess.run([sys.executable, "scripts/validate_scorecard.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "91/100" in result.stdout


def test_unverified_claim_lint_passes_product_documents():
    result = subprocess.run([sys.executable, "scripts/lint_product_claims.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_awarded_category_has_existing_evidence():
    scorecard = yaml.safe_load((ROOT / "docs/scorecard/current_score.yaml").read_text())
    for category in scorecard["categories"].values():
        if category["score"]:
            assert category["evidence"]
            assert all((ROOT / reference).exists() for reference in category["evidence"])
