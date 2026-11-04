"""Reusable conformance tests for implementations of `CalendarService`.

Subclass `CalendarServiceConformance` in a test module and override two
fixtures: `service` returns the implementation under test, and
`failing_service` returns a factory that builds the implementation on a
controlled provider failing every call with the given `ProviderFailure`:

```python
class TestMyCalendar(CalendarServiceConformance):
    @pytest.fixture
    def service(self) -> CalendarService:
        return MyCalendarService(FakeProvider())

    @pytest.fixture
    def failing_service(self) -> FailingServiceFactory:
        return lambda failure: MyCalendarService(FailingProvider(failure))
```

Every event a test creates is deleted afterward. The failure hooks live only in
the test fixtures; the production `CalendarService` protocol is unchanged.
"""

from collections.abc import Callable, Iterator
from datetime import datetime
from enum import StrEnum

import pytest
from pydantic import ValidationError

from calendar_contract.errors import CalendarError, ErrorCode
from calendar_contract.event import Event
from calendar_contract.requests import CreateEvent, ReplaceEvent
from calendar_contract.service import CalendarService


class ProviderFailure(StrEnum):
    """Provider failures an implementation must translate into `CalendarError`."""

    ACCESS_DENIED = "access_denied"
    UNEXPECTED_RESPONSE = "unexpected_response"
    UNAVAILABLE = "unavailable"
    UNCERTAIN_WRITE = "uncertain_write"


FailingServiceFactory = Callable[[ProviderFailure], CalendarService]

OPERATIONS = ("create", "get", "replace", "delete")
WRITE_OPERATIONS = ("create", "replace")
FAILING_EVENT_ID = "conformance-event"

CREATE = {
    "title": "Conformance event",
    "start": "2030-01-07T15:00:00Z",
    "end": "2030-01-07T15:30:00Z",
}
REPLACE = {
    "title": "Conformance event (replaced)",
    "start": "2030-01-07T16:00:00+01:00",
    "end": "2030-01-07T17:00:00+01:00",
}


def same_instant(actual: str, expected: str) -> bool:
    """Return whether timestamps `actual` and `expected` name the same instant."""
    return datetime.fromisoformat(actual) == datetime.fromisoformat(expected)


def assert_event_matches(event: Event, fields: dict[str, str]) -> None:
    """Assert that `event` has a non-empty `id` and the shared `fields`."""
    assert event.id
    assert event.title == fields["title"]
    assert same_instant(event.start, fields["start"])
    assert same_instant(event.end, fields["end"])


def assert_not_found(error: pytest.ExceptionInfo[CalendarError]) -> None:
    """Assert that the raised `error` is a non-retryable `not_found` failure."""
    assert error.value.code == ErrorCode.NOT_FOUND
    assert error.value.retryable is False


def call_operation(service: CalendarService, operation: str) -> None:
    """Call `operation` on `service` with valid shared input."""
    if operation == "create":
        service.create(CreateEvent(**CREATE))
    elif operation == "get":
        service.get(FAILING_EVENT_ID)
    elif operation == "replace":
        service.replace(FAILING_EVENT_ID, ReplaceEvent(**REPLACE))
    else:
        service.delete(FAILING_EVENT_ID)


def raised_error(
    failing_service: FailingServiceFactory, failure: ProviderFailure, operation: str
) -> CalendarError:
    """Return the `CalendarError` that `operation` raises under `failure`."""
    with pytest.raises(CalendarError) as error:
        call_operation(failing_service(failure), operation)
    return error.value


