"""PGN helpers for export/import workflow.

SL-07 implements PGN export and sidecar writing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from game.board import Board
from game.champion_chess import ChessGame
from game.game_state import GameState
from game.types import Color, GameStatus, Move


def export_pgn(
    game: ChessGame,
    *,
    session_meta: Optional[dict[str, Any]] = None,
    event: str = "ChessChampion Game",
    site: str = "Local",
    date_override: Optional[str] = None,
) -> str:
    """Create PGN text from current game state."""
    session_meta = session_meta or {}
    players = session_meta.get("players", {}) if isinstance(session_meta.get("players", {}), dict) else {}

    white_name = str(players.get("white", "White"))
    black_name = str(players.get("black", "Black"))
    result = _resolve_result(game)
    date_text = date_override or datetime.now(timezone.utc).strftime("%Y.%m.%d")

    tags = [
        f'[Event "{event}"]',
        f'[Site "{site}"]',
        f'[Date "{date_text}"]',
        f'[White "{white_name}"]',
        f'[Black "{black_name}"]',
        f'[Result "{result}"]',
    ]

    move_text = _build_move_text(game.game_state, result)
    return "\n".join(tags) + "\n\n" + move_text


def write_pgn(text: str, path: Path) -> None:
    """Write PGN text to disk."""
    path.write_text(text, encoding="utf-8")


def _resolve_result(game: ChessGame) -> str:
    status = game.game_state.game_status
    if status == GameStatus.CHECKMATE:
        winner = game.game_state.get_winner()
        return "1-0" if winner == Color.WHITE else "0-1"
    if status in (GameStatus.STALEMATE, GameStatus.DRAW):
        return "1/2-1/2"
    return "*"


def _build_move_text(game_state: GameState, result: str) -> str:
    tokens = _build_notation_tokens(game_state)
    tokens.append(result)
    return " ".join(tokens)


def _build_notation_tokens(game_state: GameState) -> list[str]:
    # Replay from initial position to produce per-move notation in sequence.
    replay_state = GameState(Board.from_string_board(_initial_board_strings()))
    tokens: list[str] = []

    for index, original_move in enumerate(game_state.move_history):
        if index % 2 == 0:
            tokens.append(f"{index // 2 + 1}.")

        notation = _replay_move_notation(replay_state, original_move)
        tokens.append(notation)

    return tokens


def _replay_move_notation(replay_state: GameState, original_move: Move) -> str:
    piece = replay_state.board.get_piece(original_move.from_pos)
    piece_type = piece.piece_type if piece else None

    replay_move = _find_matching_move(replay_state, original_move)
    if replay_move is None:
        return _fallback_coordinate_notation(original_move)

    if not replay_state.make_move(replay_move):
        return _fallback_coordinate_notation(original_move)

    if piece_type is None:
        return _fallback_coordinate_notation(original_move)

    return replay_state.get_move_notation(replay_move, piece_type)


def _find_matching_move(replay_state: GameState, original_move: Move) -> Optional[Move]:
    legal_moves = replay_state.get_legal_moves_for_position(original_move.from_pos)

    for candidate in legal_moves:
        if candidate.to_pos != original_move.to_pos:
            continue
        if candidate.move_type != original_move.move_type:
            continue
        if candidate.promotion_piece != original_move.promotion_piece:
            continue
        return candidate

    for candidate in legal_moves:
        if candidate.to_pos == original_move.to_pos:
            return candidate

    return None


def _fallback_coordinate_notation(move: Move) -> str:
    notation = f"{move.from_pos.to_algebraic()}{move.to_pos.to_algebraic()}"
    if move.promotion_piece is not None:
        notation += move.promotion_piece.value[0]
    return notation


def _initial_board_strings() -> list[list[Optional[str]]]:
    # Maintain a fixed chess start position for PGN replay reconstruction.
    return [
        ["b_rook", "b_knight", "b_bishop", "b_queen", "b_king", "b_bishop", "b_knight", "b_rook"],
        ["b_pawn", "b_pawn", "b_pawn", "b_pawn", "b_pawn", "b_pawn", "b_pawn", "b_pawn"],
        [None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None],
        ["w_pawn", "w_pawn", "w_pawn", "w_pawn", "w_pawn", "w_pawn", "w_pawn", "w_pawn"],
        ["w_rook", "w_knight", "w_bishop", "w_queen", "w_king", "w_bishop", "w_knight", "w_rook"],
    ]
