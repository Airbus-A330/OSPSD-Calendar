"""Shared Calendar event representation."""

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from calendar_contract.timestamps import validate_time_range


class Event(BaseModel):
    """Provider-independent event fields returned by shared operations."""

    model_config = ConfigDict(extra="ignore", strict=True)

    id: str
    title: str
    start: str
    end: str

    @model_validator(mode="after")
    def validate_event_times(self) -> Self:
        """Delegate timestamp and range rules without applying write-title rules."""
        self.start, self.end = validate_time_range(self.start, self.end)
        return self
