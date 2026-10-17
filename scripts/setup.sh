#!/usr/bin/env bash
# Onboarding script for the dagster-elt-template project.
# macOS or Linux only. Idempotent — safe to re-run.

set -euo pipefail

# ---------------------------------------------------------------------------
# 1. System dependencies via Homebrew
# ---------------------------------------------------------------------------
if command -v brew >/dev/null 2>&1; then
    echo "==> Installing Homebrew dependencies from scripts/Brewfile"
    brew bundle --file=scripts/Brewfile
else
    echo "!! Homebrew not found. Install it from https://brew.sh first,"
    echo "   then re-run this script. The Brewfile lists the system packages."
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Shell hooks — direnv
# ---------------------------------------------------------------------------
if command -v direnv >/dev/null 2>&1; then
    echo "==> Allowing .envrc (direnv)"
    direnv allow
else
    echo "!! direnv not on PATH after brew install. Add the brew shell hook:"
    echo "      eval \"\$(direnv hook <your-shell>)\""
    exit 1
fi

# ---------------------------------------------------------------------------
# 3. Python dependencies via uv
# ---------------------------------------------------------------------------
if command -v uv >/dev/null 2>&1; then
    echo "==> Syncing Python dependencies (uv sync)"
    uv sync
else
    echo "!! uv not on PATH. Install from https://docs.astral.sh/uv/"
    exit 1
fi

# ---------------------------------------------------------------------------
# 4. Git hooks via lefthook
# ---------------------------------------------------------------------------
if command -v lefthook >/dev/null 2>&1; then
    echo "==> Installing git hooks (lefthook install)"
    lefthook install
else
    echo "!! lefthook not on PATH. Run: just hooks-install"
fi

echo ""
echo "==> Setup complete. Run 'just dev' to open the Dagster UI."