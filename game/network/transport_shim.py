"""Transport-backed in-process shim for SessionManager message routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from game.network.adapter import NetworkAdapter, NetworkEvent
from game.network.protocol_contract import PROTOCOL_VERSION
from game.network.session_manager import SessionManager


@dataclass
class _ClientState:
    adapter: "SessionManagerClientAdapter"
    player_id: str | None = None
    game_id: str | None = None


class SessionManagerHub:
    """Routes protocol envelopes between adapters via SessionManager."""

    def __init__(self, manager: SessionManager | None = None):
        self.manager = manager or SessionManager()
        self._clients: dict[str, _ClientState] = {}
        self._client_by_player: dict[str, str] = {}

    def register(self, adapter: "SessionManagerClientAdapter") -> str:
        client_id = f"conn_{uuid4().hex[:12]}"
        self._clients[client_id] = _ClientState(adapter=adapter)
        return client_id

    def unregister(self, client_id: str) -> None:
        state = self._clients.pop(client_id, None)
        if state and state.player_id:
            self._client_by_player.pop(state.player_id, None)

    def submit(self, sender_client_id: str, envelope: dict[str, Any]) -> dict[str, Any]:
        result = self.manager.process_message(envelope)
        events = result.get("events", [])
        for event in events:
            self._route_event(sender_client_id, event)
        return result

    def _route_event(self, sender_client_id: str, event: dict[str, Any]) -> None:
        recipient_player_id = str(event.get("player_id", ""))
        recipient_client_id = self._client_by_player.get(recipient_player_id)

        if recipient_client_id is None:
            sender_state = self._clients.get(sender_client_id)
            if sender_state:
                sender_state.adapter._enqueue_event(event)
                self._try_bind_identity(sender_client_id, event)
            return

        state = self._clients.get(recipient_client_id)
        if state:
            state.adapter._enqueue_event(event)
            self._try_bind_identity(recipient_client_id, event)

    def _try_bind_identity(self, client_id: str, event: dict[str, Any]) -> None:
        state = self._clients.get(client_id)
        if not state:
            return

        payload = event.get("payload", {})
        event_player_id = event.get("player_id")
        payload_player_id = payload.get("player_id") if isinstance(payload, dict) else None
        bound_player_id = payload_player_id or event_player_id

        if isinstance(bound_player_id, str) and bound_player_id and bound_player_id not in self._client_by_player:
            if state.player_id and state.player_id in self._client_by_player:
                self._client_by_player.pop(state.player_id, None)
            state.player_id = bound_player_id
            self._client_by_player[bound_player_id] = client_id

        game_id = payload.get("game_id") if isinstance(payload, dict) else None
        if not game_id:
            game_id = event.get("game_id")
        if isinstance(game_id, str) and game_id:
            state.game_id = game_id


class SessionManagerClientAdapter(NetworkAdapter):
    """Client adapter that communicates through SessionManagerHub."""

    def __init__(self, hub: SessionManagerHub):
        self._hub = hub
        self._client_id: str | None = None
        self._inbox: list[dict[str, Any]] = []
        self._sequence = 0
        self.player_id: str | None = None
        self.game_id: str | None = None

    def connect(self) -> None:
        if self._client_id is None:
            self._client_id = self._hub.register(self)

    def disconnect(self) -> None:
        if self._client_id is not None:
            self._hub.unregister(self._client_id)
            self._client_id = None

    def send(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._client_id is None:
            raise RuntimeError("adapter must be connected before send")

        self._sequence += 1
        envelope = {
            "protocol_version": PROTOCOL_VERSION,
            "event_type": event_type,
            "event_id": f"evt_client_{uuid4().hex[:12]}",
            "sent_at_utc": self._iso(datetime.now(timezone.utc)),
            "game_id": self.game_id or payload.get("game_id", "pending"),
            "player_id": self.player_id or payload.get("player_id", f"pending_{self._client_id}"),
            "sequence": self._sequence,
            "payload": payload,
        }
        self._hub.submit(self._client_id, envelope)
        self._refresh_identity_from_inbox()

    def poll(self) -> list[NetworkEvent]:
        self._refresh_identity_from_inbox()
        events = [
            NetworkEvent(event_type=item["event_type"], payload=item["payload"], event_id=item["event_id"])
            for item in self._inbox
        ]
        self._inbox.clear()
        return events

    def _enqueue_event(self, envelope: dict[str, Any]) -> None:
        self._inbox.append(envelope)

    def _refresh_identity_from_inbox(self) -> None:
        for item in self._inbox:
            payload = item.get("payload", {})
            if isinstance(payload, dict):
                player_id = payload.get("player_id")
                if isinstance(player_id, str) and player_id:
                    self.player_id = player_id
                game_id = payload.get("game_id")
                if isinstance(game_id, str) and game_id:
                    self.game_id = game_id

            if not self.player_id:
                event_player = item.get("player_id")
                if isinstance(event_player, str) and event_player:
                    self.player_id = event_player

            if not self.game_id:
                event_game = item.get("game_id")
                if isinstance(event_game, str) and event_game:
                    self.game_id = event_game

    @staticmethod
    def _iso(value: datetime) -> str:
        return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")
