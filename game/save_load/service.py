"""Facade service for save/load operations.

High-level orchestration for save/load features (SL-06).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from game.champion_chess import ChessGame
from game.save_load.pgn import export_pgn, write_pgn
from game.save_load.serializer import deserialize_game, serialize_game
from game.save_load.store import (
    SAVE_GAMES_DIR,
    delete_save as delete_save_file,
    ensure_save_directory,
    list_saves as list_save_entries,
    load_payload,
    save_payload,
)


def save_game(
    game: ChessGame,
    *,
    source: str = "manual",
    session_meta: dict[str, Any] | None = None,
    app_meta: dict[str, str] | None = None,
    save_id: str | None = None,
    file_name: str | None = None,
) -> dict[str, Any]:
    """Save current game state and return a structured result."""
    ensure_save_directory()

    try:
        resolved_save_id = save_id or _generate_save_id(source)
        resolved_file_name = file_name or f"{resolved_save_id}.json"
        pgn_file_name = Path(resolved_file_name).with_suffix(".pgn").name

        payload = serialize_game(
            game,
            save_id=resolved_save_id,
            source=source,
            session_meta=session_meta,
            app_meta=app_meta,
        )
        payload.setdefault("artifacts", {})["pgn_file"] = pgn_file_name

        summary = save_payload(payload, file_name=resolved_file_name)

        pgn_text = export_pgn(game, session_meta=session_meta)
        write_pgn(pgn_text, SAVE_GAMES_DIR / pgn_file_name)

        return {
            "success": True,
            "save_id": resolved_save_id,
            "file_name": summary.get("file_name"),
            "pgn_file": pgn_file_name,
            "summary": summary,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Save failed: {exc}",
        }


def load_game(file_name: str) -> dict[str, Any]:
    """Load game state from one saved file name with safe error reporting."""
    ensure_save_directory()

    try:
        payload = load_payload(file_name)
        loaded = deserialize_game(payload)
        return {
            "success": True,
            "file_name": file_name,
            "loaded": loaded,
            "game": loaded.get("game"),
            "session_meta": loaded.get("session_meta", {}),
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Load failed for '{file_name}': {exc}",
        }


def list_saves(include_warnings: bool = False) -> dict[str, Any]:
    """List saves through facade with optional warning details."""
    ensure_save_directory()

    try:
        if include_warnings:
            saves, warnings = list_save_entries(include_warnings=True)
            return {
                "success": True,
                "saves": saves,
                "warnings": warnings,
            }

        saves = list_save_entries(include_warnings=False)
        return {
            "success": True,
            "saves": saves,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"List saves failed: {exc}",
            "saves": [],
        }


def delete_save(file_name: str) -> dict[str, Any]:
    """Delete a save by file name with safe error reporting."""
    ensure_save_directory()

    try:
        pgn_file_name = None
        try:
            existing_payload = load_payload(file_name)
            artifacts = existing_payload.get("artifacts", {})
            if isinstance(artifacts, dict):
                pgn_file_name = artifacts.get("pgn_file")
        except Exception:
            # If payload cannot be read, still try deleting the JSON entry.
            pgn_file_name = None

        deleted = delete_save_file(file_name)

        pgn_deleted = False
        if isinstance(pgn_file_name, str) and pgn_file_name:
            pgn_path = SAVE_GAMES_DIR / pgn_file_name
            if pgn_path.exists():
                pgn_path.unlink()
                pgn_deleted = True

        return {
            "success": True,
            "file_name": file_name,
            "deleted": deleted,
            "pgn_deleted": pgn_deleted,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Delete failed for '{file_name}': {exc}",
        }


def _generate_save_id(source: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    normalized_source = source if source in ("manual", "autosave") else "manual"
    return f"{timestamp}_{normalized_source}"
