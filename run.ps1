# Launch US CS Conference Finder with project venv and dependencies.
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$VenvPip = Join-Path $Root ".venv\Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv (Join-Path $Root ".venv")
}

Write-Host "Installing dependencies..."
& $VenvPip install -q -r (Join-Path $Root "requirements.txt")

Write-Host "Starting Conference Finder..."
& $VenvPython (Join-Path $Root "src\main.py")
