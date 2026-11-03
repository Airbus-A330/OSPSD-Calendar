"""Shared Calendar event representation."""

from pydantic import BaseModel


class Event(BaseModel):
    """Provider-independent event fields returned by shared operations."""

    id: str
    title: str
    start: str
    end: str
