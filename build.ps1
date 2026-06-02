# Build ConferenceFinder.exe (uses project .venv — pyinstaller is not on global PATH)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$VenvPyInstaller = Join-Path $Root ".venv\Scripts\pyinstaller.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv (Join-Path $Root ".venv")
}

Write-Host "Installing dependencies..."
& (Join-Path $Root ".venv\Scripts\pip.exe") install -q -r (Join-Path $Root "requirements.txt")

if (-not (Test-Path $VenvPyInstaller)) {
    Write-Host "PyInstaller not found in venv. Installing..."
    & (Join-Path $Root ".venv\Scripts\pip.exe") install pyinstaller
}

$exe = Join-Path $Root "dist\ConferenceFinder.exe"
if (Test-Path $exe) {
    Write-Host "Removing old executable..."
    Remove-Item $exe -Force -ErrorAction SilentlyContinue
    if (Test-Path $exe) {
        Write-Host "ERROR: Close ConferenceFinder.exe if it is running, then run build.ps1 again."
        exit 1
    }
}

Write-Host "Building with PyInstaller..."
Set-Location $Root
& $VenvPyInstaller build.spec --noconfirm

if (Test-Path $exe) {
    Write-Host ""
    Write-Host "Success: $exe"
} else {
    Write-Host "Build finished but exe not found. Check build\build\warn-build.txt"
    exit 1
}
