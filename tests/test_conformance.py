"""Runs the shared conformance suite against an in-memory reference service."""

import secrets

import pytest

from calendar_contract.conformance import (
    CalendarServiceConformance,
    FailingServiceFactory,
    ProviderFailure,
)
from calendar_contract.errors import CalendarError, ErrorCode
from calendar_contract.event import Event
from calendar_contract.requests import CreateEvent, ReplaceEvent
from calendar_contract.service import CalendarService

FAILURE_ERRORS = {
    ProviderFailure.ACCESS_DENIED: (ErrorCode.ACCESS_DENIED, False),
    ProviderFailure.UNEXPECTED_RESPONSE: (ErrorCode.PROVIDER_ERROR, False),
    ProviderFailure.UNAVAILABLE: (ErrorCode.PROVIDER_UNAVAILABLE, True),
    ProviderFailure.UNCERTAIN_WRITE: (ErrorCode.PROVIDER_ERROR, False),
}


class InMemoryCalendarService:
    """Keeps events in a dict; exists only to exercise the conformance suite."""

    def __init__(self, failure: ProviderFailure | None = None) -> None:
        self.events: dict[str, Event] = {}
        self.failure = failure

    def create(self, request: CreateEvent) -> Event:
        self._fail_if_configured()
        event = Event(id=secrets.token_hex(8), **request.model_dump())
        self.events[event.id] = event
        return event

    def get(self, event_id: str) -> Event:
        self._fail_if_configured()
        return self._existing(event_id)

    def replace(self, event_id: str, request: ReplaceEvent) -> Event:
        self._fail_if_configured()
        self._existing(event_id)
        event = Event(id=event_id, **request.model_dump())
        self.events[event_id] = event
        return event

    def delete(self, event_id: str) -> None:
        self._fail_if_configured()
        self._existing(event_id)
        del self.events[event_id]

    def _fail_if_configured(self) -> None:
        if self.failure is None:
            return
        code, retryable = FAILURE_ERRORS[self.failure]
        raise CalendarError(code, "Provider failure.", retryable)

    def _existing(self, event_id: str) -> Event:
        if event_id not in self.events:
            raise CalendarError(ErrorCode.NOT_FOUND, "Event not found.", False)
        return self.events[event_id]


class TestInMemoryCalendarService(CalendarServiceConformance):
    @pytest.fixture
    def service(self) -> CalendarService:
        return InMemoryCalendarService()

    @pytest.fixture
    def failing_service(self) -> FailingServiceFactory:
        return InMemoryCalendarService


class ForgetfulReplaceService(InMemoryCalendarService):
    """Returns the replacement but never stores it."""

    def replace(self, event_id: str, request: ReplaceEvent) -> Event:
        self._existing(event_id)
        return Event(id=event_id, **request.model_dump())


def test_suite_catches_replace_that_is_not_stored() -> None:
    service = ForgetfulReplaceService()
    created = service.create(
        CreateEvent(
            title="Conformance event",
            start="2030-01-07T15:00:00Z",
            end="2030-01-07T15:30:00Z",
        )
    )
    suite = CalendarServiceConformance()
    with pytest.raises(AssertionError):
        suite.test_replace_keeps_id_and_replaces_shared_fields(service, created)


def failing_with(code: ErrorCode, retryable: bool) -> FailingServiceFactory:
    """Return a factory whose services raise `code` with `retryable` on every call."""

    class MistranslatingService(InMemoryCalendarService):
        def _fail_if_configured(self) -> None:
            raise CalendarError(code, "Provider failure.", retryable)

    return MistranslatingService


def test_suite_catches_access_denied_reported_as_provider_error() -> None:
    suite = CalendarServiceConformance()
    with pytest.raises(AssertionError):
        suite.test_access_denied_raises_access_denied(
            failing_with(ErrorCode.PROVIDER_ERROR, False), "get"
        )


@pytest.mark.parametrize("operation", ["create", "replace"])
def test_suite_catches_retryable_uncertain_write(operation: str) -> None:
    suite = CalendarServiceConformance()
    with pytest.raises(AssertionError):
        suite.test_uncertain_write_raises_non_retryable_provider_error(
            failing_with(ErrorCode.PROVIDER_ERROR, True), operation
        )
