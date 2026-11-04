"""Provider-independent event data and create/replace validation."""

import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date

_TIMESTAMP = re.compile(
    r"(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})[Tt]"
    r"(?P<hour>[01][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):"
    r"(?P<second>[0-5][0-9]|60)(?:\.(?P<fraction>[0-9]+))?"
    r"(?P<offset>[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)


def _timestamp_key(value: str, field: str) -> tuple[int, bool, str]:
    """Validate a timestamp and return an exact, offset-independent sort key."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a timestamp string")
    match = _TIMESTAMP.fullmatch(value)
    if match is None:
        raise ValueError(f"{field} must be RFC 3339 with an explicit UTC offset")

    # date validates the calendar date; fractions are compared separately
    # because RFC 3339 permits more precision than datetime's microseconds.
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
    leap_second = second == 60
    if leap_second:
        utc_day, utc_second = divmod(seconds, 86400)
        utc_date = date.fromordinal(utc_day)
        if (
            utc_second != 86399
            or utc_date.day != monthrange(utc_date.year, utc_date.month)[1]
        ):
            raise ValueError(f"{field} has an invalid leap-second position")
    # A leap second follows :59 and precedes the next minute. Its placement
    # is checked in UTC; future leap-second announcements are not predicted.
    return seconds, leap_second, (match["fraction"] or "").rstrip("0")


def _validate_times(start: str, end: str) -> None:
    if _timestamp_key(end, "end") <= _timestamp_key(start, "start"):
        raise ValueError("end must be strictly after start")


@dataclass(frozen=True)
class Event:
    """Shared event returned by a provider.

    IDs are opaque strings. Empty titles are allowed for provider events without
    a title. Timestamp strings are preserved, including their offsets.
    """

    id: str
    title: str
    start: str
    end: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("id must be a string")
        if not isinstance(self.title, str):
            raise TypeError("title must be a string")
        _validate_times(self.start, self.end)


@dataclass(frozen=True)
class CreateEvent:
    """Required shared fields for creating an event.

    Construction rejects unknown/missing fields with TypeError, wrong field
    types with TypeError, and invalid values with ValueError. Title whitespace
    is preserved. No provider-assigned ID is accepted.
    """

    title: str
    start: str
    end: str

    def __post_init__(self) -> None:
        if not isinstance(self.title, str):
            raise TypeError("title must be a string")
        if not self.title.strip():
            raise ValueError("title must not be blank")
        _validate_times(self.start, self.end)


@dataclass(frozen=True)
class ReplaceEvent(CreateEvent):
    """Complete replacement of the shared write fields, with create validation.

    The existing event's opaque ID is supplied separately to the operation.
    """
