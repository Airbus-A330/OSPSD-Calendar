"""Shared RFC 3339 timestamp and event time-range validation."""

import re
from calendar import monthrange
from datetime import date

_TIMESTAMP = re.compile(
    r"(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})[Tt]"
    r"(?P<hour>[01][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):"
    r"(?P<second>[0-5][0-9]|60)(?:\.(?P<fraction>[0-9]+))?"
    r"(?P<offset>[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)


def _instant_key(value: str) -> tuple[int, bool, str]:
    """Validate syntax and return an exact, offset-independent ordering key."""
    if not isinstance(value, str):
        raise ValueError("Timestamp must be a string")
    match = _TIMESTAMP.fullmatch(value)
    if match is None:
        raise ValueError("Timestamp must be RFC 3339 with an explicit UTC offset")

    calendar_date = date.fromisoformat(match["date"])
    second = int(match["second"])
    seconds = (
        calendar_date.toordinal() * 86400
        + int(match["hour"]) * 3600
        + int(match["minute"]) * 60
        + min(second, 59)
    )
    offset = match["offset"]
    if offset not in ("Z", "z"):
        offset_seconds = int(offset[1:3]) * 3600 + int(offset[4:6]) * 60
        seconds -= offset_seconds if offset[0] == "+" else -offset_seconds

    # Leap seconds follow :59 and precede the next minute, at a UTC month end.
    # Validate their position without predicting leap-second announcements.
    leap_second = second == 60
    if leap_second:
        utc_day, utc_second = divmod(seconds, 86400)
        utc_date = date.fromordinal(utc_day)
        if (
            utc_second != 86399
            or utc_date.day != monthrange(utc_date.year, utc_date.month)[1]
        ):
            raise ValueError("Timestamp has an invalid leap-second position")

    # Fraction strings sort numerically once trailing zeroes are removed.
    # Keeping them separate avoids datetime's microsecond precision limit.
    return seconds, leap_second, (match["fraction"] or "").rstrip("0")


def validate_timestamp(value: str) -> str:
    """Validate an RFC 3339 timestamp without rewriting its text.

    Args:
        value: Timestamp string with an explicit UTC offset.

    Returns:
        The original valid string, including its offset and fractional seconds.

    Raises:
        ValueError: If the value is not a string or is not a valid timestamp.
    """
    _instant_key(value)
    return value


def validate_time_range(start: str, end: str) -> tuple[str, str]:
    """Validate timestamps and require the end instant to follow the start.

    Comparison accounts for offsets and preserves fractional precision. Neither
    input string is normalized or truncated.

    Args:
        start: Inclusive event start instant with an explicit UTC offset.
        end: Exclusive event end instant with an explicit UTC offset.

    Returns:
        The original start and end strings.

    Raises:
        ValueError: If either timestamp is invalid or end is not after start.
    """
    start_instant = _instant_key(start)
    end_instant = _instant_key(end)
    if end_instant <= start_instant:
        raise ValueError("Event end must be strictly after start")
    return start, end
