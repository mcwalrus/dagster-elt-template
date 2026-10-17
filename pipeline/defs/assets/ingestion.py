"""Ingestion layer assets — convert PDF/DOCX files into raw markdown.

Outputs raw markdown files into ``data/sources/{pdf,docx}/``, one
``.md`` per source file. The clean-layer assets then wrap each into a
canonical item with YAML frontmatter + meta.json.
"""

# NOTE: do NOT add `from __future__ import annotations` here. Dagster
# inspects the ``context`` parameter's annotation at decoration time to
# validate it against ``AssetExecutionContext``; PEP-563 string
# annotations break that.

import dagster as dg
from dagster import AssetExecutionContext

from pipeline.ingestion import convert_all_docx, convert_all_pdfs
from pipeline.paths import DOCX_SOURCES_DIR, PDF_SOURCES_DIR


@dg.asset(group_name="ingestion")
def ingest_pdfs(context: AssetExecutionContext) -> dg.MaterializeResult:
    """Convert every PDF in ``data/sources/pdf/`` into raw markdown.

    Output: one ``.md`` per ``.pdf``, written next to the original file.
    """
    results = convert_all_pdfs(PDF_SOURCES_DIR)
    context.log.info("Converted %d PDFs", len(results))
    return dg.MaterializeResult(
        metadata={
            "file_count": len(results),
            "source_dir": str(PDF_SOURCES_DIR),
            "files": [r["source_file"] for r in results],
        }
    )


@dg.asset(group_name="ingestion")
def ingest_docx(context: AssetExecutionContext) -> dg.MaterializeResult:
    """Convert every DOCX in ``data/sources/docx/`` into raw markdown.

    Output: one ``.md`` per ``.docx``, written next to the original file.
    """
    results = convert_all_docx(DOCX_SOURCES_DIR)
    context.log.info("Converted %d DOCX files", len(results))
    return dg.MaterializeResult(
        metadata={
            "file_count": len(results),
            "source_dir": str(DOCX_SOURCES_DIR),
            "files": [r["source_file"] for r in results],
        }
    )
