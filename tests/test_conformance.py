"""Runs the shared conformance suite against an in-memory reference service."""

import secrets

import pytest

from calendar_contract.conformance import CalendarServiceConformance
from calendar_contract.errors import CalendarError, ErrorCode
from calendar_contract.event import Event
from calendar_contract.requests import CreateEvent, ReplaceEvent
from calendar_contract.service import CalendarService


class InMemoryCalendarService:
    """Keeps events in a dict; exists only to exercise the conformance suite."""

    def __init__(self) -> None:
        self.events: dict[str, Event] = {}

    def create(self, request: CreateEvent) -> Event:
        event = Event(id=secrets.token_hex(8), **request.model_dump())
        self.events[event.id] = event
        return event

    def get(self, event_id: str) -> Event:
        return self._existing(event_id)

    def replace(self, event_id: str, request: ReplaceEvent) -> Event:
        self._existing(event_id)
        event = Event(id=event_id, **request.model_dump())
        self.events[event_id] = event
        return event

    def delete(self, event_id: str) -> None:
        self._existing(event_id)
        del self.events[event_id]

    def _existing(self, event_id: str) -> Event:
        if event_id not in self.events:
            raise CalendarError(ErrorCode.NOT_FOUND, "Event not found.", False)
        return self.events[event_id]


class TestInMemoryCalendarService(CalendarServiceConformance):
    @pytest.fixture
    def service(self) -> CalendarService:
        return InMemoryCalendarService()


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
