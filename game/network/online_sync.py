"""Helpers for authoritative online move/clock synchronization."""

from __future__ import annotations

from typing import Any

from game.board import Board
from game.champion_chess import ChessGame
from game.move_validator import MoveValidator
from game.state_fingerprint import fingerprint_game_state
from game.types import CastlingRights
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


def apply_authoritative_state(game: ChessGame, state_payload: dict[str, Any]) -> bool:
    """Apply authoritative board/state snapshot to local runtime."""
    if not isinstance(state_payload, dict):
        return False

    board_payload = state_payload.get("board")
    if not isinstance(board_payload, list):
        return False

    try:
        board = Board.from_string_board(board_payload)
    except Exception:
        return False

    board.castling_rights = _castling_from_string(str(state_payload.get("castling_rights", "-")))

    en_passant = state_payload.get("en_passant_target")
    if isinstance(en_passant, str) and en_passant:
        try:
            board.en_passant_target = Position.from_algebraic(en_passant)
        except Exception:
            board.en_passant_target = None
    else:
        board.en_passant_target = None

    game.board = board
    game.game_state.board = board
    game.game_state.validator = MoveValidator(board)

    turn = state_payload.get("current_turn")
    if turn in ("white", "black"):
        game.game_state.current_turn = Color(turn)

    try:
        game.game_state.half_move_clock = int(state_payload.get("half_move_clock", game.game_state.half_move_clock))
        game.game_state.full_move_number = int(state_payload.get("full_move_number", game.game_state.full_move_number))
    except (TypeError, ValueError):
        return False

    last_move = state_payload.get("last_move")
    if isinstance(last_move, dict) and last_move.get("from") and last_move.get("to"):
        try:
            game.last_move = (
                Position.from_algebraic(str(last_move["from"])),
                Position.from_algebraic(str(last_move["to"])),
            )
        except Exception:
            game.last_move = None
    else:
        game.last_move = None

    game.game_state.selected_position = None
    game.game_state._update_game_status()
    return True


def _castling_from_string(castling: str) -> CastlingRights:
    if not castling or castling == "-":
        return CastlingRights(0)

    rights = 0
    if "K" in castling:
        rights |= CastlingRights.WHITE_KINGSIDE
    if "Q" in castling:
        rights |= CastlingRights.WHITE_QUEENSIDE
    if "k" in castling:
        rights |= CastlingRights.BLACK_KINGSIDE
    if "q" in castling:
        rights |= CastlingRights.BLACK_QUEENSIDE
    return CastlingRights(rights)
