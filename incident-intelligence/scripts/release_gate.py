#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


REQUIRED = [
    "docs/sample_diagnostic/diagnostic_report.pdf", "docs/sample_diagnostic/diagnostic_report.html",
    "docs/releases/release_checklist.md", "docs/scorecard/current_score.yaml",
]


def run(command: list[str], failures: list[str]) -> None:
    result = subprocess.run(command, text=True)
    if result.returncode: failures.append("command failed: " + " ".join(command))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--sbom", type=Path); parser.add_argument("--skip-tests", action="store_true"); args = parser.parse_args()
    failures = [f"missing required release artifact: {path}" for path in REQUIRED if not Path(path).exists()]
    if args.sbom and not args.sbom.exists(): failures.append(f"SBOM missing: {args.sbom}")
    run([sys.executable, "scripts/validate_scorecard.py"], failures)
    run([sys.executable, "scripts/lint_product_claims.py"], failures)
    run([sys.executable, "scripts/scan_private_data.py"], failures)
    run([sys.executable, "-m", "alembic", "heads"], failures)
    if not args.skip_tests: run([sys.executable, "-m", "pytest", "-q"], failures)
    state = {"status": "failed" if failures else "passed", "failures": failures}
    print(json.dumps(state, indent=2))
    return 1 if failures else 0


if __name__ == "__main__": raise SystemExit(main())
