#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from packages.connector_sdk.testing import certify_connector


def main() -> int:
    parser = argparse.ArgumentParser(description="Certify a read-only evidence connector")
    parser.add_argument("connector", help="module:attribute connector object")
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    module_name, attribute = args.connector.split(":", 1)
    connector = getattr(importlib.import_module(module_name), attribute)
    result = certify_connector(connector, args.fixture.read_bytes())
    print(json.dumps(result.__dict__, indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
