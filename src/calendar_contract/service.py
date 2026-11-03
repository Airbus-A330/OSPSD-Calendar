"""Proposed provider-independent interface for the four shared operations."""

from typing import Protocol

from calendar_contract.event import Event
from calendar_contract.requests import CreateEvent, ReplaceEvent


class CalendarService(Protocol):
    """Creates, reads, replaces, and deletes events in one calendar.

    Failures raise `CalendarError` with the matching `ErrorCode`.
    """

    def create(self, request: CreateEvent) -> Event:
        """Create an event from `request` and return it with its new `id`."""
        ...

    def get(self, event_id: str) -> Event:
        """Return the event with `event_id`."""
        ...

    def replace(self, event_id: str, request: ReplaceEvent) -> Event:
        """Replace the shared fields of `event_id` with `request` and return it."""
        ...

    def delete(self, event_id: str) -> None:
        """Delete the event with `event_id`."""
        ...
