"""Behavioral tests for shared Event and write models."""

from dataclasses import FrozenInstanceError, asdict
from datetime import UTC, datetime
from typing import cast

import pytest

from calendar_contract import CreateEvent, Event, ReplaceEvent

START = "2026-11-04T10:00:00-05:00"
END = "2026-11-04T15:30:00Z"
WRITE_MODELS = [CreateEvent, ReplaceEvent]


@pytest.mark.parametrize("model", WRITE_MODELS)
def test_write_preserves_title_and_timestamp_strings(
    model: type[CreateEvent],
) -> None:
    request = model(title="  Team sync \t", start=START, end=END)
    assert asdict(request) == {
        "title": "  Team sync \t",
        "start": START,
        "end": END,
    }


@pytest.mark.parametrize("model", WRITE_MODELS)
@pytest.mark.parametrize("field", ["title", "start", "end"])
def test_write_rejects_missing_fields(model: type[CreateEvent], field: str) -> None:
    payload = {"title": "Team sync", "start": START, "end": END}
    del payload[field]
    with pytest.raises(TypeError):
        model(**payload)


@pytest.mark.parametrize("model", WRITE_MODELS)
@pytest.mark.parametrize("field", ["title", "start", "end"])
def test_write_rejects_null_fields(model: type[CreateEvent], field: str) -> None:
    payload = {"title": "Team sync", "start": START, "end": END}
    payload[field] = cast(str, None)
    with pytest.raises(TypeError):
        model(**payload)


@pytest.mark.parametrize("model", WRITE_MODELS)
@pytest.mark.parametrize("title", ["", " ", "\t\r\n", "\u2003\u00a0"])
def test_write_rejects_blank_title(model: type[CreateEvent], title: str) -> None:
    with pytest.raises(ValueError, match="title"):
        model(title=title, start=START, end=END)


@pytest.mark.parametrize("model", WRITE_MODELS)
@pytest.mark.parametrize("title", [1, True, b"Title", [], {}])
def test_write_rejects_non_string_title(
    model: type[CreateEvent], title: object
) -> None:
    with pytest.raises(TypeError, match="title"):
        model(title=cast(str, title), start=START, end=END)


@pytest.mark.parametrize("model", WRITE_MODELS)
@pytest.mark.parametrize("field", ["id", "description", "location", "calendar_id"])
def test_write_rejects_unknown_fields(model: type[CreateEvent], field: str) -> None:
    payload = {"title": "Team sync", "start": START, "end": END, field: "extra"}
    with pytest.raises(TypeError):
        model(**payload)


@pytest.mark.parametrize("model", WRITE_MODELS)
@pytest.mark.parametrize("field", ["start", "end"])
@pytest.mark.parametrize(
    "timestamp",
    [
        "",
        "2026-11-04",
        "2026-11-04T10:00:00",
        "2026-11-04 10:00:00Z",
        "20261104T100000Z",
        "2026-11-04T10:00Z",
        "2026-11-04T10:00:00+0500",
        "2026-11-04T10:00:00+05",
        "2026-11-04T10:00:00+05:60",
        "2026-11-04T10:00:00+24:00",
        "2026-02-30T10:00:00Z",
        "2026-11-04T24:00:00Z",
        "2026-11-04T10:60:00Z",
        "2026-11-04T10:00:60Z",
        "2026-11-04T23:59:60Z",
        "2026-11-04T10:00:00,1Z",
        "2026-11-04T10:00:00Z\n",
        "2026-11-04T10:00:00Zjunk",
    ],
)
def test_write_rejects_malformed_timestamp(
    model: type[CreateEvent], field: str, timestamp: str
) -> None:
    payload = {"title": "Team sync", "start": START, "end": END, field: timestamp}
    with pytest.raises(ValueError):
        model(**payload)


