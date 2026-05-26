Param(
    [string]$BundleName = "LAN-Test-Pack"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$clientBuildScript = Join-Path $projectRoot "scripts\build_windows.ps1"
$serverBuildScript = Join-Path $projectRoot "scripts\build_server_windows.ps1"

if (-not (Test-Path $clientBuildScript)) {
    throw "Missing client build script: $clientBuildScript"
}

if (-not (Test-Path $serverBuildScript)) {
    throw "Missing server build script: $serverBuildScript"
}

Write-Host "Building client artifact..." -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File $clientBuildScript

Write-Host "Building server artifact..." -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File $serverBuildScript

$distRoot = Join-Path $projectRoot "dist"
$clientDir = Join-Path $distRoot "ChessChampion"
$serverDir = Join-Path $distRoot "ChessChampionServer"

if (-not (Test-Path $clientDir)) {
    throw "Expected client artifact directory not found: $clientDir"
}

if (-not (Test-Path $serverDir)) {
    throw "Expected server artifact directory not found: $serverDir"
}

$bundleRoot = Join-Path $distRoot $BundleName
$hostRoot = Join-Path $bundleRoot "Host-PC"
$guestRoot = Join-Path $bundleRoot "Guest-PC"
$hostClientRoot = Join-Path $hostRoot "ChessChampion"
$guestClientRoot = Join-Path $guestRoot "ChessChampion"
$hostServerRoot = Join-Path $hostRoot "ChessChampionServer"

if (Test-Path $bundleRoot) {
    Remove-Item $bundleRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $hostRoot | Out-Null
New-Item -ItemType Directory -Path $guestRoot | Out-Null

Copy-Item $clientDir -Destination $hostClientRoot -Recurse -Force
Copy-Item $clientDir -Destination $guestClientRoot -Recurse -Force
Copy-Item $serverDir -Destination $hostServerRoot -Recurse -Force

$hostStartServer = @'
@echo off
setlocal
cd /d "%~dp0ChessChampionServer"
ChessChampionServer.exe --host 0.0.0.0 --port 8765
endlocal
'@

$hostStartClient = @'
@echo off
setlocal
cd /d "%~dp0ChessChampion"
ChessChampion.exe
endlocal
'@

$guestStartClient = @'
@echo off
setlocal
cd /d "%~dp0ChessChampion"
ChessChampion.exe
endlocal
'@

Set-Content -Path (Join-Path $hostRoot "Start-Server.bat") -Value $hostStartServer -Encoding ASCII
Set-Content -Path (Join-Path $hostRoot "Start-Client.bat") -Value $hostStartClient -Encoding ASCII
Set-Content -Path (Join-Path $guestRoot "Start-Client.bat") -Value $guestStartClient -Encoding ASCII

$readme = @'
ChessChampion LAN Test Pack

Host-PC:
1) Run Start-Server.bat
2) Run Start-Client.bat
3) In game, choose Online -> Host
4) Use transport TCP, host 127.0.0.1, port 8765
5) Share invite code with guest

Guest-PC:
1) Copy Guest-PC folder to second machine
2) Run Start-Client.bat
3) In game, choose Online -> Join
4) Use transport TCP, host <HOST-LAN-IP>, port 8765
5) Enter invite code from host

R3 Success Criteria:
- Complete one full game over LAN.
- Verify reconnect at least once mid-game.
'@

Set-Content -Path (Join-Path $bundleRoot "README.txt") -Value $readme -Encoding ASCII

Write-Host "LAN test bundle ready at: $bundleRoot" -ForegroundColor Green