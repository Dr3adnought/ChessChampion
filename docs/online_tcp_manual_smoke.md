# Online TCP Manual Smoke Runbook

This runbook verifies live Online PvP over the TCP transport (not the in-process shim).

## Preconditions

- Windows PowerShell session in project root.
- Virtual environment activated.
- No other process bound to the selected TCP port.

## 1) Start the TCP Session Server

In terminal A:

```powershell
.venv\Scripts\python.exe scripts\run_tcp_session_server.py --host 127.0.0.1 --port 8765
```

Expected output:

```text
TcpSessionServer listening on 127.0.0.1:8765
```

### Optional: Start Packaged Server (no Python required)

Build once:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_server_windows.ps1
```

Run packaged server:

```powershell
dist\ChessChampionServer\ChessChampionServer.exe --host 0.0.0.0 --port 8765
```

For single-file build:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_server_windows.ps1 -OneFile
dist\ChessChampionServer.exe --host 0.0.0.0 --port 8765
```

## 2) Start Host Client

In terminal B:

```powershell
$env:CHESSCHAMPION_ONLINE_TRANSPORT = "tcp"
$env:CHESSCHAMPION_ONLINE_HOST = "127.0.0.1"
$env:CHESSCHAMPION_ONLINE_PORT = "8765"
.venv\Scripts\python.exe main.py
```

In-game:

- Choose Online mode and Host.
- Capture the invite code shown in HUD.
- Confirm transport indicator shows tcp://127.0.0.1:8765.

## 3) Start Guest Client

In terminal C:

```powershell
$env:CHESSCHAMPION_ONLINE_TRANSPORT = "tcp"
$env:CHESSCHAMPION_ONLINE_HOST = "127.0.0.1"
$env:CHESSCHAMPION_ONLINE_PORT = "8765"
.venv\Scripts\python.exe main.py
```

In-game:

- Choose Online mode and Join.
- Enter host invite code.
- Confirm both clients transition to active game.

## 4) Verify Authoritative Move Relay

- On host, play e2->e4.
- Verify guest board updates immediately.
- On guest, play e7->e5.
- Verify host board updates immediately.

## 5) Verify Reconnect

- Close host client window.
- Relaunch host client with same TCP env vars.
- Use reconnect flow from HUD/menu.
- Verify reconnect succeeds and board/clock state match guest view.

## 6) Optional Save/Load Parity Check in Online Session

- During online game, perform save.
- Load the save.
- Verify online metadata is preserved (transport label, IDs, reconnect details) and reconnect still works.

## Pass Criteria

- Host/join succeeds over TCP.
- Moves relay authoritatively across clients.
- Reconnect succeeds with correct state restoration.
- HUD shows transport and connection status.