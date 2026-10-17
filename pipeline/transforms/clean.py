"""Shared text-cleaning utilities for PDF/DOCX source→clean transforms."""

from __future__ import annotations

import re


def strip_contents_section(body: str) -> tuple[str, bool]:
    """Remove a ``## **Contents**`` section and its TOC table from a PDF markdown body.

    pymupdf4llm emits a ``## **Contents**`` heading followed by a dot-leader TOC
    table for any PDF that has a TOC page. The rendered document provides its
    own navigation, so the duplicated table is dropped during the source→clean
    transform.

    Returns ``(stripped_body, removed_flag)``. The flag is ``True`` when a
    Contents section was actually removed; callers can use it to emit a comment
    explaining the removal.

    Idempotent: re-running on already-stripped text returns ``(body, False)``
    because the ``## **Contents**`` heading no longer matches.
    """
    # ponytail: one pattern, one replacement. The lookahead anchors at the next
    # `\n## ` (the first real content section) or end-of-string so we don't
    # swallow unrelated content.
    pattern = r"## \*\*Contents\*\*\s*\n(?:.*\n)*?(?=\n## |\Z)"
    match = re.search(pattern, body)
    if not match:
        return body, False
    return body[: match.start()] + body[match.end() :], True


def normalise_blank_runs(body: str) -> str:
    """Collapse 3+ consecutive blank lines into 2."""
    return _normalise_blank_lines(body)


def strip_duplicate_h1(body: str, title: str) -> str:
    """Remove duplicate ``# Title`` H1 headings (the clean item already adds one)."""
    escaped = re.escape(title.strip())
    pattern = rf"^(?:#\s+{escaped}\s*\n)+"
    body = re.sub(pattern, "", body, count=1)
    return body.lstrip("\n")


def _normalise_blank_lines(text: str) -> str:
    """Collapse 3+ consecutive blank lines into at most 2 (one paragraph gap)."""
    return re.sub(r"\n{3,}", "\n\n", text)
