"""Request shape and shared-validator integration for Create and Replace."""

import json
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from calendar_contract import requests
from calendar_contract.requests import CreateEvent, ReplaceEvent


@pytest.fixture(params=[CreateEvent, ReplaceEvent])
def request_model(request: pytest.FixtureRequest) -> type[CreateEvent | ReplaceEvent]:
    model: type[CreateEvent | ReplaceEvent] = request.param
    return model


@pytest.fixture
def valid_payload() -> dict[str, str]:
    return {
        "title": "  Team meeting  ",
        "start": "2026-11-03T09:00:00-05:00",
        "end": "2026-11-03T10:00:00-05:00",
    }


def test_valid_request_preserves_all_fields(
    request_model: type[CreateEvent | ReplaceEvent], valid_payload: dict[str, str]
) -> None:
    event = request_model.model_validate(valid_payload)

    assert event.model_dump() == valid_payload
    assert request_model.model_validate_json(json.dumps(valid_payload)) == event


@pytest.mark.parametrize("field", ["title", "start", "end"])
def test_each_field_is_required(
    request_model: type[CreateEvent | ReplaceEvent],
    valid_payload: dict[str, str],
    field: str,
) -> None:
    del valid_payload[field]

    with pytest.raises(ValidationError) as caught:
        request_model.model_validate(valid_payload)

    assert [(e["loc"], e["type"]) for e in caught.value.errors()] == [
        ((field,), "missing")
    ]


@pytest.mark.parametrize("field", ["title", "start", "end"])
@pytest.mark.parametrize("value", [None, 42, 1.5, True, [], {}])
def test_non_string_fields_are_rejected(
    request_model: type[CreateEvent | ReplaceEvent],
    valid_payload: dict[str, str],
    field: str,
    value: object,
) -> None:
    payload: dict[str, object] = {**valid_payload, field: value}

    with pytest.raises(ValidationError) as caught:
        request_model.model_validate(payload)

    assert [(e["loc"], e["type"]) for e in caught.value.errors()] == [
        ((field,), "string_type")
    ]


@pytest.mark.parametrize("field", ["title", "start", "end"])
@pytest.mark.parametrize("binary_type", [bytes, bytearray])
def test_encoded_strings_are_not_silently_decoded(
    request_model: type[CreateEvent | ReplaceEvent],
    valid_payload: dict[str, str],
    field: str,
    binary_type: type[bytes] | type[bytearray],
) -> None:
    payload: dict[str, object] = {
        **valid_payload,
        field: binary_type(valid_payload[field].encode()),
    }

    with pytest.raises(ValidationError) as caught:
        request_model.model_validate(payload)

    assert [(e["loc"], e["type"]) for e in caught.value.errors()] == [
        ((field,), "string_type")
    ]


@pytest.mark.parametrize("field", ["id", "description"])
def test_extra_fields_are_rejected(
    request_model: type[CreateEvent | ReplaceEvent],
    valid_payload: dict[str, str],
    field: str,
) -> None:
    payload = {**valid_payload, field: "caller-supplied value"}

    with pytest.raises(ValidationError) as caught:
        request_model.model_validate_json(json.dumps(payload))

    assert [(e["loc"], e["type"]) for e in caught.value.errors()] == [
        ((field,), "extra_forbidden")
    ]


def test_shared_validators_receive_inputs_and_their_results_are_preserved(
    request_model: type[CreateEvent | ReplaceEvent],
    valid_payload: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Sentinel results isolate delegation from the other issues' parsing rules.
    title_validator = Mock(return_value="validated title")
    time_validator = Mock(return_value=("validated start", "validated end"))
    monkeypatch.setattr(requests, "validate_write_title", title_validator)
    monkeypatch.setattr(requests, "validate_time_range", time_validator)

    event = request_model.model_validate(valid_payload)

    title_validator.assert_called_once_with(valid_payload["title"])
    time_validator.assert_called_once_with(valid_payload["start"], valid_payload["end"])
    assert event.model_dump() == {
        "title": "validated title",
        "start": "validated start",
        "end": "validated end",
    }


@pytest.mark.parametrize("validator", ["validate_write_title", "validate_time_range"])
def test_shared_validation_failures_reject_the_request(
    request_model: type[CreateEvent | ReplaceEvent],
    valid_payload: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    validator: str,
) -> None:
    failing_validator = Mock(side_effect=ValueError("Shared validation rejected input"))
    monkeypatch.setattr(requests, validator, failing_validator)

    with pytest.raises(ValidationError, match="Shared validation rejected input"):
        request_model.model_validate(valid_payload)

    failing_validator.assert_called_once()