class CalendarServiceConformance:
    """Shared behavior every `CalendarService` implementation must show."""

    @pytest.fixture
    def service(self) -> CalendarService:
        """Return the implementation under test; subclasses must override this."""
        raise NotImplementedError("override the `service` fixture")

    @pytest.fixture
    def failing_service(self) -> FailingServiceFactory:
        """Return a factory for failing implementations; subclasses must override."""
        raise NotImplementedError("override the `failing_service` fixture")

    @pytest.fixture
    def created_ids(self, service: CalendarService) -> Iterator[list[str]]:
        """Collect created event IDs and delete any that still exist afterward."""
        ids: list[str] = []
        yield ids
        for event_id in ids:
            try:
                service.delete(event_id)
            except CalendarError as error:
                if error.code != ErrorCode.NOT_FOUND:
                    raise

    @pytest.fixture
    def created(self, service: CalendarService, created_ids: list[str]) -> Event:
        """Create one event from `CREATE` for the test and return it."""
        event = service.create(CreateEvent(**CREATE))
        created_ids.append(event.id)
        return event

    @pytest.fixture
    def missing_id(self, service: CalendarService) -> str:
        """Return the ID of an event that was created and then deleted."""
        event = service.create(CreateEvent(**CREATE))
        service.delete(event.id)
        return event.id

    def test_create_returns_event_with_shared_fields(self, created: Event) -> None:
        assert_event_matches(created, CREATE)

    def test_create_twice_creates_two_events(
        self, service: CalendarService, created: Event, created_ids: list[str]
    ) -> None:
        second = service.create(CreateEvent(**CREATE))
        created_ids.append(second.id)
        assert second.id != created.id

    def test_get_returns_created_event(
        self, service: CalendarService, created: Event
    ) -> None:
        fetched = service.get(created.id)
        assert fetched.id == created.id
        assert_event_matches(fetched, CREATE)

    def test_get_missing_event_raises_not_found(
        self, service: CalendarService, missing_id: str
    ) -> None:
        with pytest.raises(CalendarError) as error:
            service.get(missing_id)
        assert_not_found(error)

    def test_replace_keeps_id_and_replaces_shared_fields(
        self, service: CalendarService, created: Event
    ) -> None:
        replaced = service.replace(created.id, ReplaceEvent(**REPLACE))
        assert replaced.id == created.id
        assert_event_matches(replaced, REPLACE)
        assert_event_matches(service.get(created.id), REPLACE)

    def test_replace_missing_event_raises_not_found(
        self, service: CalendarService, missing_id: str
    ) -> None:
        with pytest.raises(CalendarError) as error:
            service.replace(missing_id, ReplaceEvent(**REPLACE))
        assert_not_found(error)

    def test_delete_removes_event(
        self, service: CalendarService, created: Event
    ) -> None:
        service.delete(created.id)
        with pytest.raises(CalendarError) as error:
            service.get(created.id)
        assert_not_found(error)

    def test_delete_missing_event_raises_not_found(
        self, service: CalendarService, missing_id: str
    ) -> None:
        with pytest.raises(CalendarError) as error:
            service.delete(missing_id)
        assert_not_found(error)

    def test_create_request_with_unknown_field_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            CreateEvent(**{**CREATE, "location": "Room 101"})

    def test_replace_request_missing_a_shared_field_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            ReplaceEvent.model_validate(
                {"title": REPLACE["title"], "start": REPLACE["start"]}
            )

    @pytest.mark.parametrize("operation", OPERATIONS)
    def test_access_denied_raises_access_denied(
        self, failing_service: FailingServiceFactory, operation: str
    ) -> None:
        error = raised_error(failing_service, ProviderFailure.ACCESS_DENIED, operation)
        assert error.code == ErrorCode.ACCESS_DENIED
        assert isinstance(error.retryable, bool)

    @pytest.mark.parametrize("operation", OPERATIONS)
    def test_unexpected_provider_response_raises_provider_error(
        self, failing_service: FailingServiceFactory, operation: str
    ) -> None:
        error = raised_error(
            failing_service, ProviderFailure.UNEXPECTED_RESPONSE, operation
        )
        assert error.code == ErrorCode.PROVIDER_ERROR
        assert isinstance(error.retryable, bool)

    @pytest.mark.parametrize("operation", OPERATIONS)
    def test_unavailable_provider_raises_provider_unavailable(
        self, failing_service: FailingServiceFactory, operation: str
    ) -> None:
        error = raised_error(failing_service, ProviderFailure.UNAVAILABLE, operation)
        assert error.code == ErrorCode.PROVIDER_UNAVAILABLE
        assert isinstance(error.retryable, bool)

    @pytest.mark.parametrize("operation", WRITE_OPERATIONS)
    def test_uncertain_write_raises_non_retryable_provider_error(
        self, failing_service: FailingServiceFactory, operation: str
    ) -> None:
        error = raised_error(
            failing_service, ProviderFailure.UNCERTAIN_WRITE, operation
        )
        assert error.code == ErrorCode.PROVIDER_ERROR
        assert error.retryable is False
