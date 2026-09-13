from __future__ import annotations

import json
import re
from typing import Any


PATTERNS = {
    "emails": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "mac": re.compile(r"\b(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}\b", re.I),
}


def redact(value: Any, rules: dict) -> tuple[Any, dict[str, int]]:
    """Redact a structured snapshot without mutating the preserved source evidence."""
    text = json.dumps(value, sort_keys=True)
    counts: dict[str, int] = {}
    for name, pattern in PATTERNS.items():
        if rules.get(name, False):
            text, counts[name] = pattern.subn(f"[REDACTED_{name.upper()}]", text)
    for secret in rules.get("customer_secrets", []):
        text, count = re.subn(re.escape(secret), "[REDACTED_SECRET]", text)
        counts["customer_secrets"] = counts.get("customer_secrets", 0) + count
    result = json.loads(text)
    for field in rules.get("selected_fields", []):
        _redact_field(result, field.split("."), counts)
    return result, counts


def _redact_field(value: Any, path: list[str], counts: dict[str, int]) -> None:
    if not path:
        return
    if isinstance(value, list):
        for item in value: _redact_field(item, path, counts)
    elif isinstance(value, dict) and path[0] in value:
        if len(path) == 1:
            value[path[0]] = "[REDACTED_FIELD]"; counts["selected_fields"] = counts.get("selected_fields", 0) + 1
        else:
            _redact_field(value[path[0]], path[1:], counts)