@pytest.mark.parametrize("model", WRITE_MODELS)
@pytest.mark.parametrize("field", ["start", "end"])
@pytest.mark.parametrize(
    "timestamp",
    [1793800000, 1793800000.5, True, datetime(2026, 11, 4, tzinfo=UTC)],
)
def test_write_rejects_non_string_timestamp(
    model: type[CreateEvent], field: str, timestamp: object
) -> None:
    payload = {"title": "Team sync", "start": START, "end": END}
    payload[field] = cast(str, timestamp)
    with pytest.raises(TypeError):
        model(**payload)


@pytest.mark.parametrize("model", WRITE_MODELS)
@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2026-11-04T10:00:00Z", "2026-11-04T10:00:00Z"),
        ("2026-11-04T10:00:01Z", "2026-11-04T10:00:00Z"),
        ("2026-11-04T10:00:00-05:00", "2026-11-04T15:00:00Z"),
        ("2026-11-04T10:00:00-05:00", "2026-11-04T11:00:00Z"),
        ("2026-11-04T10:00:00.10Z", "2026-11-04T10:00:00.1Z"),
        ("2016-12-31T23:59:60Z", "2017-01-01T00:59:60+01:00"),
    ],
)
def test_write_rejects_end_not_after_start(
    model: type[CreateEvent], start: str, end: str
) -> None:
    with pytest.raises(ValueError, match="end must be strictly after start"):
        model(title="Meeting", start=start, end=end)


@pytest.mark.parametrize("model", WRITE_MODELS)
@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2026-11-04T10:00:00+05:30", "2026-11-04T05:00:00Z"),
        ("2026-11-04T10:00:00Z", "2026-11-04T05:30:00-05:00"),
        ("2026-11-04T23:59:59Z", "2026-11-05T00:00:00+00:00"),
        ("2026-11-04t10:00:00z", "2026-11-04t10:00:01z"),
        ("2026-11-04T10:00:00.1234567Z", "2026-11-04T10:00:00.1234568Z"),
        ("2026-11-04T10:00:00.09Z", "2026-11-04T10:00:00.1Z"),
        ("2016-12-31T23:59:59.999Z", "2016-12-31T23:59:60Z"),
        ("2016-12-31T23:59:60Z", "2017-01-01T00:00:00Z"),
        ("2017-01-01T00:59:60+01:00", "2017-01-01T01:00:00+01:00"),
        ("0001-01-01T00:00:00+01:00", "0001-01-01T00:00:01+01:00"),
        ("9999-12-31T23:59:58-01:00", "9999-12-31T23:59:59-01:00"),
    ],
)
def test_write_accepts_increasing_instants(
    model: type[CreateEvent], start: str, end: str
) -> None:
    assert asdict(model(title="Meeting", start=start, end=end)) == {
        "title": "Meeting",
        "start": start,
        "end": end,
    }


@pytest.mark.parametrize(
    "event_id", ["external:Event / ? \u2603", "", "GOOGLE-NOT-REQUIRED"]
)
def test_event_preserves_opaque_id_and_all_shared_fields(event_id: str) -> None:
    assert asdict(Event(id=event_id, title="Meeting", start=START, end=END)) == {
        "id": event_id,
        "title": "Meeting",
        "start": START,
        "end": END,
    }


def test_event_allows_empty_provider_title() -> None:
    assert Event(id="opaque-id", title="", start=START, end=END).title == ""


@pytest.mark.parametrize("field", ["id", "title"])
def test_event_rejects_non_string_fields(field: str) -> None:
    payload = {"id": "opaque-id", "title": "", "start": START, "end": END}
    payload[field] = cast(str, 123)
    with pytest.raises(TypeError):
        Event(**payload)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2026-11-04T10:00:00", END),
        (START, START),
        (END, START),
    ],
)
def test_event_validates_time_invariants(start: str, end: str) -> None:
    with pytest.raises(ValueError):
        Event(id="opaque-id", title="", start=start, end=end)


def test_write_cannot_be_mutated_to_bypass_validation() -> None:
    request = CreateEvent(title="Meeting", start=START, end=END)
    with pytest.raises(FrozenInstanceError):
        request.title = ""  # type: ignore[misc]
