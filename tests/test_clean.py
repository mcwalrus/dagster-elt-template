"""Tests for the shared text-cleaning utilities used by the clean layer."""

from __future__ import annotations

import pytest

from pipeline.transforms.clean import (
    normalise_blank_runs,
    strip_contents_section,
    strip_duplicate_h1,
)


def test_strip_contents_section_removes_toc_table():
    """A TOC block at the top of a PDF body is dropped."""
    body = (
        "Some preamble.\n\n"
        "## **Contents**\n"
        "Introduction .................. 1\n"
        "Method .................. 2\n"
        "\n## **Introduction**\n"
        "Body content here.\n"
    )
    out, removed = strip_contents_section(body)
    assert removed is True
    assert "## **Contents**" not in out
    assert "Introduction .................. 1" not in out
    assert "## **Introduction**" in out
    assert "Body content here." in out


def test_strip_contents_section_is_idempotent():
    """Re-running on already-stripped text returns the input unchanged."""
    body = "Some preamble.\n\n## **Introduction**\nBody content here.\n"
    out, removed = strip_contents_section(body)
    assert removed is False
    assert out == body


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("a\n\n\n\nb", "a\n\nb"),
        ("a\n\n\nb\n\n\n\n\nc", "a\n\nb\n\nc"),
        ("a\n\nb", "a\n\nb"),  # already normalised
    ],
)
def test_normalise_blank_runs(input_text: str, expected: str):
    """3+ consecutive blank lines collapse to a single paragraph gap."""
    assert normalise_blank_runs(input_text) == expected


def test_strip_duplicate_h1_removes_matching_h1():
    """An H1 line matching the title is removed from the body."""
    body = "# The Charter\n\nBody content.\n"
    out = strip_duplicate_h1(body, title="The Charter")
    assert out.lstrip().startswith("Body content.")


def test_strip_duplicate_h1_keeps_non_matching_h1():
    """A non-matching H1 is left alone."""
    body = "# Other Title\n\nBody content.\n"
    out = strip_duplicate_h1(body, title="The Charter")
    assert "# Other Title" in out
