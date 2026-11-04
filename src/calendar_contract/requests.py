"""Shared write-request model boundaries."""

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from calendar_contract.timestamps import validate_time_range
from calendar_contract.title import validate_write_title


class CreateEvent(BaseModel):
    """Values supplied when creating an event with a provider-assigned ID."""

    model_config = ConfigDict(extra="forbid", strict=True)

    title: str
    start: str
    end: str

    @model_validator(mode="after")
    def validate_shared_fields(self) -> Self:
        """Call the stable Team 2 validation boundaries."""
        self.title = validate_write_title(self.title)
        self.start, self.end = validate_time_range(self.start, self.end)
        return self


class ReplaceEvent(BaseModel):
    """Complete writable values used to replace an existing event."""

    model_config = ConfigDict(extra="forbid", strict=True)

    title: str
    start: str
    end: str

    @model_validator(mode="after")
    def validate_shared_fields(self) -> Self:
        """Call the stable Team 2 validation boundaries."""
        self.title = validate_write_title(self.title)
        self.start, self.end = validate_time_range(self.start, self.end)
        return self
