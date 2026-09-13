#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re


PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "IP": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "MAC": re.compile(r"\b(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}\b", re.I),
    "HOST": re.compile(r"\b(?:host|robot|pc|server)-[a-z0-9._-]+\b", re.I),
}


def pseudonym(kind: str, value: str, secret: bytes) -> str:
    token = hmac.new(secret, f"{kind}:{value}".encode(), hashlib.sha256).hexdigest()[:12]
    return f"{kind}_{token}"


def anonymize_text(text: str, secret: bytes, selected_values: list[str] | None = None) -> tuple[str, dict[str, str]]:
    mapping: dict[str, str] = {}
    for kind, pattern in PATTERNS.items():
        def replace(match):
            value = match.group(0); replacement = pseudonym(kind, value, secret); mapping[value] = replacement; return replacement
        text = pattern.sub(replace, text)
    for value in selected_values or []:
        replacement = pseudonym("SELECTED", value, secret); text = text.replace(value, replacement); mapping[value] = replacement
    return text, mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically pseudonymise an exported text/CSV/JSON/JSONL file")
    parser.add_argument("input", type=Path); parser.add_argument("output", type=Path)
    parser.add_argument("--secret-env", default="RFII_ANONYMISATION_SECRET")
    parser.add_argument("--selected-value", action="append", default=[])
    parser.add_argument("--mapping-output", type=Path, help="Optional sensitive reversible map; store separately from anonymised data")
    args = parser.parse_args(); secret_value = os.getenv(args.secret_env)
    if not secret_value or len(secret_value) < 16: raise SystemExit(f"{args.secret_env} must contain at least 16 characters")
    if args.input.resolve() == args.output.resolve(): raise SystemExit("input must not be overwritten")
    mapping: dict[str, str] = {}
    with args.input.open("r", encoding="utf-8", errors="strict") as source, args.output.open("x", encoding="utf-8") as destination:
        for line in source:
            transformed, found = anonymize_text(line, secret_value.encode(), args.selected_value); mapping.update(found); destination.write(transformed)
    if args.mapping_output:
        args.mapping_output.write_text(json.dumps(mapping, indent=2) + "\n"); args.mapping_output.chmod(0o600)
    print(json.dumps({"output": str(args.output), "replacements": len(mapping), "mapping_written": bool(args.mapping_output)})); return 0


if __name__ == "__main__": raise SystemExit(main())
