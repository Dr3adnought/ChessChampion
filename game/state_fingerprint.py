"""Deterministic state fingerprint helpers for desync detection."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from game.board import Board
from game.champion_chess import ChessGame


FINGERPRINT_ALGORITHM = "sha256"


def fingerprint_game_state(game: ChessGame) -> str:
    """Compute a deterministic hash for relevant game state."""
    payload = {
        "board": _normalize_board(game.board),
        "current_turn": game.game_state.current_turn.value,
        "castling_rights": str(game.board.castling_rights),
        "en_passant_target": game.board.en_passant_target.to_algebraic() if game.board.en_passant_target else None,
        "half_move_clock": game.game_state.half_move_clock,
        "full_move_number": game.game_state.full_move_number,
    }
    return _hash_payload(payload)


def fingerprint_board_state(board: Board) -> str:
    """Compute a deterministic hash from board-only data."""
    payload = {
        "board": _normalize_board(board),
        "castling_rights": str(board.castling_rights),
        "en_passant_target": board.en_passant_target.to_algebraic() if board.en_passant_target else None,
    }
    return _hash_payload(payload)


def _normalize_board(board: Board) -> list[list[str | None]]:
    return board.to_string_board()


def _hash_payload(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.new(FINGERPRINT_ALGORITHM)
    digest.update(canonical.encode("utf-8"))
    return f"{FINGERPRINT_ALGORITHM}:{digest.hexdigest()}"
