"""Shared path constants for the pipeline.

All data directories are resolved relative to the project root
(where ``pyproject.toml`` lives).
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Source layer — raw file conversions (written by ingestion, never by consumers)
# ---------------------------------------------------------------------------
SOURCES_DIR = PROJECT_ROOT / "data" / "sources"

# Per-source subdirectories. Each ingestor writes into its own folder so
# different file types (PDF vs DOCX) don't mix.
PDF_SOURCES_DIR = SOURCES_DIR / "pdf"
DOCX_SOURCES_DIR = SOURCES_DIR / "docx"

# ---------------------------------------------------------------------------
# Clean layer — normalised content, canonical source for all consumers
# ---------------------------------------------------------------------------
CLEAN_DIR = Path("data/clean")
