"""Tests for the local-files source → clean transform.

Parametrised over both PDF and DOCX content types. Each test writes a
small synthetic source markdown file under a temporary directory, runs
:func:`transform_local_files`, and asserts the resulting clean item has
the expected ``{stem}.md`` + ``meta.json`` shape.
"""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003 — used at runtime in test bodies

import pytest

from pipeline.transforms.sources.local_files import (
    _SOURCE_REGISTRY,
    regenerate_clean_index,
    transform_local_files,
)


@pytest.fixture
def isolated_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect SOURCES_DIR / CLEAN_DIR into a temp directory tree.

    Returns ``(source_dir_map, clean_dir)`` so the test can drop files
    into the right source folder and assert against the right clean
    folder without polluting the real project tree.
    """
    from pipeline.paths import CLEAN_DIR as REAL_CLEAN_DIR
    from pipeline.paths import DOCX_SOURCES_DIR as REAL_DOCX
    from pipeline.paths import PDF_SOURCES_DIR as REAL_PDF

    clean_dir = tmp_path / "clean"
    pdf_source = tmp_path / "sources" / "pdf"
    docx_source = tmp_path / "sources" / "docx"
    pdf_source.mkdir(parents=True)
    docx_source.mkdir(parents=True)

    # Patch the module-level path constants the transform reads.
    monkeypatch.setattr("pipeline.transforms.sources.local_files.PDF_SOURCES_DIR", pdf_source)
    monkeypatch.setattr("pipeline.transforms.sources.local_files.DOCX_SOURCES_DIR", docx_source)
    monkeypatch.setattr("pipeline.transforms.sources.local_files.CLEAN_DIR", clean_dir)
    # Also patch the source-dir references in paths.py so the cross-imports
    # the transform makes stay consistent.
    monkeypatch.setattr("pipeline.paths.PDF_SOURCES_DIR", pdf_source)
    monkeypatch.setattr("pipeline.paths.DOCX_SOURCES_DIR", docx_source)
    monkeypatch.setattr("pipeline.paths.CLEAN_DIR", clean_dir)
    # Clean_dir inside the transform reads ``Path("data/clean")`` directly
    # via string concatenation. Override that constant too.
    monkeypatch.setattr(
        "pipeline.transforms.sources.local_files._SOURCE_REGISTRY",
        {
            "pdf-document": (pdf_source, "pdf", "pdf"),
            "docx-document": (docx_source, "docx", "docx"),
        },
    )
    # Keep references alive so they aren't garbage collected mid-test.
    _ = (REAL_CLEAN_DIR, REAL_PDF, REAL_DOCX)
    return {
        "pdf_source": pdf_source,
        "docx_source": docx_source,
        "clean_dir": clean_dir,
    }


def _write_source_md(source_dir: Path, stem: str, body: str) -> Path:
    """Write a synthetic ingestor output to *source_dir*."""
    md_path = source_dir / f"{stem}.md"
    md_path.write_text(body, encoding="utf-8")
    return md_path


def _source_body(stem: str) -> str:
    """Realistic ingestor output: a ## Source marker + a heading + body."""
    return (
        f"## Source\n\n"
        f"`{stem}.pdf`\n\n"
        f"# {stem.replace('-', ' ').title()}\n\n"
        f"This is the body of {stem}.\n"
    )


