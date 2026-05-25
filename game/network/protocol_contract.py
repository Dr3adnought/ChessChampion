"""Protocol envelope and event contract helpers for Online Phase A."""

from __future__ import annotations

from typing import Any

PROTOCOL_VERSION = "1.0"

PHASE_A_EVENT_TYPES = {
    "host_create",
    "host_created",
    "join_request",
    "join_accepted",
    "join_rejected",
    "game_start",
    "reconnect_request",
    "reconnect_accepted",
    "reconnect_rejected",
    "move_intent",
    "move_accepted",
    "move_rejected",
    "state_resync_request",
    "state_resync",
    "draw_offer",
    "draw_response",
    "resign",
    "game_end",
    "heartbeat",
    "error",
}

REQUIRED_ENVELOPE_FIELDS = (
    "protocol_version",
    "event_type",
    "event_id",
    "sent_at_utc",
    "game_id",
    "player_id",
    "sequence",
    "payload",
)


def validate_envelope(message: Any) -> tuple[bool, str | None]:
    """Validate protocol envelope shape and key invariants."""
    if not isinstance(message, dict):
        return False, "message must be an object"

    for field_name in REQUIRED_ENVELOPE_FIELDS:
        if field_name not in message:
            return False, f"missing required field: {field_name}"

    if message.get("protocol_version") != PROTOCOL_VERSION:
        return False, f"unsupported protocol_version: {message.get('protocol_version')}"

    event_type = message.get("event_type")
    if not isinstance(event_type, str) or event_type not in PHASE_A_EVENT_TYPES:
        return False, f"unsupported event_type: {event_type}"

    if not isinstance(message.get("sequence"), int) or message["sequence"] < 0:
        return False, "sequence must be a non-negative integer"

    if not isinstance(message.get("payload"), dict):
        return False, "payload must be an object"

    return True, None
