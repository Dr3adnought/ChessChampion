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
.venv\Scripts\python.exe main.py
```

In-game:

- Choose Online mode and Host.
- Choose transport/host/port in the Online setup screen (defaults are persisted).
- Capture the invite code shown in HUD.
- Confirm transport indicator shows tcp://127.0.0.1:8765.

## 3) Start Guest Client

In terminal C:

```powershell
.venv\Scripts\python.exe main.py
```

In-game:

- Choose Online mode and Join.
- Choose the same transport/host/port as host.
- Enter host invite code.
- Confirm both clients transition to active game.

## 4) Verify Authoritative Move Relay

- On host, play e2->e4.
- Verify guest board updates immediately.
- On guest, play e7->e5.
- Verify host board updates immediately.

## 5) Verify Reconnect

- Close host client window.
- Relaunch host client and confirm saved transport/host/port values are pre-filled.
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

## Packaged Two-Machine Execution

For Checkpoint R3 with packaged artifacts only, use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\prepare_lan_test_bundle.ps1
```

Then follow the worksheet in `docs/r3_two_machine_lan_acceptance.md`.