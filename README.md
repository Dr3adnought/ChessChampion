# ChessChampion

### Repository Overview

`ChessChampion` is a Python-based chess game featuring:
- Checkmate and stalemate detection
- Castling and en passant moves
- A medium-difficulty AI opponent

This repository contains the following structure:
- `game`: Main chess logic.
- `ai`: AI decision-making logic.
- `assets`: Graphical assets for chess pieces.
- `main.py`: Application entry point.
- `.idea`: IDE-specific configuration files.

### Chat Notes and Recommendations

This section documents suggestions during a code review of the repository:

1. Refactor `ChessGame` class into smaller components: `Board`, `RuleEngine`, and `GameEngine`.
2. Centralize move validation into a utility module.
3. Improve robustness of asset handling to ensure image presence before rendering.
   - Validate paths during initialization.
4. Use Enums for chess pieces and moves instead of raw strings.
5. Add unit tests for critical components (`ai` logic and game rules).

### Notes
This README reflects insights from analyzing relevant files, like `main.py` and `game/champion_chess.py`. Advanced features, such as AI logic, were emphasized during the discussion.