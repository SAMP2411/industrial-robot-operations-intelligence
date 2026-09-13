from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ParsedTimestamp:
    value: datetime | None
    quality: str
    error: str | None = None


def parse_timestamp(
    raw: object,
    *,
    source_timezone: str = "UTC",
    custom_format: str | None = None,
    clock_offset_ms: int = 0,
) -> ParsedTimestamp:
    if raw is None or str(raw).strip() == "":
        return ParsedTimestamp(None, "unknown", "missing timestamp")
    try:
        if isinstance(raw, (int, float)) or str(raw).strip().replace(".", "", 1).isdigit():
            number = float(raw)
            if number > 100_000_000_000:
                number /= 1000.0
            parsed = datetime.fromtimestamp(number, timezone.utc)
            quality = "converted"
        elif custom_format:
            parsed = datetime.strptime(str(raw), custom_format)
            quality = "converted"
        else:
            text = str(raw).strip().replace("Z", "+00:00")
            parsed = datetime.fromisoformat(text)
            quality = "exact" if parsed.tzinfo else "converted"
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo(source_timezone))
        parsed = parsed.astimezone(timezone.utc) + timedelta(milliseconds=clock_offset_ms)
        return ParsedTimestamp(parsed, quality)
    except (ValueError, TypeError, OverflowError) as exc:
        return ParsedTimestamp(None, "unknown", f"unparseable timestamp: {exc}")

