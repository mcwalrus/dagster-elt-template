# Data Architecture

This document describes the full data pipeline for the
dagster-elt-template: from raw PDF/DOCX files through the
normalized clean layer.

---

## Pipeline Overview

```
PDF/DOCX in data/sources/{pdf,docx}/
        │
        ▼ ingestors (pipeline.ingestion.*)
data/sources/{pdf,docx}/{stem}.md     ← raw converter output, gitignored
        │
        ▼ transforms/sources/local_files.py
data/clean/{content-type}/{stem}/     ← canonical, git-tracked
        │
        ├──▶ {stem}.md                ──▶ ingestible markdown (frontmatter + body)
        └──▶ meta.json                ──▶ machine-readable metadata
```

Run the full pipeline with:

```bash
just dev               # open Dagster UI — launch full_pipeline from there
uv run dg launch full_pipeline --job full_pipeline
```

---

## Layer Invariants

### `data/sources/`

- **Owner:** ingestors (`pipeline/ingestion/pdf_convert.py`,
  `pipeline/ingestion/docx_convert.py`).
- **Contract:** Ingestors write here; consumers MUST NOT read from this path.
- **Gitignore:** Entirely gitignored. The raw converter output is
  ephemeral — regenerate it by re-running an ingestion job.
- **Format:** One directory per source (`pdf/`, `docx/`), with a `.md`
  per source file (PDF or DOCX binary).
- **Binary media:** Source PDFs and DOCX files live in their respective
  source directories alongside their converter output. Both are
  gitignored; clean items reference them by relative path via the
  ``source_path`` field in ``meta.json``.

### `data/clean/`

- **Owner:** transform pipeline (`transforms/sources/local_files.py`).
- **Contract:** All consumers read from here. Never modified by ingestors.
- **Gitignore:** Tracked by git. This is the durable, version-controlled
  record of normalized content.
- **Format:** `data/clean/{content-type}/{stem}/{stem}.md` + `meta.json`.
  See [data-schema.md](data-schema.md) for the full schema per content type.
- **Index:** `data/clean/_index.json` is regenerated on every clean
  transform run. It is a flat array of `{stem, content_type, source_id,
  source_file, title, ingested_at}` entries — suitable for
  search/discovery without reading individual files.

---

## Directory Reference

```
data/
├── sources/                            # [gitignored] raw converter output
│   ├── pdf/                            # PDF ingestor output
│   │   └── {stem}.pdf                  # original binary
│   │   └── {stem}.md                   # raw converter markdown
│   └── docx/                           # DOCX ingestor output
│       └── {stem}.docx                 # original binary
│       └── {stem}.md                   # raw converter markdown
│
└── clean/                              # [git-tracked] normalized consumer-ready content
    ├── _index.json                     # Cross-type search index (regenerated each run)
    ├── pdf-document/
    │   └── {stem}/
    │       ├── {stem}.md               # YAML frontmatter + cleaned markdown body
    │       └── meta.json               # Machine-readable metadata
    └── docx-document/
        └── {stem}/
            ├── {stem}.md
            └── meta.json
```

---

## How to Add a New Source Type

1. **Add a converter** under `pipeline/ingestion/` — implement two
   public functions: ``convert_one(path) -> dict`` and
   ``convert_all(source_dir) -> list[dict]``. Mirror the shape of
   `pdf_convert.py` / `docx_convert.py`.

2. **Register the source** in
   `pipeline/transforms/sources/local_files.py:_SOURCE_REGISTRY`:

   ```python
   _SOURCE_REGISTRY["epub-document"] = (EPUB_SOURCES_DIR, "epub", "epub")
   ```

3. **Add the ingestor + clean assets** in
   `pipeline/defs/assets/{ingestion,clean}.py`, mirroring the existing
   `ingest_pdfs` / `clean_pdfs` pair.

4. **Wire them into** `pipeline/definitions.py` and add to
   `full_pipeline` in `pipeline/defs/jobs.py`.

5. **Test** by dropping a sample file into the new source directory
   and running `just dev` → `full_pipeline`.

---

## How to Add a New Consumer

Consumers read from `data/clean/`. They MUST NOT read from `data/sources/`.

1. **Read `data/clean/_index.json`** for a quick overview of all items
   (stem, content_type, source_id, source_file, title, ingested_at)
   without reading individual files.

2. **Read individual items** from `data/clean/{content-type}/{stem}/`:
   - `meta.json` for structured, machine-readable metadata (no YAML parsing)
   - `{stem}.md` for the human-readable body with YAML frontmatter

3. **Handle missing items gracefully** — `data/clean/` is rebuilt by the
   transform pipeline. If a source is offline or empty, some content
   types may be absent. Consumers should handle this without crashing.

---

## Transform Modules Reference

| Module | Reads from | Writes to |
|---|---|---|
| `pipeline/ingestion/pdf_convert.py` | `data/sources/pdf/*.pdf` | `data/sources/pdf/*.md` |
| `pipeline/ingestion/docx_convert.py` | `data/sources/docx/*.docx` | `data/sources/docx/*.md` |
| `pipeline/transforms/sources/local_files.py` | `data/sources/{pdf,docx}/*.md` | `data/clean/` |