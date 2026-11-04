"""Tests for the provider-independent Calendar error contract."""

import pytest

from calendar_contract.errors import CalendarError, ErrorCode


def test_error_codes_remain_unchanged() -> None:
    assert {code.name: code.value for code in ErrorCode} == {
        "INVALID_INPUT": "invalid_input",
        "NOT_FOUND": "not_found",
        "ACCESS_DENIED": "access_denied",
        "PROVIDER_ERROR": "provider_error",
        "PROVIDER_UNAVAILABLE": "provider_unavailable",
    }


@pytest.mark.parametrize("code", list(ErrorCode))
@pytest.mark.parametrize("retryable", [False, True])
def test_construction_without_details(code: ErrorCode, retryable: bool) -> None:
    error = CalendarError(
        code=code, message="Calendar operation failed", retryable=retryable
    )

    assert isinstance(error, Exception)
    assert error.code is code
    assert error.message == "Calendar operation failed"
    assert error.retryable is retryable
    assert error.details is None
    assert str(error) == "Calendar operation failed"
    assert error.args == ("Calendar operation failed",)


@pytest.mark.parametrize("details", [None, {}, {"field": "start", "attempt": 2}])
def test_construction_with_explicit_details(details: dict[str, object] | None) -> None:
    error = CalendarError(
        code=ErrorCode.INVALID_INPUT,
        message="Invalid event start",
        retryable=False,
        details=details,
    )

    assert error.details == details
    assert str(error) == "Invalid event start"


def test_retryable_is_required() -> None:
    with pytest.raises(TypeError, match="retryable"):
        CalendarError(code=ErrorCode.NOT_FOUND, message="Event not found")  # type: ignore[call-arg]


def test_error_can_be_raised_and_caught_as_an_exception() -> None:
    error = CalendarError(
        code=ErrorCode.NOT_FOUND,
        message="Event not found",
        retryable=False,
    )

    with pytest.raises(Exception, match="^Event not found$") as caught:
        raise error

    assert caught.value is error


@pytest.mark.parametrize("message", ["", "Événement introuvable"])
def test_message_is_preserved(message: str) -> None:
    error = CalendarError(code=ErrorCode.NOT_FOUND, message=message, retryable=False)

    assert error.message == message
    assert str(error) == message
