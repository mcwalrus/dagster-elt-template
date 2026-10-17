"""Tests for the shared glyph-stripping helpers."""

from __future__ import annotations

from pipeline.text_clean import strip_glyphs


def test_strip_zero_width_chars():
    """Zero-width space and similar chars are removed."""
    text = "Of\u200bfice\u200crs of the Party."
    assert strip_glyphs(text) == "Officers of the Party."


def test_strip_replacement_char():
    """U+FFFD replacement char is removed."""
    text = "Of\ufffdcers"  # Of + U+FFFD + cers
    assert strip_glyphs(text) == "Ofcers"


def test_strip_soft_hyphen():
    """Soft hyphen is removed."""
    text = "oc­ficer"
    assert strip_glyphs(text) == "ocficer"


def test_strip_pua_between_letters():
    """PUA chars sandwiched between letters are dropped (font-glyph fallback)."""
    text = "Offi\ue000cers"
    assert strip_glyphs(text) == "Officers"


def test_keeps_pua_at_word_boundaries():
    """PUA chars NOT between two letters are kept untouched."""
    text = "\ue000boundary"
    assert strip_glyphs(text) == "\ue000boundary"


def test_idempotent():
    """Re-running strip_glyphs on already-clean text is a no-op."""
    text = "Clean ASCII text only."
    assert strip_glyphs(strip_glyphs(text)) == text
