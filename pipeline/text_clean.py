"""Shared text cleanup helpers used by both PDF extraction and DOCX extraction.

PDF parsers in particular embed font-glyph fallbacks as zero-width /
replacement / Private Use Area characters when a font glyph is unavailable.
Both ingestion (``pdf_convert.clean_body``) and any future validation need
to strip these so downstream consumers see clean text — kept in one place
so they can't drift apart.
"""

from __future__ import annotations

import re

# Zero-width + replacement + soft-hyphen + BOM. Some PDFs embed these
# when 'ffi' / 'ffl' ligatures or accented chars can't be rendered.
_INLINE_GLYPH_RE = re.compile(r"[\u200b-\u200f\ufeff\ufffd\u00ad]")
# Private Use Area chars between letters are font-glyph fallbacks (the
# 'ffi' ligature renders as e.g. 'o<PUA>icers').
_PUA_BETWEEN_LETTERS_RE = re.compile(r"(?<=[A-Za-z])[\ue000-\uf8ff](?=[A-Za-z])")


def strip_glyphs(text: str) -> str:
    """Remove zero-width / replacement / PUA-between-letters characters."""
    return _PUA_BETWEEN_LETTERS_RE.sub("", _INLINE_GLYPH_RE.sub("", text))
