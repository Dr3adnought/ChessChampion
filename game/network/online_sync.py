"""Helpers for authoritative online move/clock synchronization."""

from __future__ import annotations

from typing import Any

from game.champion_chess import ChessGame
from game.state_fingerprint import fingerprint_game_state
from game.types import Color, PieceType, Position


def build_move_intent_payload(
    game: ChessGame,
    *,
    from_pos: Position,
    to_pos: Position,
    promotion_piece: PieceType | None = None,
) -> dict[str, Any]:
    """Build move_intent payload using current authoritative expectations."""
    return {
        "move": {
            "from": from_pos.to_algebraic(),
            "to": to_pos.to_algebraic(),
            "promotion": promotion_piece.value if promotion_piece else None,
        },
        "expected_halfmove": len(game.game_state.move_history),
        "expected_position_hash": fingerprint_game_state(game),
    }


def apply_authoritative_move(game: ChessGame, move_payload: dict[str, Any]) -> bool:
    """Apply one authoritative move payload to local game state."""
    try:
        from_pos = Position.from_algebraic(str(move_payload["from"]))
        to_pos = Position.from_algebraic(str(move_payload["to"]))
    except Exception:
        return False

    promotion_piece = None
    promotion_value = move_payload.get("promotion")
    if isinstance(promotion_value, str):
        try:
            promotion_piece = PieceType(promotion_value)
        except ValueError:
            return False

    legal_moves = game.game_state.get_legal_moves_for_position(from_pos)
    for move in legal_moves:
        if move.to_pos != to_pos:
            continue
        if move.promotion_piece is None and promotion_piece is None:
            if game.game_state.make_move(move):
                game.last_move = (move.from_pos, move.to_pos)
                return True
        elif move.promotion_piece == promotion_piece:
            if game.game_state.make_move(move):
                game.last_move = (move.from_pos, move.to_pos)
                return True

    return False


def apply_authoritative_clock(game: ChessGame, clock_payload: dict[str, Any]) -> None:
    """Apply authoritative clock snapshot from network payload."""
    if not isinstance(clock_payload, dict):
        return

    if "white_ms" in clock_payload:
        game.timer.white_time = float(clock_payload.get("white_ms", 0)) / 1000.0
    if "black_ms" in clock_payload:
        game.timer.black_time = float(clock_payload.get("black_ms", 0)) / 1000.0

    active = clock_payload.get("active")
    if active in ("white", "black"):
        game.timer.current_player = Color(active)
        game.timer.is_paused = False
    else:
        game.timer.current_player = None
        game.timer.is_paused = True
