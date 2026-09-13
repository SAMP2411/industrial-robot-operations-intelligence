from __future__ import annotations

import os
from pathlib import Path
import subprocess

from sqlalchemy import create_engine, inspect, text


ROOT = Path(__file__).resolve().parents[2]


def _alembic(url, *args):
    env = {**os.environ, "RFII_DATABASE_URL": url}
    subprocess.run(["alembic", *args], cwd=ROOT, env=env, check=True, capture_output=True, text=True)


def test_clean_upgrade_and_one_revision_round_trip_preserve_data(tmp_path):
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    _alembic(url, "upgrade", "0006_buyer_reports")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO customers (id, schema_version, created_at, updated_at, name) VALUES ('c1','1.0',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,'Preserved')"))
    _alembic(url, "upgrade", "head")
    assert "deletion_receipts" in inspect(engine).get_table_names()
    with engine.connect() as connection: assert connection.scalar(text("SELECT name FROM customers WHERE id='c1'")) == "Preserved"
    _alembic(url, "downgrade", "0006_buyer_reports")
    assert "deletion_receipts" not in inspect(engine).get_table_names()
    _alembic(url, "upgrade", "head")


def test_single_migration_head_exists():
    result = subprocess.run(["alembic", "heads"], cwd=ROOT, check=True, capture_output=True, text=True)
    assert result.stdout.count("(head)") == 1
