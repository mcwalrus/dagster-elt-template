"""Convert DOCX files into structured markdown.

Uses Microsoft's markitdown for DOCX → markdown conversion. markitdown is
robust for headings, lists, tables, and basic inline formatting, with no
system dependencies.

Output is written to ``data/sources/docx/{stem}.md`` — one markdown file
per DOCX. The clean-layer transform then wraps each into a canonical
item with YAML frontmatter + meta.json.
"""

from __future__ import annotations

import logging
from pathlib import Path  # noqa: TC003 — used at runtime in function bodies

from markitdown import MarkItDown

from pipeline.paths import DOCX_SOURCES_DIR

logger = logging.getLogger(__name__)


def convert_all_docx(source_dir: Path = DOCX_SOURCES_DIR) -> list[dict]:
    """Find all DOCX files in *source_dir* and convert them to markdown.

    Returns a list of ``{"source_file", "output_file", "stem"}`` entries
    describing every conversion performed.
    """
    source_dir.mkdir(parents=True, exist_ok=True)

    docx_files = sorted(source_dir.glob("*.docx"))
    if not docx_files:
        logger.warning("No DOCX files found in %s", source_dir)
        return []

    logger.info("Found %d DOCX files in %s", len(docx_files), source_dir)
    results: list[dict] = []
    for docx_path in docx_files:
        try:
            entry = convert_docx(docx_path, source_dir)
            results.append(entry)
            logger.info("Converted: %s -> %s", docx_path.name, entry["output_file"])
        except Exception as e:
            logger.error("Failed to convert %s: %s", docx_path.name, e)
    return results


def convert_docx(docx_path: Path, source_dir: Path = DOCX_SOURCES_DIR) -> dict:
    """Convert a single DOCX file to markdown and save it next to the source file.

    Output lives in the same directory as the input, with the ``.md``
    extension replacing ``.docx``. This keeps the source→clean relationship
    one-to-one and trivially diffable.
    """
    converter = MarkItDown()
    result = converter.convert(str(docx_path))
    body_md = (result.text_content or "").strip()
    markdown = format_markdown(body_md, docx_path)

    output_path = docx_path.with_suffix(".md")
    output_path.write_text(markdown, encoding="utf-8")

    return {
        "source_file": docx_path.name,
        "output_file": output_path.name,
        "stem": docx_path.stem,
    }


def format_markdown(body_md: str, docx_path: Path) -> str:
    """Format body into a well-structured markdown document.

    Adds a level-2 ``Source`` marker so downstream consumers can trace
    the clean item back to its originating file.
    """
    lines = [
        "## Source",
        "",
        f"`{docx_path.name}`",
        "",
        body_md,
    ]
    return "\n".join(lines) + "\n"
