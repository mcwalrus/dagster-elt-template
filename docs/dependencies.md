# Dependencies

Every tool the project depends on, grouped by what it's used for. For
the canonical version pins, see `pyproject.toml` and `scripts/Brewfile`.

## Local environment

| Tool | Purpose |
| --- | --- |
| [`direnv`](https://direnv.net) | Loads `.envrc` on `cd` — stable `DAGSTER_HOME` + venv `PATH` |
| [`uv`](https://docs.astral.sh/uv) | Python toolchain + dependency manager (reads `.python-version`) |
| [`just`](https://github.com/casey/just) | Task runner — see `justfile` for recipes |
| [`lefthook`](https://lefthook.com) | Git hook manager (pre-commit: ruff, ty) |

## Pipeline orchestration

| Tool | Purpose |
| --- | --- |
| [`dagster`](https://dagster.io) | Asset-based pipeline orchestrator — gives every artefact lineage + observability |
| [`dagster-webserver`](https://dagster.io) | Dagster UI (the `just dev` surface) |
| [`dagster-dg-cli`](https://docs.dagster.io/api/clis/dg-cli/dg-cli-reference) | Project scaffolding + asset/job launch (`dg launch`) |

## File conversion

| Tool | Purpose |
| --- | --- |
| [`pymupdf4llm`](https://pymupdf.io) | PDF → Markdown extraction. Captures tables, headings, and bullet lists with no system dependencies. |
| [`markitdown`](https://github.com/microsoft/markitdown) | DOCX → Markdown extraction (Microsoft-maintained, robust for headings, lists, and tables). |

## Python developer tooling

| Tool | Purpose |
| --- | --- |
| [`ruff`](https://docs.astral.sh/ruff) | Linter + formatter (replaces black, isort, flake8) |
| [`ty`](https://github.com/astral-sh/ty) | Static type checker (pre-commit strict) |
| [`pytest`](https://docs.pytest.org) | Test runner |