def test_transform_writes_clean_item_for_pdf(isolated_dirs: dict[str, Path]) -> None:
    """A PDF source markdown produces a clean item with frontmatter + meta.json."""
    _write_source_md(isolated_dirs["pdf_source"], "report-2026", _source_body("report-2026"))

    entries = transform_local_files(content_type="pdf-document")

    assert len(entries) == 1
    item_dir = isolated_dirs["clean_dir"] / "pdf-document" / "report-2026"
    assert item_dir.exists()
    assert (item_dir / "report-2026.md").exists()
    assert (item_dir / "meta.json").exists()

    meta = json.loads((item_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["stem"] == "report-2026"
    assert meta["content_type"] == "pdf-document"
    assert meta["source_id"] == "pdf"
    assert meta["source_file"] == "report-2026.pdf"
    assert meta["source_path"] == "data/sources/pdf/report-2026.pdf"
    assert meta["title"] == "Report 2026"
    assert "ingested_at" in meta
    assert "cleaned_at" in meta

    md = (item_dir / "report-2026.md").read_text(encoding="utf-8")
    assert md.startswith("---\n")
    assert 'content_type: "pdf-document"' in md
    assert "## Source" not in md  # source marker stripped


def test_transform_writes_clean_item_for_docx(isolated_dirs: dict[str, Path]) -> None:
    """A DOCX source markdown produces a clean item with frontmatter + meta.json."""
    _write_source_md(isolated_dirs["docx_source"], "memo-q1", _source_body("memo-q1"))

    entries = transform_local_files(content_type="docx-document")

    assert len(entries) == 1
    item_dir = isolated_dirs["clean_dir"] / "docx-document" / "memo-q1"
    assert item_dir.exists()
    meta = json.loads((item_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["content_type"] == "docx-document"
    assert meta["source_id"] == "docx"
    assert meta["source_file"] == "memo-q1.docx"


def test_transform_handles_empty_source_dir(isolated_dirs: dict[str, Path]) -> None:
    """No source files = no entries, no exception."""
    entries = transform_local_files(content_type="pdf-document")
    assert entries == []


def test_transform_strips_contents_section_for_pdf(isolated_dirs: dict[str, Path]) -> None:
    """A PDF body with a Contents TOC gets the TOC stripped with an explanatory comment."""
    body = (
        "## Source\n\n"
        "`charter.pdf`\n\n"
        "# Charter\n\n"
        "## **Contents**\n"
        "Section A .................. 1\n"
        "Section B .................. 2\n"
        "\n## **Section A**\n\n"
        "Real content.\n"
    )
    _write_source_md(isolated_dirs["pdf_source"], "charter", body)

    transform_local_files(content_type="pdf-document")

    md = (isolated_dirs["clean_dir"] / "pdf-document" / "charter" / "charter.md").read_text(
        encoding="utf-8"
    )
    assert "## **Contents**" not in md
    assert "Contents (TOC) table has been removed" in md
    assert "## **Section A**" in md


def test_full_transform_regenerates_index(isolated_dirs: dict[str, Path]) -> None:
    """A full (no-arg) transform writes both clean items and ``_index.json``."""
    _write_source_md(isolated_dirs["pdf_source"], "report-2026", _source_body("report-2026"))
    _write_source_md(isolated_dirs["docx_source"], "memo-q1", _source_body("memo-q1"))

    entries = transform_local_files()
    assert {e["content_type"] for e in entries} == {"pdf-document", "docx-document"}

    index_path = isolated_dirs["clean_dir"] / "_index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(index) == 2
    assert {entry["stem"] for entry in index} == {"report-2026", "memo-q1"}


def test_regenerate_clean_index_reads_existing_items(isolated_dirs: dict[str, Path]) -> None:
    """``regenerate_clean_index`` rebuilds the index from disk without re-transforming."""
    # First populate the clean layer AND write the index (full transform)
    _write_source_md(isolated_dirs["pdf_source"], "report-2026", _source_body("report-2026"))
    transform_local_files()  # no content_type arg → writes _index.json

    # Now nuke the index and confirm regenerate brings it back
    index_path = isolated_dirs["clean_dir"] / "_index.json"
    index_path.unlink()
    count = regenerate_clean_index()
    assert count == 1
    assert index_path.exists()


def test_source_registry_has_expected_entries() -> None:
    """The source registry lists both PDF and DOCX content types."""
    assert "pdf-document" in _SOURCE_REGISTRY
    assert "docx-document" in _SOURCE_REGISTRY
