"""Dagster job definitions for the dagster-elt-template pipeline."""

import dagster as dg

# ---------------------------------------------------------------------------
# Asset selections
# ---------------------------------------------------------------------------

_ingestion_assets = dg.AssetSelection.groups("ingestion")

_clean_assets = dg.AssetSelection.groups("clean")

# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

full_pipeline = dg.define_asset_job(
    name="full_pipeline",
    description=(
        "Convert every PDF/DOCX in ``data/sources/`` and normalise into "
        "``data/clean/``. End-to-end ingestion → clean → index."
    ),
    selection=_ingestion_assets | _clean_assets,
)

ingestion_job = dg.define_asset_job(
    name="ingestion_job",
    description=(
        "Convert every PDF/DOCX in ``data/sources/`` into raw markdown. "
        "Output lives next to the source files (one ``.md`` per binary)."
    ),
    selection=_ingestion_assets,
)

transforms_job = dg.define_asset_job(
    name="transforms_job",
    description=(
        "Normalise raw source markdown into the clean layer "
        "(``data/clean/``) and regenerate the search index. Re-runs are "
        "idempotent — they overwrite existing items with current content."
    ),
    selection=_clean_assets,
)
