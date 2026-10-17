# dagster-elt-template
# Run `just` to see available recipes.
#
# All data-pipeline operations (PDF/DOCX extraction, cleaning, indexing)
# are managed as Dagster assets — run `just dev` to open the UI, or launch
# them headless with `dg launch`. Linting and one-shot tooling stay in
# this justfile so they're trivial to run outside the pipeline.

# Install Python dependencies
install:
    uv sync

# Launch the Dagster UI dev server
dev:
    uv run dg dev

# Open data/ in Finder
open:
    open data

# Verify code quality: lint + format-check + type-check + tests (read-only, safe for CI)
check: install
    uv run ruff check .
    uv run ruff format --check .
    uv run ty check .
    uv run pytest tests/ -q

# Auto-fix lint issues and reformat (ty has no autofix — run `just check` after)
fix: install
    uv run ruff check --fix .
    uv run ruff format .

# Run pytest suite (extraction unit tests, etc.)
test: install
    uv run pytest tests/ -q

# Wire lefthook into .git/hooks (run once after cloning)
hooks-install:
    lefthook install
    @echo "Git hooks installed via lefthook."