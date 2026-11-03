"""Reusable conformance tests for implementations of `CalendarService`.

Subclass `CalendarServiceConformance` in a test module and override the
`service` fixture to return the implementation under test:

```python
class TestMyCalendar(CalendarServiceConformance):
    @pytest.fixture
    def service(self) -> CalendarService:
        return MyCalendarService()
```

Every event a test creates is deleted afterward. Failures that cannot be
triggered through the four operations alone (access denied, provider errors,
temporary unavailability, uncertain writes) are not covered here yet.
"""

from collections.abc import Iterator
from datetime import datetime

import pytest

from calendar_contract.errors import CalendarError, ErrorCode
from calendar_contract.event import Event
from calendar_contract.requests import CreateEvent, ReplaceEvent
from calendar_contract.service import CalendarService

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


class CalendarServiceConformance:
    """Shared behavior every `CalendarService` implementation must show."""

    @pytest.fixture
    def service(self) -> CalendarService:
        """Return the implementation under test; subclasses must override this."""
        raise NotImplementedError("override the `service` fixture")

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
