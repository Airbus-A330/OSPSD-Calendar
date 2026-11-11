"""Smoke tests for the installed package surface."""

from importlib.resources import files

import calendar_contract


def test_package_declares_only_intentional_root_exports() -> None:
    assert calendar_contract.__all__ == [
        "CalendarError",
        "CalendarService",
        "CreateEvent",
        "ErrorCode",
        "Event",
        "ReplaceEvent",
    ]
    assert not hasattr(calendar_contract, "version")


def test_package_is_importable_with_initial_version() -> None:
    """Confirm the installed package exposes its scaffold version."""
    assert calendar_contract.__version__ == "0.1.0"


def test_typed_package_marker_is_installed() -> None:
    assert files(calendar_contract).joinpath("py.typed").is_file()
