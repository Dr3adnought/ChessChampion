# R3 Two-Machine LAN Acceptance Worksheet

Use this worksheet when running Checkpoint R3 on two different computers with packaged artifacts only.

## Preparation

1. Build and prepare bundle:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\prepare_lan_test_bundle.ps1
```

2. Copy `dist/LAN-Test-Pack/Guest-PC` to the second machine.

3. On host machine, launch:

- `dist/LAN-Test-Pack/Host-PC/Start-Server.bat`
- `dist/LAN-Test-Pack/Host-PC/Start-Client.bat`

4. On guest machine, launch:

- `Guest-PC/Start-Client.bat`

## Test Record

- Date:
- Host machine:
- Guest machine:
- Host LAN IP:
- Build commit:

## Steps and Results

1. Host creates online session over TCP: PASS/FAIL
2. Guest joins host session using invite code: PASS/FAIL
3. Host move appears on guest board: PASS/FAIL
4. Guest move appears on host board: PASS/FAIL
5. Complete full game to result screen: PASS/FAIL
6. Close host client and reconnect mid-game: PASS/FAIL
7. Reconnected host state matches guest state: PASS/FAIL

## Notes

- Issues observed:
- Workarounds used:
- Follow-up fixes required:

## Exit Criteria

Mark R3 complete only when all seven step results are PASS.