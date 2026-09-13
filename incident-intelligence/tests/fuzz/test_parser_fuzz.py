from __future__ import annotations

import io
from pathlib import Path
import zipfile

from hypothesis import HealthCheck, given, settings, strategies as st

from packages.ingestion_core.service import _records
from packages.ingestion_core.archive import extract_safe_zip


@settings(max_examples=100, deadline=500)
@given(st.binary(max_size=2048))
def test_jsonl_parser_never_hangs_or_crashes_process(payload):
    try: _records(payload, "fuzz.jsonl")
    except (ValueError, UnicodeError, __import__('json').JSONDecodeError): pass


@settings(max_examples=50, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.text(min_size=1, max_size=100))
def test_zip_member_names_cannot_escape(tmp_path, name):
    archive = tmp_path / "fuzz.zip"
    try:
        if archive.exists(): archive.unlink()
        with zipfile.ZipFile(archive, "w") as bundle: bundle.writestr(name + ".csv", "a,b\n1,2\n")
        manifest = extract_safe_zip(archive, tmp_path / "out")
        assert all(".." not in Path(item["relative_path"]).parts and not Path(item["relative_path"]).is_absolute() for item in manifest["files"])
    except (ValueError, OSError, KeyError): pass
