"""File-system storage utilities for save files and save index (SL-01 foundation)."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

from game.save_load.schema import SCHEMA_VERSION, ValidationResult, validate_payload

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAVE_GAMES_DIR = PROJECT_ROOT / "saved_games"
INDEX_FILE = SAVE_GAMES_DIR / "index.json"

INDEX_REQUIRED_FIELDS = (
    "save_id",
    "file_name",
    "source",
    "created_at_utc",
    "updated_at_utc",
)


def ensure_save_directory() -> Path:
    """Ensure saved_games directory and index file exist."""
    SAVE_GAMES_DIR.mkdir(parents=True, exist_ok=True)

    if not INDEX_FILE.exists():
        INDEX_FILE.write_text(
            json.dumps({"schema_version": SCHEMA_VERSION, "saves": []}, indent=2),
            encoding="utf-8",
        )

    return SAVE_GAMES_DIR


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON file as a dictionary."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON payload with stable formatting."""
    if "schema_version" not in payload:
        payload = {"schema_version": SCHEMA_VERSION, **payload}

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def validate_save_payload(payload: dict[str, Any]) -> ValidationResult:
    """Validate payload before persistence or load."""
    return validate_payload(payload)


def save_payload(payload: dict[str, Any], file_name: str | None = None) -> dict[str, Any]:
    """Persist a save payload and update index with summary metadata."""
    ensure_save_directory()

    validation_result = validate_save_payload(payload)
    if not validation_result.valid:
        details = "; ".join(f"{err.path}: {err.message}" for err in validation_result.errors)
        raise ValueError(f"Cannot save invalid payload: {details}")

    save_id = str(payload["save_id"])
    source = str(payload.get("source", "manual"))
    if source not in ("manual", "autosave"):
        source = "manual"

    resolved_file_name = file_name or f"{save_id}.json"
    save_path = SAVE_GAMES_DIR / resolved_file_name

    write_json(save_path, payload)

    summary = _build_summary(payload, resolved_file_name, source)
    index_data = _load_index()
    index_saves = [
        entry
        for entry in index_data["saves"]
        if not (
            entry.get("save_id") == summary["save_id"]
            or entry.get("file_name") == summary["file_name"]
        )
    ]
    index_saves.append(summary)
    index_data["saves"] = sorted(index_saves, key=lambda e: e.get("updated_at_utc", ""), reverse=True)
    _write_index(index_data)

    return summary


def load_payload(file_name: str) -> dict[str, Any]:
    """Load and validate one save payload by file name."""
    ensure_save_directory()

    save_path = SAVE_GAMES_DIR / file_name
    if not save_path.exists():
        raise FileNotFoundError(f"Save file does not exist: {file_name}")

    payload = read_json(save_path)
    validation_result = validate_save_payload(payload)
    if not validation_result.valid:
        details = "; ".join(f"{err.path}: {err.message}" for err in validation_result.errors)
        raise ValueError(f"Save file '{file_name}' is invalid: {details}")

    return payload


def list_saves(include_warnings: bool = False) -> list[dict[str, Any]] | tuple[list[dict[str, Any]], list[str]]:
    """List save summaries from index; skip malformed or missing entries with warnings."""
    ensure_save_directory()

    index_data = _load_index()
    warnings_list: list[str] = []
    valid_entries: list[dict[str, Any]] = []
    index_changed = False

    for entry in index_data.get("saves", []):
        reason = _validate_index_entry(entry)
        if reason:
            message = f"Skipping corrupt index entry: {reason}"
            warnings.warn(message)
            warnings_list.append(message)
            index_changed = True
            continue

        file_name = str(entry["file_name"])
        save_path = SAVE_GAMES_DIR / file_name
        if not save_path.exists():
            message = f"Skipping stale index entry; file missing: {file_name}"
            warnings.warn(message)
            warnings_list.append(message)
            index_changed = True
            continue

        valid_entries.append(entry)

    if index_changed:
        index_data["saves"] = sorted(
            valid_entries,
            key=lambda e: e.get("updated_at_utc", ""),
            reverse=True,
        )
        _write_index(index_data)

    if include_warnings:
        return valid_entries, warnings_list
    return valid_entries


def delete_save(file_name: str) -> bool:
    """Delete a save file and remove its entry from index."""
    ensure_save_directory()

    save_path = SAVE_GAMES_DIR / file_name
    file_existed = save_path.exists()
    if file_existed:
        save_path.unlink()

    index_data = _load_index()
    before_count = len(index_data.get("saves", []))
    index_data["saves"] = [
        entry for entry in index_data.get("saves", []) if entry.get("file_name") != file_name
    ]
    after_count = len(index_data["saves"])
    if before_count != after_count:
        _write_index(index_data)

    return file_existed or (before_count != after_count)


def _build_summary(payload: dict[str, Any], file_name: str, source: str) -> dict[str, Any]:
    session = payload.get("session", {})
    players = session.get("players", {})
    ai = session.get("ai", {}) if isinstance(session.get("ai", {}), dict) else {}
    position = payload.get("position", {})

    return {
        "save_id": payload["save_id"],
        "file_name": file_name,
        "source": source,
        "created_at_utc": payload.get("created_at_utc"),
        "updated_at_utc": payload.get("updated_at_utc"),
        "mode": session.get("mode", "pvp"),
        "white": players.get("white", "White"),
        "black": players.get("black", "Black"),
        "ai_enabled": bool(ai.get("enabled", False)),
        "game_status": position.get("game_status", "ACTIVE"),
        "move_count": len(payload.get("history", {}).get("moves", [])),
    }


def _load_index() -> dict[str, Any]:
    ensure_save_directory()

    try:
        data = read_json(INDEX_FILE)
    except Exception:
        message = "Corrupt save index detected; recreating a clean index."
        warnings.warn(message)
        data = {"schema_version": SCHEMA_VERSION, "saves": []}
        _write_index(data)
        return data

    if not isinstance(data, dict) or not isinstance(data.get("saves"), list):
        message = "Malformed save index structure detected; recreating a clean index."
        warnings.warn(message)
        data = {"schema_version": SCHEMA_VERSION, "saves": []}
        _write_index(data)
        return data

    if "schema_version" not in data:
        data["schema_version"] = SCHEMA_VERSION

    return data


def _write_index(index_data: dict[str, Any]) -> None:
    if "schema_version" not in index_data:
        index_data["schema_version"] = SCHEMA_VERSION
    if "saves" not in index_data or not isinstance(index_data["saves"], list):
        index_data["saves"] = []
    write_json(INDEX_FILE, index_data)


def _validate_index_entry(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return "entry is not an object"

    for field_name in INDEX_REQUIRED_FIELDS:
        if field_name not in entry:
            return f"missing '{field_name}'"

    if not isinstance(entry.get("file_name"), str) or not entry.get("file_name"):
        return "file_name must be a non-empty string"

    return None


# Bootstrap persistence directory at module import so external callers can rely on it.
ensure_save_directory()
