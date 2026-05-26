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
    & $python -m PyInstaller --noconfirm --clean --specpath build --onefile --name ChessChampionServer scripts\run_tcp_session_server.py
    Write-Host "Build complete. Artifact is in dist/ChessChampionServer.exe" -ForegroundColor Green
}
else {
    & $python -m PyInstaller --noconfirm --clean --specpath build --name ChessChampionServer scripts\run_tcp_session_server.py
    Write-Host "Build complete. Artifacts are in dist/ChessChampionServer" -ForegroundColor Green
}