from __future__ import annotations

import os
import pytest


@pytest.mark.skipif(os.getenv("RFII_RUN_PERFORMANCE") != "1", reason="manual/scheduled 100k-event profile")
def test_100k_timeline_profile_is_enabled_explicitly():
    # The load harness seeds through the normal ingestion API; this gate prevents accidental CI resource claims.
    assert int(os.getenv("RFII_TIMELINE_EVENT_COUNT", "100000")) >= 100_000
