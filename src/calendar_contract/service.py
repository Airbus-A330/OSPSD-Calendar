"""Provider-independent interface for the four shared Calendar operations."""

from typing import Protocol

from calendar_contract.event import Event
from calendar_contract.requests import CreateEvent, ReplaceEvent


class CalendarService(Protocol):
    """Synchronous operations on one implementation-configured calendar.

    Operation failures raise CalendarError with a shared ErrorCode.
    Translate provider exceptions before they cross this boundary.
    """

    def create(self, request: CreateEvent) -> Event:
        """Create an event with a provider-assigned ID; creation is not idempotent.

        An uncertain write raises PROVIDER_ERROR with retryable=False.
        Never automatically retry an uncertain write.
        """
        ...

    def get(self, event_id: str) -> Event:
        """Read an opaque ID without changing state; missing events use NOT_FOUND."""
        ...

    def replace(self, event_id: str, request: ReplaceEvent) -> Event:
        """Replace title/start/end, keeping the ID; missing events use NOT_FOUND.

        Extension-field behavior is implementation-specific. An uncertain write
        raises PROVIDER_ERROR with retryable=False and is not retried automatically.
        """
        ...

    def delete(self, event_id: str) -> None:
        """Delete an event; absent or already deleted events use NOT_FOUND."""
        ...
