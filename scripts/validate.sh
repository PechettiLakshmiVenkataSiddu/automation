#!/usr/bin/env bash
set -eo pipefail
export PYTHONPATH=backend/src

echo "=== Running Aether Platform Validation ==="

# 1. Ruff lint checks
echo "Running Ruff Linter..."
.venv/bin/ruff check backend/src backend/tests services

# 2. MyPy type check
echo "Running MyPy Strict Type Checker..."
.venv/bin/mypy

# 3. PyTest with Coverage
echo "Running PyTest with Coverage Thresholds..."
.venv/bin/pytest --cov=backend/src/aether --cov-report=term-missing

# 4. Next.js Web type check
echo "Running Next.js Web Client Type Checker..."
./.corepack-bin/pnpm --filter web typecheck

echo "============================================="
echo "Success: All validation checks passed cleanly!"
