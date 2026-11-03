"""Public names reserved for shared Calendar failures."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Stable provider-independent error codes for the shared contract."""

    INVALID_INPUT = "invalid_input"
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    PROVIDER_ERROR = "provider_error"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
