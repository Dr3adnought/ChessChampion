"""Application identity and version metadata."""

from __future__ import annotations

import os

APP_NAME = "ChessChampion"
APP_VERSION = "0.2.0"
APP_BUILD = os.environ.get("CHESSCHAMPION_BUILD", "local")


def get_app_metadata() -> dict[str, str]:
    """Return app metadata for persistence and diagnostics."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "build": APP_BUILD,
    }
