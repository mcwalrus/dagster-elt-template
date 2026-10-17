# Agent Instructions

## Project Overview

A [Dagster](https://dagster.io) template for converting PDF and DOCX
files into clean, ingestible markdown. Drop source files into
`data/sources/{pdf,docx}/`, run the pipeline, and the normalised
content appears in `data/clean/`.

## Key Paths

| Path                                        | Description                                                          | Git     |
| ------------------------------------------- | -------------------------------------------------------------------- | ------- |
| `data/sources/{pdf,docx}/`                  | Raw source files + ingestor output — write-only                       | Ignored |
| `data/clean/`                               | Normalised content — canonical source for all consumers              | Tracked |
| `data/clean/_index.json`                    | Cross-type search index (regenerated each transform run)             | Tracked |
| `pipeline/`                                 | Dagster code location — wraps ingestion + transforms as assets       | —       |
| `docs/data-architecture.md`                 | Pipeline design, layer invariants, how to add source/consumer        | Tracked |
| `docs/data-schema.md`                       | Per-content-type schema for `data/clean/` items                      | Tracked |
| `docs/dependencies.md`                      | Why each dependency exists (grouped by purpose)                      | Tracked |

## Data Pipeline

[httpx](https://www.python-httpx.org/) is **not** in this project — there is
no scraping layer. The pipeline is purely local-file ingestion.

### Operations go through Dagster

**Most operations should be expressed as Dagster assets** — not as
standalone scripts or justfile recipes. The justfile is reserved for:

- **Local development tooling** that doesn't fit the asset model
  (interactive dev servers, manual lint runs, lefthook setup).
- **Quality gates** (lint, type-check, test) that run pre-commit or in CI.

If you want to add a new data-pipeline operation (a new source type, a
new clean step, an index regeneration), model it as a Dagster asset
under `pipeline/defs/assets/` and wire it into `full_pipeline` in
`pipeline/defs/jobs.py`.

### Adding new Dagster assets

When you add a new asset:

1. **Pick the right group** (`ingestion`, `clean`) — this drives job selection.
2. **Declare upstream deps** via the `deps=[...]` argument on `@dg.asset`.
   Don't rely on file-path inference.
3. **Register the asset** in `pipeline/definitions.py` and add it to the
   appropriate job in `pipeline/defs/jobs.py` if it needs to run as part
   of `full_pipeline`.

### Type-annotation note for Dagster assets

Do **not** add `from __future__ import annotations` to files that define
Dagster assets. PEP-563 string annotations break Dagster's runtime
validation of `context: AssetExecutionContext`. The existing
`pipeline/defs/assets/{ingestion,clean}.py` are correct reference
patterns.

## Setup

Run the onboarding script once on a fresh machine (macOS/Linux only):

```bash
./scripts/setup.sh
```

This installs all system dependencies via Homebrew (`scripts/Brewfile`),
configures shell hooks for `direnv`, installs Python via `uv`, and
wires up git hooks. Keep track of all tools or major dependencies going
forward.

## CLI Tools

| Tool       | Purpose                                                            |
| ---------- | ------------------------------------------------------------------ |
| `uv`       | Dependency management and script runner (`uv sync`, `uv run`)      |
| `just`     | Task runner — see `justfile` for recipes (lint, dev, open)         |
| `ruff`     | Linter and formatter for Python                                    |
| `ty`       | Static type checker for Python                                     |
| `lefthook` | Git hook manager (pre-commit runs ruff + ty)                       |
| `direnv`   | Per-directory env vars — run `direnv allow` after cloning          |
| `pi`       | AI coding agent — install via `scripts/setup.sh`                   |
| `dg`       | CLI for managing Dagster projects                                  |
| `dagster`  | CLI tools for working with Dagster                                 |

## Python Libraries

| Library       | Purpose                                       |
| ------------- | --------------------------------------------- |
| `pymupdf4llm` | PDF to markdown converter                     |
| `markitdown`  | DOCX to markdown converter                    |
| `dagster`     | ETL pipeline orchestration (asset-based)      |

## Common Commands

### Dagster — data pipeline (primary)

```bash
just dev            # Open the Dagster UI (dg dev) — pick jobs to launch from there
uv run dg launch    # Run a job headless (see `uv run dg launch --help` for options)
```

Inside the Dagster UI, the canonical jobs are:

- **`full_pipeline`** — ingest PDFs + DOCX → clean → regenerate index.
- **`ingestion_job`** — ingest only (convert source files to raw markdown).
- **`transforms_job`** — clean only (normalize raw markdown into `data/clean/`).

### Justfile — local tooling

```bash
just install        # uv sync
just check          # ruff check + ruff format --check + ty check + pytest (read-only, CI-safe)
just fix            # ruff check --fix + ruff format
just open           # Open data/ in Finder
just hooks-install  # Wire lefthook into .git/hooks (once after cloning)
```

## Quality Gates

```bash
just check   # Must pass before committing
```

Pre-commit hooks (via lefthook) run ruff-lint, ruff-format, and ty
automatically on staged files. See [`docs/dependencies.md`](docs/dependencies.md).