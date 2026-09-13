from pathlib import Path

import pytest

from packages.ingestion_core.service import IngestionService, safe_filename


@pytest.mark.parametrize("name", ["../secret.csv", ".hidden.csv", "payload.exe", "", "../../a.json"])
def test_unsafe_file_names_are_rejected(name):
    if name in {"../secret.csv", "../../a.json"}:
        assert safe_filename(name) in {"secret.csv", "a.json"}
    else:
        with pytest.raises(ValueError):
            safe_filename(name)


def test_oversized_upload_is_rejected(db_session, tmp_path: Path):
    service = IngestionService(db_session, tmp_path, max_upload_bytes=4)
    with pytest.raises(ValueError, match="size limit"):
        service.preview(filename="a.csv", content=b"12345")


def test_dangerous_mime_type_is_rejected(db_session, tmp_path: Path):
    service = IngestionService(db_session, tmp_path)
    with pytest.raises(ValueError, match="MIME"):
        service.create_run(
            data_source_id="unused", filename="renamed.csv", content=b"a,b\n1,2\n",
            mime_type="application/x-msdownload", mapping={}, idempotency_key=None, actor="test",
        )
