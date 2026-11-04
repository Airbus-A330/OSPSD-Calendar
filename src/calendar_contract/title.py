"""Shared write-title validation boundary."""


def validate_write_title(value: str) -> str:
    """Reject blank write titles while preserving the submitted string.

    Args:
        value: Title supplied by a create or replace request.

    Returns:
        The original title string, including leading and trailing whitespace.

    Raises:
        ValueError: If the title is empty or contains only whitespace.
    """
    if not value.strip():
        raise ValueError("Title must not be blank")
    return value
