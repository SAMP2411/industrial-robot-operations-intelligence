from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
import io

from hypothesis import given, strategies as st

from packages.event_normalization import parse_timestamp
from packages.ingestion_core.service import _records, safe_filename


@given(st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31), timezones=st.just(timezone.utc)))
def test_iso_timestamp_round_trip(value):
    parsed = parse_timestamp(value.isoformat().replace("+00:00", "Z"))
    assert parsed.value == value
    assert parsed.quality == "exact"


@given(st.integers(min_value=-86_400_000, max_value=86_400_000))
def test_clock_offset_is_exact_millisecond_delta(offset):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    parsed = parse_timestamp(base.isoformat(), clock_offset_ms=offset)
    assert parsed.value == base + timedelta(milliseconds=offset)


@given(
    delimiter=st.sampled_from([",", ";", "\t", "|"]),
    message=st.text(alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00\r\n"), max_size=80),
)
def test_csv_delimiters_and_quotes_round_trip(delimiter, message):
    stream = io.StringIO(); writer = csv.writer(stream, delimiter=delimiter); writer.writerow(["event_time", "message"]); writer.writerow(["2026-01-01T00:00:00Z", message])
    _, rows = _records(stream.getvalue().encode(), "events.csv", mapping={"delimiter": delimiter})
    assert rows[0]["message"] == message


@given(st.text(min_size=1, max_size=80))
def test_untrusted_filename_never_escapes_basename(value):
    try:
        result = safe_filename(value + ".csv")
    except ValueError:
        return
    assert "/" not in result and "\\" not in result and not result.startswith(".")
