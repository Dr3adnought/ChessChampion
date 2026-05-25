"""Path utilities for source and packaged runtime environments.

These helpers centralize path resolution so development runs and PyInstaller
builds use the same API for assets and writable user data.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "ChessChampion"


def get_project_root() -> Path:
    """Return repository root during source execution."""
    return Path(__file__).resolve().parents[1]


def get_runtime_base_dir() -> Path:
    """Return extraction directory when frozen, otherwise project root."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent

    return get_project_root()


def get_assets_dir() -> Path:
    """Return assets directory for current runtime mode."""
    return get_runtime_base_dir() / "assets"


def _default_user_data_root() -> Path:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata)

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home)

    return Path.home() / ".local" / "share"


def get_user_data_dir(app_name: str = APP_NAME) -> Path:
    """Return writable user data directory.

    CHESSCHAMPION_DATA_DIR can override the default for local testing.
    """
    override = os.environ.get("CHESSCHAMPION_DATA_DIR")
    if override:
        return Path(override)

    return _default_user_data_root() / app_name


def get_saved_games_dir() -> Path:
    """Return writable save directory under user data."""
    return get_user_data_dir() / "saved_games"


def get_logs_dir() -> Path:
    """Return writable logs directory under user data."""
    return get_user_data_dir() / "logs"


def get_settings_file() -> Path:
    """Return settings file path under user data."""
    return get_user_data_dir() / "settings.json"


def ensure_user_data_layout() -> Path:
    """Create standard writable app directories and return root."""
    root = get_user_data_dir()
    root.mkdir(parents=True, exist_ok=True)
    get_saved_games_dir().mkdir(parents=True, exist_ok=True)
    get_logs_dir().mkdir(parents=True, exist_ok=True)
    return root
