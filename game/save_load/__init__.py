"""Save/load package for ChessChampion.

This package groups persistence helpers for JSON save files and PGN export.
"""

from game.save_load.pgn import export_pgn, write_pgn
from game.save_load.schema import SCHEMA_VERSION, ValidationError, ValidationResult, validate_payload
from game.save_load.serializer import deserialize_game, serialize_game
from game.save_load.service import delete_save, list_saves, load_game, save_game
from game.save_load.store import (
    SAVE_GAMES_DIR,
    ensure_save_directory,
    load_payload,
    save_payload,
)

__all__ = [
    "SCHEMA_VERSION",
    "SAVE_GAMES_DIR",
    "ValidationError",
    "ValidationResult",
    "delete_save",
    "deserialize_game",
    "ensure_save_directory",
    "export_pgn",
    "list_saves",
    "load_game",
    "load_payload",
    "save_game",
    "save_payload",
    "serialize_game",
    "validate_payload",
    "write_pgn",
]
