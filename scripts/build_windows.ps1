Param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Missing virtual environment python at .venv\\Scripts\\python.exe"
}

$python = ".venv\Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install pyinstaller

if ($OneFile) {
    & $python -m PyInstaller --noconfirm --clean --onefile --windowed --name ChessChampion --add-data "assets;assets" main.py
}
else {
    & $python -m PyInstaller --noconfirm --clean chesschampion.spec
}

Write-Host "Build complete. Artifacts are in dist/ChessChampion" -ForegroundColor Green
