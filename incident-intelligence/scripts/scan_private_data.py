#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import subprocess


DENIED_PATHS = ("data/private/", "fixtures/private/", "private_data/")
SENSITIVE = [re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), re.compile(rb"AKIA[0-9A-Z]{16}")]


def main() -> int:
    tracked = subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0")
    failures = []
    for encoded in filter(None, tracked):
        name = encoded.decode(errors="replace")
        if any(name.startswith(prefix) for prefix in DENIED_PATHS) and not name.endswith(".gitkeep"): failures.append(f"private path tracked: {name}")
        path = Path(name)
        if path.is_file() and path.stat().st_size <= 5 * 1024 * 1024:
            content = path.read_bytes()
            if any(pattern.search(content) for pattern in SENSITIVE): failures.append(f"secret-like content: {name}")
    for failure in failures: print(failure)
    return 1 if failures else 0


if __name__ == "__main__": raise SystemExit(main())
