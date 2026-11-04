"""Tests for shared create and replace title validation."""

import pytest

from calendar_contract.title import validate_write_title


@pytest.mark.parametrize("title", ["Meeting", "M", "Team meeting", "Réunion"])
def test_accepts_non_empty_title(title: str) -> None:
    assert validate_write_title(title) == title


def test_rejects_empty_title() -> None:
    with pytest.raises(ValueError):
        validate_write_title("")


@pytest.mark.parametrize("title", [" ", "   ", "\t", "\n", " \t\r\n ", "\u00a0\u2003"])
def test_rejects_whitespace_only_title(title: str) -> None:
    with pytest.raises(ValueError):
        validate_write_title(title)


@pytest.mark.parametrize(
    "title", ["  Meeting", "Meeting  ", "  Meeting  ", "\tMeeting\n", "Team  meeting"]
)
def test_preserves_original_title(title: str) -> None:
    assert validate_write_title(title) == title


def test_accepts_long_title_without_a_length_limit() -> None:
    title = "M" * 100_000

    assert validate_write_title(title) == title
