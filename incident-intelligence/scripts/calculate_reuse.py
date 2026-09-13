#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


COMPONENTS = ("ingestion", "mapping", "domain_logic", "timeline", "reporting", "deployment")


def calculate(values: dict) -> dict:
    reused = sum(float(values.get("reused_hours", {}).get(name, 0)) for name in COMPONENTS)
    customer_specific = sum(float(values.get("customer_specific_hours", {}).get(name, 0)) for name in COMPONENTS)
    manual = float(values.get("manual_transformation_hours", 0))
    denominator = reused + customer_specific + manual
    percentage = round(100 * reused / denominator, 2) if denominator else 0
    return {
        "reused_hours": reused, "customer_specific_hours": customer_specific,
        "manual_transformation_hours": manual, "denominator_hours": denominator,
        "reuse_percentage": percentage, "target_percentage": 70,
        "passes_target": percentage >= 70,
        "formula_version": "reuse.v1",
        "denominator_rule": "all reusable, customer-specific, and manual transformation implementation effort",
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("input", type=Path); parser.add_argument("--output", type=Path); args = parser.parse_args()
    result = calculate(json.loads(args.input.read_text()))
    output = json.dumps(result, indent=2) + "\n"
    if args.output: args.output.write_text(output)
    else: print(output, end="")
    return 0


if __name__ == "__main__": raise SystemExit(main())
