"""Shared timestamp-validation boundaries."""


def validate_timestamp(value: str) -> str:
    """Return a timestamp after shared RFC 3339 validation.

    The final implementation will require an explicit UTC offset, reject naive
    or numeric model input, and preserve the supplied string rather than forcing
    textual UTC normalization.

    Args:
        value: Timestamp string supplied at the model boundary.

    Returns:
        The original timestamp string.
    """
    return value


def validate_time_range(start: str, end: str) -> tuple[str, str]:
    """Return a timestamp pair after shared range validation.

    The final implementation will validate both RFC 3339 strings and require
    the end instant to be strictly after the start instant. Team 2 does not
    deliberately truncate fractional seconds in application code.

    Args:
        start: Inclusive event start instant with an explicit UTC offset.
        end: Exclusive event end instant with an explicit UTC offset.

    Returns:
        The original start and end strings.
    """
    return validate_timestamp(start), validate_timestamp(end)
