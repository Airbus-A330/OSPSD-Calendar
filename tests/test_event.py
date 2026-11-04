"""Shared read-model fields and delegation to timestamp validation."""

import json
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from calendar_contract import event as event_module
from calendar_contract.event import Event


@pytest.fixture
def valid_payload() -> dict[str, str]:
    return {
        "id": "opaque-event-123",
        "title": "  Team meeting  ",
        "start": "2026-11-04T09:00:00-05:00",
        "end": "2026-11-04T10:00:00-05:00",
    }


def test_event_has_exactly_four_required_string_fields(
    valid_payload: dict[str, str],
) -> None:
    assert set(Event.model_fields) == {"id", "title", "start", "end"}
    assert all(field.annotation is str for field in Event.model_fields.values())
    event = Event.model_validate(valid_payload)
    assert event.model_dump() == valid_payload
    assert Event.model_validate_json(json.dumps(valid_payload)) == event


@pytest.mark.parametrize("field", ["id", "title", "start", "end"])
def test_each_event_field_is_required(
    valid_payload: dict[str, str], field: str
) -> None:
    del valid_payload[field]
    with pytest.raises(ValidationError) as caught:
        Event.model_validate(valid_payload)
    assert [(error["loc"], error["type"]) for error in caught.value.errors()] == [
        ((field,), "missing")
    ]


@pytest.mark.parametrize("title", ["", " \t "])
def test_read_title_can_be_empty_or_blank(
    valid_payload: dict[str, str], title: str
) -> None:
    assert Event.model_validate({**valid_payload, "title": title}).title == title


@pytest.mark.parametrize("event_id", [" opaque:/?会議 ", "x" * 10000])
def test_provider_assigned_ids_are_preserved_without_syntax_or_length_rules(
    valid_payload: dict[str, str], event_id: str
) -> None:
    assert Event.model_validate({**valid_payload, "id": event_id}).id == event_id


@pytest.mark.parametrize("field", ["id", "title", "start", "end"])
@pytest.mark.parametrize(
    "value", [None, 42, 1.5, True, b"text", bytearray(b"text"), [], {}]
)
def test_non_string_values_are_rejected(
    valid_payload: dict[str, str], field: str, value: object
) -> None:
    payload: dict[str, object] = {**valid_payload, field: value}
    with pytest.raises(ValidationError) as caught:
        Event.model_validate(payload)
    assert [(error["loc"], error["type"]) for error in caught.value.errors()] == [
        ((field,), "string_type")
    ]


def test_extra_response_fields_are_ignored(valid_payload: dict[str, str]) -> None:
    payload = {**valid_payload, "description": "Extension", "location": "Room 1"}
    event = Event.model_validate_json(json.dumps(payload))
    assert event.model_dump() == valid_payload


def test_event_delegates_time_range_validation_and_preserves_its_result(
    valid_payload: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    validator = Mock(return_value=("validated start", "validated end"))
    monkeypatch.setattr(event_module, "validate_time_range", validator)
    event = Event.model_validate(valid_payload)
    validator.assert_called_once_with(valid_payload["start"], valid_payload["end"])
    assert event.model_dump() == {
        **valid_payload,
        "start": "validated start",
        "end": "validated end",
    }


def test_shared_time_range_failure_rejects_the_event(
    valid_payload: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    validator = Mock(side_effect=ValueError("Shared time range rejected input"))
    monkeypatch.setattr(event_module, "validate_time_range", validator)
    with pytest.raises(ValidationError, match="Shared time range rejected input"):
        Event.model_validate(valid_payload)
    validator.assert_called_once_with(valid_payload["start"], valid_payload["end"])
