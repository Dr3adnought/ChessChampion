"""Serializer helpers for runtime <-> payload conversion."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Optional

from game.board import Board
from game.champion_chess import ChessGame
from game.game_state import GameState
from game.pieces import Piece, create_piece
from game.types import CastlingRights, Color, GameStatus, Move, MoveType, PieceType, Position
from game.save_load.schema import SCHEMA_VERSION, validate_payload


def serialize_game(
    game: ChessGame,
    *,
    save_id: str,
    source: str = "manual",
    session_meta: Optional[dict[str, Any]] = None,
    app_meta: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Serialize runtime game state to a save payload (SL-03)."""
    now = _utc_now_iso()
    session = _build_session_payload(session_meta)
    app = app_meta or {"name": "ChessChampion", "build": "local"}

    payload = {
        "schema_version": SCHEMA_VERSION,
        "save_id": save_id,
        "created_at_utc": now,
        "updated_at_utc": now,
        "source": source,
        "app": app,
        "session": session,
        "clock": _serialize_clock(game),
        "position": _serialize_position(game),
        "captures": {
            "captured_by_white": [p.value for p in game.game_state.captured_by_white],
            "captured_by_black": [p.value for p in game.game_state.captured_by_black],
        },
        "history": {
            "moves": [_serialize_move(move) for move in game.game_state.move_history],
            "redo_moves": [_serialize_move(move) for move in game.game_state.redo_stack],
        },
        "artifacts": {},
    }

    validation_result = validate_payload(payload)
    if not validation_result.valid:
        errors = "; ".join(f"{e.path}: {e.message}" for e in validation_result.errors)
        raise ValueError(f"Serialized payload failed validation: {errors}")

    return payload


def deserialize_game(payload: dict[str, Any]) -> dict[str, Any]:
    """Deserialize save payload back to runtime-compatible state (SL-04)."""
    validation_result = validate_payload(payload)
    if not validation_result.valid:
        errors = "; ".join(f"{e.path}: {e.message}" for e in validation_result.errors)
        raise ValueError(f"Cannot deserialize invalid payload: {errors}")

    position = payload["position"]
    board = Board.from_string_board(position["board"])
    board.castling_rights = _castling_from_string(position.get("castling_rights", "-"))
    board.en_passant_target = _algebraic_to_pos(position.get("en_passant_target"))

    game_state = GameState(board)
    game_state.current_turn = Color(position["current_turn"])
    game_state.game_status = _game_status_from_name(position.get("game_status", "ACTIVE"))
    game_state.half_move_clock = int(position["half_move_clock"])
    game_state.full_move_number = int(position["full_move_number"])
    game_state.selected_position = _algebraic_to_pos(position.get("selected_position"))

    captures = payload["captures"]
    game_state.captured_by_white = [PieceType(name) for name in captures["captured_by_white"]]
    game_state.captured_by_black = [PieceType(name) for name in captures["captured_by_black"]]

    history = payload["history"]
    game_state.move_history = [_deserialize_move(move_data) for move_data in history["moves"]]
    game_state.redo_stack = [_deserialize_move(move_data) for move_data in history["redo_moves"]]

    game = ChessGame(0, 0)
    game.board = board
    game.game_state = game_state
    game.last_move = _deserialize_last_move(position.get("last_move"))
    _restore_clock(game, payload["clock"])

    return {
        "game": game,
        "session_meta": payload.get("session", {}),
        "save_id": payload.get("save_id"),
        "source": payload.get("source"),
        "created_at_utc": payload.get("created_at_utc"),
        "updated_at_utc": payload.get("updated_at_utc"),
    }


def _build_session_payload(session_meta: Optional[dict[str, Any]]) -> dict[str, Any]:
    session_meta = session_meta or {}

    mode = session_meta.get("mode", "pvp")
    if mode not in ("pvp", "pvai"):
        mode = "pvp"

    players_meta = session_meta.get("players", {})
    white_name = players_meta.get("white", "White")
    black_name = players_meta.get("black", "Black")

    ai_payload: dict[str, Any] = {
        "enabled": mode == "pvai",
        "color": session_meta.get("ai", {}).get("color", "black"),
        "difficulty": session_meta.get("ai", {}).get("difficulty", "medium"),
        "depth": session_meta.get("ai", {}).get("depth", 2),
    }

    return {
        "mode": mode,
        "players": {
            "white": str(white_name),
            "black": str(black_name),
        },
        "ai": ai_payload,
    }


def _serialize_clock(game: ChessGame) -> dict[str, Any]:
    timer = game.timer
    return {
        "is_timed": timer.is_timed,
        "base_seconds": timer.base_time,
        "increment_seconds": timer.increment,
        "white_remaining_seconds": timer.white_time,
        "black_remaining_seconds": timer.black_time,
        "current_player": timer.current_player.value if timer.current_player else None,
        "is_paused": timer.is_paused,
    }


