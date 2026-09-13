#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/disallowed_unverified_claims.yaml"


def iter_files(scan_paths: list[str], excluded: list[str]):
    excluded_paths = [(ROOT / item).resolve() for item in excluded]
    for item in scan_paths:
        path = ROOT / item
        candidates = [path] if path.is_file() else path.rglob("*.md") if path.exists() else []
        for candidate in candidates:
            resolved = candidate.resolve()
            if any(resolved == blocked or blocked in resolved.parents for blocked in excluded_paths):
                continue
            yield candidate


def lint() -> list[str]:
    config = yaml.safe_load(CONFIG.read_text())
    markers = tuple(config["allowed_context_markers"])
    errors: list[str] = []
    for path in iter_files(config["scan_paths"], config.get("excluded_paths", [])):
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
            folded = line.casefold()
            for phrase in config["phrases"]:
                position = folded.find(phrase.casefold())
                if position < 0:
                    continue
                prefix = folded[:position]
                if not any(marker in prefix for marker in markers):
                    errors.append(f"{path.relative_to(ROOT)}:{number}: unverified claim '{phrase}'")
    return errors


if __name__ == "__main__":
    failures = lint()
    if failures:
        print("Product claim lint failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        raise SystemExit(1)
    print("Product claim lint passed")
