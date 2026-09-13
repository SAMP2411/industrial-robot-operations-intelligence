#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--version", required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    migrations = sorted(path.stem for path in Path("deployment/migrations/versions").glob("*.py") if not path.name.startswith("__"))
    manifest = {
        "version": args.version, "migrations": migrations,
        "deployment_guide": "deployment/on_prem/secure_install.md",
        "known_limitations": "docs/current_known_limitations.md",
        "security_contact": "SECURITY.md",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    }
    args.output.write_text(json.dumps(manifest, indent=2) + "\n"); return 0


if __name__ == "__main__": raise SystemExit(main())
