"""Schema and validation helpers for save files (SL-02)."""

from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = "1.0.0"

REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "save_id",
    "created_at_utc",
    "updated_at_utc",
    "source",
    "app",
    "session",
    "clock",
    "position",
    "captures",
    "history",
    "artifacts",
)


@dataclass(frozen=True)
class ValidationError:
    """Represents one validation issue at a specific path."""

    path: str
    message: str


@dataclass
class ValidationResult:
    """Validation result containing errors and warnings."""

    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, path: str, message: str) -> None:
        self.errors.append(ValidationError(path=path, message=message))

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


# Note: Validation is intentionally lightweight in SL-02. It checks required shape
# and key value types to prevent malformed payloads from being persisted or loaded.
def validate_payload(payload: Any) -> ValidationResult:
    """Validate top-level and key nested fields for save payloads."""

    result = ValidationResult()

    if not isinstance(payload, dict):
        result.add_error("$", "Payload must be a dictionary.")
        return result

    for field_name in REQUIRED_TOP_LEVEL_FIELDS:
        if field_name not in payload:
            result.add_error("$", f"Missing required field: '{field_name}'.")

    if result.errors:
        return result

    _validate_schema_version(payload, result)
    _validate_session(payload.get("session"), result)
    _validate_clock(payload.get("clock"), result)
    _validate_position(payload.get("position"), result)
    _validate_captures(payload.get("captures"), result)
    _validate_history(payload.get("history"), result)

    return result


def _validate_schema_version(payload: dict[str, Any], result: ValidationResult) -> None:
    version = payload.get("schema_version")
    if not isinstance(version, str) or not version.strip():
        result.add_error("schema_version", "schema_version must be a non-empty string.")
        return

    if version != SCHEMA_VERSION:
        result.add_warning(
            f"schema_version '{version}' differs from supported '{SCHEMA_VERSION}'."
        )


def _validate_session(session: Any, result: ValidationResult) -> None:
    if not isinstance(session, dict):
        result.add_error("session", "session must be an object.")
        return

    mode = session.get("mode")
    if not isinstance(mode, str) or mode not in ("pvp", "pvai"):
        result.add_error("session.mode", "session.mode must be 'pvp' or 'pvai'.")

    players = session.get("players")
    if not isinstance(players, dict):
        result.add_error("session.players", "session.players must be an object.")
    else:
        for side in ("white", "black"):
            name = players.get(side)
            if not isinstance(name, str) or not name.strip():
                result.add_error(
                    f"session.players.{side}",
                    f"session.players.{side} must be a non-empty string.",
                )

    ai = session.get("ai")
    if ai is not None and not isinstance(ai, dict):
        result.add_error("session.ai", "session.ai must be an object when present.")


def _validate_clock(clock: Any, result: ValidationResult) -> None:
    if not isinstance(clock, dict):
        result.add_error("clock", "clock must be an object.")
        return

    _require_type(clock, "is_timed", bool, result, "clock")
    _require_number(clock, "base_seconds", result, "clock")
    _require_number(clock, "increment_seconds", result, "clock")
    _require_number(clock, "white_remaining_seconds", result, "clock")
    _require_number(clock, "black_remaining_seconds", result, "clock")

    current_player = clock.get("current_player")
    if current_player is not None and current_player not in ("white", "black"):
        result.add_error(
            "clock.current_player",
            "clock.current_player must be 'white', 'black', or null.",
        )

    _require_type(clock, "is_paused", bool, result, "clock")


def _validate_position(position: Any, result: ValidationResult) -> None:
    if not isinstance(position, dict):
        result.add_error("position", "position must be an object.")
        return

    board = position.get("board")
    if not isinstance(board, list) or len(board) != 8:
        result.add_error("position.board", "position.board must be an 8-row array.")
    else:
        for row_index, row in enumerate(board):
            if not isinstance(row, list) or len(row) != 8:
                result.add_error(
                    f"position.board[{row_index}]",
                    "Each board row must be an 8-item array.",
                )
                continue

            for col_index, cell in enumerate(row):
                if cell is not None and not isinstance(cell, str):
                    result.add_error(
                        f"position.board[{row_index}][{col_index}]",
                        "Board cells must be piece strings or null.",
                    )

    turn = position.get("current_turn")
    if turn not in ("white", "black"):
        result.add_error("position.current_turn", "position.current_turn must be 'white' or 'black'.")

    _require_type(position, "game_status", str, result, "position")
    _require_number(position, "half_move_clock", result, "position", integer_only=True)
    _require_number(position, "full_move_number", result, "position", integer_only=True)
    _require_type(position, "castling_rights", str, result, "position")

    en_passant_target = position.get("en_passant_target")
    if en_passant_target is not None and not isinstance(en_passant_target, str):
        result.add_error(
            "position.en_passant_target",
            "position.en_passant_target must be a string or null.",
        )


def _validate_captures(captures: Any, result: ValidationResult) -> None:
    if not isinstance(captures, dict):
        result.add_error("captures", "captures must be an object.")
        return

    for field_name in ("captured_by_white", "captured_by_black"):
        values = captures.get(field_name)
        if not isinstance(values, list):
            result.add_error(f"captures.{field_name}", f"captures.{field_name} must be an array.")
            continue

        for index, value in enumerate(values):
            if not isinstance(value, str):
                result.add_error(
                    f"captures.{field_name}[{index}]",
                    "Captured piece entries must be strings.",
                )


def _validate_history(history: Any, result: ValidationResult) -> None:
    if not isinstance(history, dict):
        result.add_error("history", "history must be an object.")
        return

    for field_name in ("moves", "redo_moves"):
        values = history.get(field_name)
        if not isinstance(values, list):
            result.add_error(f"history.{field_name}", f"history.{field_name} must be an array.")


def _require_type(
    source: dict[str, Any],
    field_name: str,
    expected_type: type,
    result: ValidationResult,
    prefix: str,
) -> None:
    value = source.get(field_name)
    if not isinstance(value, expected_type):
        type_name = expected_type.__name__
        result.add_error(f"{prefix}.{field_name}", f"{prefix}.{field_name} must be a {type_name}.")


def _require_number(
    source: dict[str, Any],
    field_name: str,
    result: ValidationResult,
    prefix: str,
    integer_only: bool = False,
) -> None:
    value = source.get(field_name)
    if not isinstance(value, (int, float)):
        result.add_error(f"{prefix}.{field_name}", f"{prefix}.{field_name} must be numeric.")
        return

    if integer_only and not isinstance(value, int):
        result.add_error(f"{prefix}.{field_name}", f"{prefix}.{field_name} must be an integer.")