def _serialize_position(game: ChessGame) -> dict[str, Any]:
    game_state = game.game_state

    return {
        "board": game.board.to_string_board(),
        "current_turn": game_state.current_turn.value,
        "game_status": game_state.game_status.name,
        "half_move_clock": game_state.half_move_clock,
        "full_move_number": game_state.full_move_number,
        "castling_rights": str(game.board.castling_rights),
        "en_passant_target": _pos_to_algebraic(game.board.en_passant_target),
        "selected_position": _pos_to_algebraic(game_state.selected_position),
        "last_move": _serialize_last_move(game.last_move),
    }


def _serialize_last_move(last_move: Optional[tuple[Position, Position]]) -> Optional[dict[str, str]]:
    if not last_move:
        return None

    from_pos, to_pos = last_move
    return {
        "from": from_pos.to_algebraic(),
        "to": to_pos.to_algebraic(),
    }


def _serialize_move(move: Move) -> dict[str, Any]:
    return {
        "from": move.from_pos.to_algebraic(),
        "to": move.to_pos.to_algebraic(),
        "move_type": move.move_type.name,
        "promotion_piece": _piece_type_name(move.promotion_piece),
        "captured_piece": _serialize_piece(move.captured_piece),
        "previous_castling_rights": str(move.previous_castling_rights)
        if move.previous_castling_rights
        else None,
        "previous_en_passant": _pos_to_algebraic(move.previous_en_passant),
        "previous_half_move_clock": move.previous_half_move_clock,
    }


def _deserialize_move(move_data: dict[str, Any]) -> Move:
    from_pos = Position.from_algebraic(move_data["from"])
    to_pos = Position.from_algebraic(move_data["to"])

    move_type_name = move_data.get("move_type", "NORMAL")
    move_type = MoveType[move_type_name] if move_type_name in MoveType.__members__ else MoveType.NORMAL

    promotion_piece = None
    if move_data.get("promotion_piece"):
        promotion_piece = PieceType(move_data["promotion_piece"])

    captured_piece = _deserialize_piece(move_data.get("captured_piece"))

    move = Move(
        from_pos=from_pos,
        to_pos=to_pos,
        move_type=move_type,
        promotion_piece=promotion_piece,
        captured_piece=captured_piece,
    )

    previous_castling_rights = move_data.get("previous_castling_rights")
    move.previous_castling_rights = (
        _castling_from_string(previous_castling_rights) if previous_castling_rights is not None else None
    )
    move.previous_en_passant = _algebraic_to_pos(move_data.get("previous_en_passant"))
    move.previous_half_move_clock = int(move_data.get("previous_half_move_clock", 0))

    return move


def _serialize_piece(piece: Optional[Piece]) -> Optional[dict[str, str]]:
    if piece is None:
        return None

    return {
        "color": piece.color.value,
        "piece_type": piece.piece_type.value,
    }


def _deserialize_piece(piece_data: Optional[dict[str, str]]) -> Optional[Piece]:
    if piece_data is None:
        return None

    color = Color(piece_data["color"])
    piece_type = PieceType(piece_data["piece_type"])
    return create_piece(color, piece_type)


def _piece_type_name(piece_type: Optional[PieceType]) -> Optional[str]:
    if piece_type is None:
        return None
    return piece_type.value


def _pos_to_algebraic(position: Optional[Position]) -> Optional[str]:
    if position is None:
        return None
    return position.to_algebraic()


def _algebraic_to_pos(notation: Optional[str]) -> Optional[Position]:
    if notation is None:
        return None
    return Position.from_algebraic(notation)


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


def _game_status_from_name(name: str) -> GameStatus:
    if name in GameStatus.__members__:
        return GameStatus[name]
    return GameStatus.ACTIVE


def _deserialize_last_move(last_move: Optional[dict[str, str]]) -> Optional[tuple[Position, Position]]:
    if not last_move:
        return None

    return (
        Position.from_algebraic(last_move["from"]),
        Position.from_algebraic(last_move["to"]),
    )


def _restore_clock(game: ChessGame, clock: dict[str, Any]) -> None:
    timer = game.timer
    timer.base_time = int(clock["base_seconds"])
    timer.increment = int(clock["increment_seconds"])
    timer.is_timed = bool(clock["is_timed"])
    timer.white_time = float(clock["white_remaining_seconds"])
    timer.black_time = float(clock["black_remaining_seconds"])

    current_player = clock.get("current_player")
    timer.current_player = Color(current_player) if current_player else None
    timer.is_paused = bool(clock["is_paused"])

    if timer.is_timed and not timer.is_paused and timer.current_player is not None:
        timer.turn_start_time = time.time()
    else:
        timer.turn_start_time = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
