"""Check structural typing and the public consumer API without a provider."""

from typing import assert_type

from calendar_contract import (
    CalendarService,
    CreateEvent,
    Event,
    ReplaceEvent,
)


class IndependentCalendar:
    def __init__(self) -> None:
        self.event = Event(
            id="opaque-provider-id",
            title="Review",
            start="2030-01-07T15:00:00Z",
            end="2030-01-07T15:30:00Z",
        )
        self.calls: list[str] = []

    def create(self, request: CreateEvent) -> Event:
        self.calls.append("create")
        return self.event

    def get(self, event_id: str) -> Event:
        self.calls.append("get")
        return self.event

    def replace(self, event_id: str, request: ReplaceEvent) -> Event:
        self.calls.append("replace")
        return self.event

    def delete(self, event_id: str) -> None:
        self.calls.append("delete")


def test_consumer_accepts_structural_implementation() -> None:
    implementation = IndependentCalendar()
    service: CalendarService = implementation
    fields = {
        "title": "Review",
        "start": "2030-01-07T15:00:00Z",
        "end": "2030-01-07T15:30:00Z",
    }

    created = assert_type(service.create(CreateEvent(**fields)), Event)
    fetched = assert_type(service.get(created.id), Event)
    replaced = assert_type(service.replace(created.id, ReplaceEvent(**fields)), Event)
    assert assert_type(service.delete(created.id), None) is None

    assert created is implementation.event
    assert fetched is implementation.event
    assert replaced is implementation.event
    assert implementation.calls == ["create", "get", "replace", "delete"]
