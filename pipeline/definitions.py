"""Root-level Dagster code location entry point.

``dg dev`` discovers this file via the ``[tool.dagster]`` section in
``pyproject.toml``.  All assets and jobs are wired here.
"""

import dagster as dg

from pipeline.defs.assets.clean import clean_docx, clean_index, clean_pdfs
from pipeline.defs.assets.ingestion import ingest_docx, ingest_pdfs
from pipeline.defs.jobs import full_pipeline, ingestion_job, transforms_job

defs = dg.Definitions(
    jobs=[full_pipeline, ingestion_job, transforms_job],
    assets=[
        # ingestion layer
        ingest_pdfs,
        ingest_docx,
        # clean layer
        clean_pdfs,
        clean_docx,
        clean_index,
    ],
)
