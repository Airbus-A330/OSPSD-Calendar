"""Provider-independent errors for shared Calendar operations."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Stable provider-independent error codes for the shared contract."""

    INVALID_INPUT = "invalid_input"
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    PROVIDER_ERROR = "provider_error"
    PROVIDER_UNAVAILABLE = "provider_unavailable"


class CalendarError(Exception):
    """A shared Calendar failure without provider or HTTP dependencies.

    Details must remain provider-independent. Callers are responsible for
    ensuring details are sanitized before exposing them externally.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        retryable: bool,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code: ErrorCode = code
        self.message: str = message
        self.retryable: bool = retryable
        self.details: dict[str, object] | None = details
