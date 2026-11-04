"""Tests for provider-independent error data."""

import json
from dataclasses import asdict
from typing import cast

import pytest

from calendar_contract import CalendarError, ErrorCode


def test_shared_error_codes_have_contract_values() -> None:
    assert {code.value for code in ErrorCode} == {
        "invalid_input",
        "not_found",
        "access_denied",
        "provider_error",
        "provider_unavailable",
    }


@pytest.mark.parametrize("code", list(ErrorCode))
def test_error_carries_required_data_without_details(code: ErrorCode) -> None:
    error = CalendarError(code=code, message="Operation failed.", retryable=False)
    assert asdict(error) == {
        "code": code.value,
        "message": "Operation failed.",
        "retryable": False,
        "details": None,
    }
    assert json.loads(json.dumps(asdict(error)))["code"] == code.value


def test_error_carries_sanitized_details() -> None:
    error = CalendarError(
        code=ErrorCode.INVALID_INPUT,
        message="Invalid event.",
        retryable=False,
        details={"field": "title", "reason": "blank"},
    )
    assert asdict(error) == {
        "code": "invalid_input",
        "message": "Invalid event.",
        "retryable": False,
        "details": {"field": "title", "reason": "blank"},
    }


@pytest.mark.parametrize("retryable", [False, True])
def test_retryability_is_explicit_not_inferred_from_code(retryable: bool) -> None:
    error = CalendarError(
        code=ErrorCode.PROVIDER_ERROR,
        message="Provider operation failed.",
        retryable=retryable,
    )
    assert error.retryable is retryable


def test_error_rejects_unknown_code() -> None:
    with pytest.raises(ValueError):
        ErrorCode("unknown")


def test_error_rejects_untyped_code() -> None:
    with pytest.raises(TypeError, match="code"):
        CalendarError(
            code=cast(ErrorCode, "not_found"), message="Not found.", retryable=False
        )


def test_error_rejects_non_boolean_retryable() -> None:
    with pytest.raises(TypeError, match="retryable"):
        CalendarError(
            code=ErrorCode.PROVIDER_ERROR,
            message="Failed.",
            retryable=cast(bool, "false"),
        )


def test_error_rejects_non_string_message() -> None:
    with pytest.raises(TypeError, match="message"):
        CalendarError(
            code=ErrorCode.PROVIDER_ERROR, message=cast(str, None), retryable=False
        )


def test_error_rejects_non_dictionary_details() -> None:
    with pytest.raises(TypeError, match="details"):
        CalendarError(
            code=ErrorCode.INVALID_INPUT,
            message="Invalid event.",
            retryable=False,
            details=cast(dict[str, object], "raw response"),
        )
