"""Shared, provider-independent Calendar contract package."""

from importlib.metadata import version

from calendar_contract.errors import CalendarError, ErrorCode
from calendar_contract.event import Event
from calendar_contract.requests import CreateEvent, ReplaceEvent
from calendar_contract.service import CalendarService

__all__ = [
    "CalendarError",
    "CalendarService",
    "CreateEvent",
    "ErrorCode",
    "Event",
    "ReplaceEvent",
]

__version__ = version("calendar-contract")
