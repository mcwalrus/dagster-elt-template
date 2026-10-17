"""Normalize data/sources/ into the data/clean/ layer.

Reads the raw converter output for every file type (PDF, DOCX) and writes
normalized items to::

    data/clean/{content-type}/{stem}/{stem}.md   — YAML frontmatter + body
    data/clean/{content-type}/{stem}/meta.json   — machine-readable metadata
    data/clean/_index.json                       — flat cross-type search index

Provenance fields written to every item
---------------------------------------
stem, content_type, source_id, source_type, source_file, source_path,
ingested_at, cleaned_at, title
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003 — used at runtime in function bodies

from pipeline.paths import CLEAN_DIR, DOCX_SOURCES_DIR, PDF_SOURCES_DIR
from pipeline.transforms.clean import (
    normalise_blank_runs,
    strip_contents_section,
    strip_duplicate_h1,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maps content_type -> (source directory, source_id, source_type)
# Add a new entry here when introducing a new ingestor (e.g. EPUB, HTML).
_SOURCE_REGISTRY: dict[str, tuple[Path, str, str]] = {
    "pdf-document": (PDF_SOURCES_DIR, "pdf", "pdf"),
    "docx-document": (DOCX_SOURCES_DIR, "docx", "docx"),
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def transform_local_files(content_type: str | None = None) -> list[dict[str, str]]:
    """Read converted files from sources and write normalized items to data/clean/.

    Args:
        content_type: When provided, only the matching content type is processed
            and written to ``data/clean/{type}/`` — other directories are not
            touched. Accepted values: ``'pdf-document'``, ``'docx-document'``.
            When ``None`` (default) all registered types are processed and
            ``data/clean/_index.json`` is regenerated.

    Returns a list of index entries suitable for ``data/clean/_index.json``.
    """
    cleaned_at = datetime.now(UTC).isoformat()
    index_entries: list[dict[str, str]] = []

    for ct, (source_dir, source_id, source_type) in _SOURCE_REGISTRY.items():
        if content_type is not None and content_type != ct:
            continue
        index_entries += _transform_one_type(ct, source_dir, source_id, source_type, cleaned_at)

    if content_type is None:
        _write_index(index_entries)
        print(f"  📋 clean/_index.json  ({len(index_entries)} items)")

    return index_entries


def regenerate_clean_index() -> int:
    """Regenerate data/clean/_index.json from the existing clean data.

    Scans every ``meta.json`` under CLEAN_DIR without re-running the full
    transform pipeline, then writes a fresh cross-type search index.

    Returns the number of index entries written.
    """
    entries: list[dict[str, str]] = []
    if CLEAN_DIR.exists():
        for type_dir in sorted(CLEAN_DIR.iterdir()):
            if not type_dir.is_dir() or type_dir.name.startswith("_"):
                continue
            for item_dir in sorted(type_dir.iterdir()):
                if not item_dir.is_dir():
                    continue
                meta_file = item_dir / "meta.json"
                if not meta_file.exists():
                    continue
                with open(meta_file) as fh:
                    meta: dict[str, object] = json.load(fh)
                entries.append(
                    {
                        "stem": str(meta.get("stem", "")),
                        "slug": str(meta.get("stem", "")),  # alias for cross-compat
                        "content_type": str(meta.get("content_type", "")),
                        "source_id": str(meta.get("source_id", "")),
                        "source_file": str(meta.get("source_file", "")),
                        "title": str(meta.get("title", "")),
                        "ingested_at": str(meta.get("ingested_at", "")),
                    }
                )
    _write_index(entries)
    return len(entries)


# ---------------------------------------------------------------------------
# Per-type transforms
# ---------------------------------------------------------------------------


def _transform_one_type(
    content_type: str,
    source_dir: Path,
    source_id: str,
    source_type: str,
    cleaned_at: str,
) -> list[dict[str, str]]:
    """Transform every ``*.md`` in *source_dir* into a clean item.

    Source markdown files must have been written by the corresponding
    ingestor (``pipeline.ingestion.{pdf,docx}_convert``). The transform
    strips the ingestion-side ``## Source`` marker, applies content-type
    specific cleanup (Contents-section stripping for PDFs), and writes
    a clean item per file.
    """
    if not source_dir.exists():
        return []

    entries: list[dict[str, str]] = []
    for md_file in sorted(source_dir.glob("*.md")):
        raw = md_file.read_text(encoding="utf-8")
        stem = md_file.stem

        title = _extract_title(raw) or stem.replace("-", "_").replace("_", " ").title()

        # Strip the ingestor's "## Source" marker + filename line.
        body = _strip_source_marker(raw)
        body = strip_duplicate_h1(body, title)

        # PDF-specific: drop the duplicated TOC table pymupdf4llm emits.
        if content_type == "pdf-document":
            body, had_contents = strip_contents_section(body)
            if had_contents:
                body = (
                    "<!-- The Contents (TOC) table has been removed during transformation; "
                    "the rendered document provides its own navigation. -->\n\n" + body
                )

        body = normalise_blank_runs(body)

        meta: dict[str, object] = {
            "stem": stem,
            "content_type": content_type,
            "source_id": source_id,
            "source_type": source_type,
            "source_file": f"{stem}.{source_type}",
            "source_path": f"data/sources/{source_id}/{stem}.{source_type}",
            "ingested_at": _source_mtime(source_dir, stem, source_type),
            "cleaned_at": cleaned_at,
            "title": title,
        }
        _write_clean_item(content_type, stem, meta, body)
        print(f"  📝 clean/{content_type}/{stem}/{stem}.md")

        entries.append(
            {
                "stem": stem,
                "slug": stem,
                "content_type": content_type,
                "source_id": source_id,
                "source_file": meta["source_file"],
                "title": title,
                "ingested_at": str(meta["ingested_at"]),
            }
        )

    return entries


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def _write_clean_item(
    content_type: str,
    stem: str,
    meta: dict[str, object],
    body: str,
) -> None:
    """Write ``{stem}.md`` and ``meta.json`` into ``data/clean/{content_type}/{stem}/``.

    ``meta.json`` is written as a merge of the existing on-disk fields
    and the new ``meta`` dict (new fields win). This preserves
    out-of-band fields added by downstream consumers when the transform
    pipeline re-materialises the item.
    """
    item_dir = CLEAN_DIR / content_type / stem
    item_dir.mkdir(parents=True, exist_ok=True)

    # Write .md with YAML frontmatter
    frontmatter = _build_frontmatter(meta)
    md_content = frontmatter + "\n" + body.lstrip("\n")
    (item_dir / f"{stem}.md").write_text(md_content, encoding="utf-8")

    # Preserve existing meta.json fields the transform didn't compute.
    meta_path = item_dir / "meta.json"
    if meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        merged = {**existing, **meta}
    else:
        merged = meta

    meta_path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_index(entries: list[dict[str, str]]) -> None:
    """Write the flat cross-type search index to data/clean/_index.json."""
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    index_path = CLEAN_DIR / "_index.json"
    index_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------


def _build_frontmatter(fields: dict[str, object]) -> str:
    """Build a minimal YAML frontmatter block from a dict.

    Rules:
    - ``None``, ``""``, and ``[]`` values are omitted.
    - String values are double-quoted with internal quotes escaped.
    """
    lines = ["---"]
    for key, value in fields.items():
        if value is None or value == "" or value == []:
            continue
        lines.append(f'{key}: "{_esc(str(value))}"')
    lines.append("---")
    return "\n".join(lines)


def _esc(s: str) -> str:
    """Escape a string for use inside YAML double-quoted scalars."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_title(body: str) -> str:
    """Return the text of the first ``# Heading`` in the body, or ``""``.

    Skips ``## Source`` markers written by the ingestor.
    """
    for line in body.split("\n"):
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            return m.group(1).strip()
    return ""


_SOURCE_MARKER_RE = re.compile(
    r"^## Source\s*\n+\s*`[^`]+`\s*\n+",
    re.MULTILINE,
)


def _strip_source_marker(body: str) -> str:
    """Remove the ``## Source`` / `` `filename.ext` `` block written by ingestors."""
    return _SOURCE_MARKER_RE.sub("", body, count=1)


def _source_mtime(source_dir: Path, stem: str, source_type: str) -> str:
    """Return the mtime of the original source file as an ISO-8601 string.

    Falls back to ``cleaned_at`` (caller's responsibility) if the file
    doesn't exist — should never happen for items in the clean layer.
    """
    source_file = source_dir / f"{stem}.{source_type}"
    if not source_file.exists():
        return ""
    from datetime import UTC, datetime

    return datetime.fromtimestamp(source_file.stat().st_mtime, tz=UTC).isoformat()
