# Aether Local & CI Validation Runner (Windows PowerShell)
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "backend/src"

Write-Host "=== Running Aether Platform Validation ===" -ForegroundColor Cyan

# 1. Ruff lint checks
Write-Host "Running Ruff Linter..." -ForegroundColor Green
.\.venv\Scripts\ruff check backend/src backend/tests services
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff lint validation failed!"
}

# 2. MyPy type check
Write-Host "Running MyPy Strict Type Checker..." -ForegroundColor Green
.\.venv\Scripts\mypy
if ($LASTEXITCODE -ne 0) {
    Write-Error "MyPy type validation failed!"
}

# 3. PyTest with Coverage
Write-Host "Running PyTest with Coverage Thresholds..." -ForegroundColor Green
.\.venv\Scripts\pytest --cov=backend/src/aether --cov-report=term-missing
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyTest suite failed!"
}

# 4. Next.js Web type check
Write-Host "Running Next.js Web Client Type Checker..." -ForegroundColor Green
.\.corepack-bin\pnpm --filter web typecheck
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pnpm web client type check failed!"
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Success: All validation checks passed cleanly!" -ForegroundColor Cyan
