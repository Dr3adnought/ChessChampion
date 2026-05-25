"""TCP JSON-lines network adapter for real transport-backed online events."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import socket
import threading
from typing import Any
from uuid import uuid4

from game.network.adapter import NetworkAdapter, NetworkEvent
from game.network.protocol_contract import PROTOCOL_VERSION


class TcpJsonNetworkAdapter(NetworkAdapter):
    """NetworkAdapter backed by a TCP socket using newline-delimited JSON envelopes."""

    def __init__(self, host: str, port: int, *, connect_timeout_seconds: float = 5.0):
        self.host = host
        self.port = int(port)
        self.connect_timeout_seconds = connect_timeout_seconds

        self.player_id: str | None = None
        self.game_id: str | None = None

        self._sequence = 0
        self._socket: socket.socket | None = None
        self._recv_thread: threading.Thread | None = None
        self._recv_stop = threading.Event()
        self._inbox: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def connect(self) -> None:
        if self._socket is not None:
            return

        sock = socket.create_connection((self.host, self.port), timeout=self.connect_timeout_seconds)
        sock.settimeout(0.25)
        self._socket = sock

        self._recv_stop.clear()
        self._recv_thread = threading.Thread(target=self._recv_loop, name="tcp-json-adapter-recv", daemon=True)
        self._recv_thread.start()

    def disconnect(self) -> None:
        self._recv_stop.set()

        sock = self._socket
        self._socket = None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

        if self._recv_thread is not None and self._recv_thread.is_alive():
            self._recv_thread.join(timeout=0.5)
        self._recv_thread = None

    def send(self, event_type: str, payload: dict[str, Any]) -> None:
        sock = self._socket
        if sock is None:
            raise RuntimeError("adapter must be connected before send")

        self._sequence += 1
        envelope = {
            "protocol_version": PROTOCOL_VERSION,
            "event_type": event_type,
            "event_id": f"evt_client_{uuid4().hex[:12]}",
            "sent_at_utc": self._iso(datetime.now(timezone.utc)),
            "game_id": self.game_id or payload.get("game_id", "pending"),
            "player_id": self.player_id or payload.get("player_id", "pending_client"),
            "sequence": self._sequence,
            "payload": payload,
        }

        raw = (json.dumps(envelope, separators=(",", ":")) + "\n").encode("utf-8")
        sock.sendall(raw)

    def poll(self) -> list[NetworkEvent]:
        with self._lock:
            pending = self._inbox
            self._inbox = []

        self._refresh_identity(pending)
        return [
            NetworkEvent(
                event_type=str(item.get("event_type", "")),
                payload=item.get("payload", {}) if isinstance(item.get("payload"), dict) else {},
                event_id=str(item.get("event_id", "")),
            )
            for item in pending
        ]

    def _recv_loop(self) -> None:
        buffer = ""
        while not self._recv_stop.is_set():
            sock = self._socket
            if sock is None:
                return

            try:
                chunk = sock.recv(4096)
                if not chunk:
                    return
                buffer += chunk.decode("utf-8")
            except socket.timeout:
                continue
            except OSError:
                return

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(message, dict):
                    continue

                with self._lock:
                    self._inbox.append(message)

    def _refresh_identity(self, events: list[dict[str, Any]]) -> None:
        for message in events:
            payload = message.get("payload", {}) if isinstance(message.get("payload"), dict) else {}

            payload_player_id = payload.get("player_id")
            if isinstance(payload_player_id, str) and payload_player_id:
                self.player_id = payload_player_id

            payload_game_id = payload.get("game_id")
            if isinstance(payload_game_id, str) and payload_game_id:
                self.game_id = payload_game_id

            if not self.player_id:
                event_player_id = message.get("player_id")
                if isinstance(event_player_id, str) and event_player_id:
                    self.player_id = event_player_id

            if not self.game_id:
                event_game_id = message.get("game_id")
                if isinstance(event_game_id, str) and event_game_id:
                    self.game_id = event_game_id

    @staticmethod
    def _iso(value: datetime) -> str:
        return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")
