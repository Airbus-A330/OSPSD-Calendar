"""Smoke tests for the initial package scaffold."""

import calendar_contract
from calendar_contract import errors, event, requests, timestamps, title


def test_package_is_importable_with_initial_version() -> None:
    """Confirm the installed package exposes its scaffold version."""
    assert calendar_contract.__version__ == "0.1.0"


def test_team_2_scaffold_modules_are_importable() -> None:
    """Confirm each parallel Team 2 work area has a stable module boundary."""
    assert (
        title.__name__,
        timestamps.__name__,
        errors.__name__,
        event.__name__,
        requests.__name__,
    ) == (
        "calendar_contract.title",
        "calendar_contract.timestamps",
        "calendar_contract.errors",
        "calendar_contract.event",
        "calendar_contract.requests",
    )
