"""Shared error data, independent of HTTP and provider exception classes."""

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    """Error codes defined by the common Calendar contract."""

    INVALID_INPUT = "invalid_input"
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    PROVIDER_ERROR = "provider_error"
    PROVIDER_UNAVAILABLE = "provider_unavailable"


@dataclass(frozen=True)
class CalendarError:
    """Transport-independent error data.

    Callers must sanitize message and details before constructing this value:
    never include credentials, raw provider responses, or provider exceptions.
    Details have no shared schema. Retryability is explicit because it depends
    on the operation and outcome, not just the error code; an unknown write
    outcome must use PROVIDER_ERROR with retryable=False.
    """

    code: ErrorCode
    message: str
    retryable: bool
    details: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, ErrorCode):
            raise TypeError("code must be an ErrorCode")
        if not isinstance(self.message, str):
            raise TypeError("message must be a string")
        if not isinstance(self.retryable, bool):
            raise TypeError("retryable must be a boolean")
        if self.details is not None and not isinstance(self.details, dict):
            raise TypeError("details must be a dictionary or None")
