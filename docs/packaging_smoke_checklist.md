# Packaging Smoke Checklist (Windows)

Use this checklist after each distributable build.

## Build
- [ ] Build succeeds with no fatal errors.
- [ ] App launches from `dist/ChessChampion/ChessChampion.exe`.

## Startup
- [ ] Main menu renders correctly.
- [ ] Piece sprites load (no placeholders).
- [ ] No missing-file errors in startup logs.

## Core Gameplay
- [ ] New PvP game starts and accepts legal moves.
- [ ] New PvAI game starts and AI responds.
- [ ] Undo/Redo works (`Ctrl+Z` / `Ctrl+Y`).
- [ ] Promotion dialog appears and completes correctly.

## Time Controls
- [ ] Timed game starts with correct preset values.
- [ ] Clock switches active player after move.
- [ ] Increment applies after valid move.
- [ ] Timeout ends game correctly.

## Save/Load
- [ ] Manual save works from button and `Ctrl+S`.
- [ ] Load list opens with `Ctrl+L` and loads selected game.
- [ ] Autosave is written on quit/new-game/end-game transitions.

## User Data Layout
- [ ] Save files are created in user data directory, not install folder.
- [ ] `saved_games/` index updates after save/delete.
- [ ] App can relaunch and load prior saves.

## Release Readiness
- [ ] Version metadata is updated.
- [ ] Release notes summarize changes and known issues.
- [ ] Virus scan/signing steps completed (if applicable).
