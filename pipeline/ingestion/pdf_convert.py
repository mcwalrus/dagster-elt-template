"""Convert PDF files into structured markdown.

Uses pymupdf4llm for text extraction — produces structured markdown with
headings, reflowed paragraphs, and real tables, with no system dependencies
(pure-Python).

Output is written to ``data/sources/pdf/{stem}.md`` — one markdown file per
PDF. The clean-layer transform then wraps each into a canonical item with
YAML frontmatter + meta.json.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path  # noqa: TC003 — used at runtime in function bodies

import pymupdf4llm

from pipeline.paths import PDF_SOURCES_DIR
from pipeline.text_clean import strip_glyphs

logger = logging.getLogger(__name__)

# Picture placeholders inserted by pymupdf4llm
PICTURE_RE = re.compile(r"^\s*\**==>\s*picture.*<==\**\s*$")


def convert_all_pdfs(source_dir: Path = PDF_SOURCES_DIR) -> list[dict]:
    """Find all PDFs in *source_dir* and convert them to markdown.

    Returns a list of ``{"source_file", "output_file", "stem"}`` entries
    describing every conversion performed.
    """
    source_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(source_dir.glob("*.pdf"))
    if not pdfs:
        logger.warning("No PDFs found in %s", source_dir)
        return []

    logger.info("Found %d PDFs in %s", len(pdfs), source_dir)
    results: list[dict] = []
    for pdf_path in pdfs:
        try:
            entry = convert_pdf(pdf_path, source_dir)
            results.append(entry)
            logger.info("Converted: %s -> %s", pdf_path.name, entry["output_file"])
        except Exception as e:
            logger.error("Failed to convert %s: %s", pdf_path.name, e)
    return results


def convert_pdf(pdf_path: Path, source_dir: Path = PDF_SOURCES_DIR) -> dict:
    """Convert a single PDF to markdown and save it next to the source file.

    Output lives in the same directory as the input, with the ``.md``
    extension replacing ``.pdf``. This keeps the source→clean relationship
    one-to-one and trivially diffable.
    """
    raw_md = _extract_raw_markdown(pdf_path)
    body_md = clean_body(raw_md)

    markdown = format_markdown(body_md, pdf_path)

    output_path = pdf_path.with_suffix(".md")
    output_path.write_text(markdown, encoding="utf-8")

    return {
        "source_file": pdf_path.name,
        "output_file": output_path.name,
        "stem": pdf_path.stem,
    }


def _extract_raw_markdown(pdf_path: Path) -> str:
    """Return raw markdown from pymupdf4llm (no post-processing)."""
    return pymupdf4llm.to_markdown(str(pdf_path), show_progress=False)


def clean_body(raw_md: str) -> str:
    """Strip artifacts from pymupdf4llm output and return clean body markdown.

    Removes:
      1. Picture placeholders  (``**==> picture ... <==**``)
      2. Page footers / standalone page numbers (de-bolded before matching)
      3. Zero-width / replacement glyphs that pymupdf4llm embeds when a
         font glyph is unavailable.

    Public so the transform module can apply the same cleaning step
    that the ingestion produces — keeps ingestor output and any
    re-cleaning consistent.
    """
    out: list[str] = []
    for line in raw_md.split("\n"):
        stripped = line.strip()
        if PICTURE_RE.match(stripped):
            continue
        out.append(line.rstrip())

    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)  # collapse excessive blank lines
    text = strip_glyphs(text)
    return text.strip()


def format_markdown(body_md: str, pdf_path: Path) -> str:
    """Format body into a well-structured markdown document.

    Adds a level-2 ``Source`` marker so downstream consumers can trace
    the clean item back to its originating file.
    """
    lines = [
        "## Source",
        "",
        f"`{pdf_path.name}`",
        "",
        body_md,
    ]
    return "\n".join(lines) + "\n"
