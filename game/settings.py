"""Settings model and persistence utilities."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from game.paths import ensure_user_data_layout, get_settings_file


@dataclass
class AppSettings:
    """Runtime settings persisted in user data."""

    network_enabled: bool = False
    network_server_url: str = "ws://localhost:8765"
    network_heartbeat_interval_ms: int = 1000
    reconnect_timeout_seconds: int = 30
    debug_network_logging: bool = False


DEFAULT_SETTINGS = AppSettings()


def load_settings() -> AppSettings:
    """Load settings from disk or return defaults."""
    ensure_user_data_layout()
    settings_path = get_settings_file()

    if not settings_path.exists():
        return AppSettings()

    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return AppSettings()

    return _from_payload(payload)


def save_settings(settings: AppSettings) -> Path:
    """Persist settings to user data directory."""
    ensure_user_data_layout()
    settings_path = get_settings_file()
    settings_path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
    return settings_path


def _from_payload(payload: Any) -> AppSettings:
    if not isinstance(payload, dict):
        return AppSettings()

    def _safe_int(key: str, default_value: int) -> int:
        try:
            return int(payload.get(key, default_value))
        except (TypeError, ValueError):
            return default_value

    return AppSettings(
        network_enabled=bool(payload.get("network_enabled", DEFAULT_SETTINGS.network_enabled)),
        network_server_url=str(payload.get("network_server_url", DEFAULT_SETTINGS.network_server_url)),
        network_heartbeat_interval_ms=max(
            250, _safe_int("network_heartbeat_interval_ms", DEFAULT_SETTINGS.network_heartbeat_interval_ms)
        ),
        reconnect_timeout_seconds=max(
            5, _safe_int("reconnect_timeout_seconds", DEFAULT_SETTINGS.reconnect_timeout_seconds)
        ),
        debug_network_logging=bool(payload.get("debug_network_logging", DEFAULT_SETTINGS.debug_network_logging)),
    )
