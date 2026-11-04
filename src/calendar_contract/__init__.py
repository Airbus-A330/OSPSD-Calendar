"""Shared, provider-independent Calendar contract package."""

from importlib.metadata import version

from calendar_contract.errors import CalendarError, ErrorCode
from calendar_contract.models import CreateEvent, Event, ReplaceEvent

__version__ = version("calendar-contract")

__all__ = ["CalendarError", "CreateEvent", "ErrorCode", "Event", "ReplaceEvent"]
