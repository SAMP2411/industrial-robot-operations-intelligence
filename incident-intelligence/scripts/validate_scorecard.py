#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]


def validate(path: Path) -> list[str]:
    document = yaml.safe_load(path.read_text())
    errors: list[str] = []
    if document.get("scorecard_version") != "1.0":
        errors.append("scorecard_version must be 1.0")
    categories = document.get("categories")
    if not isinstance(categories, dict) or not categories:
        return errors + ["categories must be a non-empty mapping"]
    weight_total = 0
    score_total = 0
    for key, category in categories.items():
        weight = category.get("weight")
        score = category.get("score")
        target = category.get("target")
        if not all(isinstance(value, int) for value in (weight, score, target)):
            errors.append(f"{key}: weight, score, and target must be integers")
            continue
        weight_total += weight
        score_total += score
        if not 0 <= score <= target <= weight:
            errors.append(f"{key}: require 0 <= score <= target <= weight")
        evidence = category.get("evidence", [])
        if score and not evidence:
            errors.append(f"{key}: awarded score has no evidence")
        for reference in evidence:
            if not (ROOT / reference).exists():
                errors.append(f"{key}: missing evidence path {reference}")
    if weight_total != 100:
        errors.append(f"weights total {weight_total}, expected 100")
    expected = document.get("expected_total")
    if score_total != expected:
        errors.append(f"scores total {score_total}, expected_total is {expected}")
    commercial = categories.get("commercial_validation", {})
    if commercial.get("score", 0) > 1:
        evidence_text = " ".join(commercial.get("evidence", [])).casefold()
        if not any(marker in evidence_text for marker in ("payment", "pilot", "operator", "real_dataset")):
            errors.append("commercial score above baseline requires real validation evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=ROOT / "docs/scorecard/current_score.yaml")
    args = parser.parse_args()
    errors = validate(args.path)
    if errors:
        print("Scorecard validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    document = yaml.safe_load(args.path.read_text())
    total = sum(category["score"] for category in document["categories"].values())
    print(f"Scorecard valid: {total}/100")
    return 0


if __name__ == "__main__":
    sys.exit(main())

