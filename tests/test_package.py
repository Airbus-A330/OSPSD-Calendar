"""Smoke tests for the initial package scaffold."""

import calendar_contract


def test_package_is_importable_with_initial_version() -> None:
    """Confirm the installed package exposes its scaffold version."""
    assert calendar_contract.__version__ == "0.1.0"
