"""Clean layer assets — normalise raw file conversions to ``data/clean/``.

Each clean item is a directory containing ``{stem}.md`` (YAML frontmatter +
body) and ``meta.json`` (machine-readable metadata). The cross-type
search index at ``data/clean/_index.json`` is regenerated on every
clean run.
"""

# NOTE: do NOT add `from __future__ import annotations` here. Dagster
# inspects the ``context`` parameter's annotation at decoration time to
# validate it against ``AssetExecutionContext``; PEP-563 string
# annotations break that.

from pathlib import Path

import dagster as dg

from pipeline.paths import CLEAN_DIR
from pipeline.transforms.sources.local_files import regenerate_clean_index, transform_local_files


def _item_count(path: Path) -> int:
    """Count immediate subdirectories (one per cleaned item) under *path*."""
    if not path.exists():
        return 0
    return sum(1 for p in path.iterdir() if p.is_dir())


@dg.asset(group_name="clean", deps=["ingest_pdfs"])
def clean_pdfs() -> dg.MaterializeResult:
    """Normalise raw PDF markdown → ``data/clean/pdf-document/``."""
    entries = transform_local_files(content_type="pdf-document")
    output_dir = CLEAN_DIR / "pdf-document"
    return dg.MaterializeResult(
        metadata={
            "item_count": _item_count(output_dir),
            "output_path": str(output_dir),
            "new_entries": len(entries),
        }
    )


@dg.asset(group_name="clean", deps=["ingest_docx"])
def clean_docx() -> dg.MaterializeResult:
    """Normalise raw DOCX markdown → ``data/clean/docx-document/``."""
    entries = transform_local_files(content_type="docx-document")
    output_dir = CLEAN_DIR / "docx-document"
    return dg.MaterializeResult(
        metadata={
            "item_count": _item_count(output_dir),
            "output_path": str(output_dir),
            "new_entries": len(entries),
        }
    )


@dg.asset(
    group_name="clean",
    deps=["clean_pdfs", "clean_docx"],
)
def clean_index() -> dg.MaterializeResult:
    """Regenerate ``data/clean/_index.json`` from all existing clean content."""
    count = regenerate_clean_index()
    index_path = CLEAN_DIR / "_index.json"
    return dg.MaterializeResult(
        metadata={
            "item_count": count,
            "output_path": str(index_path),
        }
    )
