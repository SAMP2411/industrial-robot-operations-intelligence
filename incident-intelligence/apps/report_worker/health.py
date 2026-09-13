from pathlib import Path
import sys

from packages.common import get_settings


if __name__ == "__main__":
    root = get_settings().report_root
    root.mkdir(parents=True, exist_ok=True)
    sys.exit(0 if root.is_dir() else 1)
