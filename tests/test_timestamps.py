"""Timestamp syntax, instant ordering, and model-boundary regression tests."""

from typing import cast

import pytest
from pydantic import ValidationError

from calendar_contract.event import Event
from calendar_contract.requests import CreateEvent, ReplaceEvent
from calendar_contract.timestamps import validate_time_range, validate_timestamp


@pytest.mark.parametrize(
    "value",
    [
        "2026-11-02T14:30:00Z",
        "2026-11-02T14:30:00+00:00",
        "2026-11-02T09:30:00-05:00",
        "2026-11-02T20:00:00+05:30",
        "2026-11-02T14:30:00.123Z",
        "2026-11-02T14:30:00.123456789Z",
        "2026-11-02t14:30:00z",
        "2024-02-29T14:30:00Z",
        "2016-12-31T23:59:60Z",
        "2017-01-01T00:59:60+01:00",
    ],
)
def test_valid_timestamp_is_returned_unchanged(value: str) -> None:
    assert validate_timestamp(value) is value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "2026-11-02",
        "2026-11-02T14:30:00",
        "2026-11-02T14:30:00.123",
        "2026-11-02 14:30:00Z",
        "20261102T143000Z",
        "2026-11-02T14:30Z",
        "2026-11-02T14:30:00+0000",
        "2026-11-02T14:30:00+00",
        "2026-11-02T14:30:00+24:00",
        "2026-11-02T14:30:00+05:60",
        "2026-02-29T14:30:00Z",
        "2026-13-02T14:30:00Z",
        "2026-11-31T14:30:00Z",
        "2026-11-02T24:00:00Z",
        "2026-11-02T14:60:00Z",
        "2026-11-02T14:30:61Z",
        "2026-11-02T14:30:60Z",
        "2026-11-02T23:59:60Z",
        "2026-11-02T14:30:00.Z",
        "2026-11-02T14:30:00,123Z",
        " 2026-11-02T14:30:00Z",
        "2026-11-02T14:30:00Z\n",
        "2026-11-02T14:30:00Zjunk",
    ],
)
def test_invalid_timestamp_is_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        validate_timestamp(value)


@pytest.mark.parametrize(
    "value", [None, 1793629800, 1793629800.5, True, b"text", [], {}]
)
def test_non_string_misuse_fails_cleanly(value: object) -> None:
    with pytest.raises(ValueError, match="string"):
        validate_timestamp(cast(str, value))


@pytest.mark.parametrize("field", ["start", "end"])
@pytest.mark.parametrize("invalid", ["2026-11-02T14:30:00", "bad", None, 123])
def test_range_validates_both_inputs(field: str, invalid: object) -> None:
    values = {
        "start": "2026-11-02T14:30:00Z",
        "end": "2026-11-02T15:30:00Z",
    }
    values[field] = cast(str, invalid)
    with pytest.raises(ValueError):
        validate_time_range(**values)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2026-11-02T14:30:00Z", "2026-11-02T15:30:00Z"),
        ("2026-11-02T10:00:00-05:00", "2026-11-02T16:00:00Z"),
        ("2026-11-02T16:00:00+02:00", "2026-11-02T15:00:00Z"),
        ("2026-11-02T23:30:00-05:00", "2026-11-03T05:00:00Z"),
        ("2026-11-02T14:30:00.1Z", "2026-11-02T14:30:00.9Z"),
        ("2026-11-02T14:30:00.123456789Z", "2026-11-02T14:30:00.123456790Z"),
        ("2026-11-02T14:30:00.09Z", "2026-11-02T14:30:00.1Z"),
        ("2016-12-31T23:59:59.999Z", "2016-12-31T23:59:60Z"),
        ("2016-12-31T23:59:60Z", "2017-01-01T00:00:00Z"),
        ("0001-01-01T00:00:00+01:00", "0001-01-01T00:00:01+01:00"),
        ("9999-12-31T23:59:58-01:00", "9999-12-31T23:59:59-01:00"),
    ],
)
def test_increasing_instants_preserve_original_strings(start: str, end: str) -> None:
    assert validate_time_range(start, end) == (start, end)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2026-11-02T14:30:00Z", "2026-11-02T14:30:00Z"),
        ("2026-11-02T10:00:00-05:00", "2026-11-02T15:00:00Z"),
        ("2026-11-02T14:30:00.10Z", "2026-11-02T14:30:00.1+00:00"),
        ("2026-11-02T14:30:01Z", "2026-11-02T14:30:00Z"),
        ("2026-11-02T10:00:00-05:00", "2026-11-02T14:00:00Z"),
        ("2026-11-02T14:30:00.123456790Z", "2026-11-02T14:30:00.123456789Z"),
        ("2016-12-31T23:59:60Z", "2017-01-01T00:59:60+01:00"),
    ],
)
def test_non_increasing_instants_are_rejected(start: str, end: str) -> None:
    with pytest.raises(ValueError, match="strictly after"):
        validate_time_range(start, end)


@pytest.mark.parametrize("model", [Event, CreateEvent, ReplaceEvent])
@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2026-11-02T14:30:00", "2026-11-02T15:30:00Z"),
        ("2026-11-02T14:30:00Z", "bad"),
        ("2026-11-02T10:00:00-05:00", "2026-11-02T15:00:00Z"),
        ("2026-11-02T10:00:00-05:00", "2026-11-02T14:00:00Z"),
    ],
)
def test_model_surfaces_timestamp_failures_as_validation_errors(
    model: type[Event | CreateEvent | ReplaceEvent], start: str, end: str
) -> None:
    payload = {"title": "Meeting", "start": start, "end": end}
    if model is Event:
        payload["id"] = "opaque-id"
    with pytest.raises(ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize("model", [Event, CreateEvent, ReplaceEvent])
def test_model_preserves_subsecond_precision(
    model: type[Event | CreateEvent | ReplaceEvent],
) -> None:
    payload = {
        "title": "Meeting",
        "start": "2026-11-02T10:00:00.123456789-05:00",
        "end": "2026-11-02T15:00:00.123456790Z",
    }
    if model is Event:
        payload["id"] = "opaque-id"
    assert model.model_validate(payload).model_dump() == payload
