from __future__ import annotations

import os
import pytest
from sqlalchemy import create_engine, text


pytestmark = pytest.mark.skipif(not os.getenv("POSTGRES_TEST_URL"), reason="PostgreSQL CI only")


def test_constraints_indexes_and_skip_locked_are_available():
    engine = create_engine(os.environ["POSTGRES_TEST_URL"])
    with engine.begin() as connection:
        assert connection.scalar(text("SELECT count(*) FROM pg_indexes WHERE tablename='jobs'")) >= 3
        connection.execute(text("SELECT id FROM jobs WHERE status IN ('queued','retrying') FOR UPDATE SKIP LOCKED"))
        assert connection.scalar(text("SELECT count(*) FROM alembic_version")) == 1
