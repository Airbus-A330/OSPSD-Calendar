"""Shared write-title validation boundary."""


def validate_write_title(value: str) -> str:
    """Return a write title after shared validation.

    The final implementation will reject titles that are empty after trimming
    leading and trailing whitespace. It will return the original string rather
    than requiring callers to store a trimmed replacement.

    Args:
        value: Title supplied by a create or replace request.

    Returns:
        The original title string.
    """
    return value
