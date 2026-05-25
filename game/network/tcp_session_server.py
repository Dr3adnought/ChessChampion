"""TCP JSON-lines server that routes protocol envelopes through SessionManager."""

from __future__ import annotations

import argparse
import json
import socket
import threading
from typing import Any

from game.network.session_manager import SessionManager


class TcpSessionServer:
    """Small TCP server that dispatches client envelopes to SessionManager."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765, *, manager: SessionManager | None = None):
        self.host = host
        self.port = int(port)
        self.manager = manager or SessionManager()

        self._server_socket: socket.socket | None = None
        self._accept_thread: threading.Thread | None = None
        self._client_threads: set[threading.Thread] = set()
        self._connections: set[socket.socket] = set()
        self._player_connections: dict[str, socket.socket] = {}
        self._socket_players: dict[socket.socket, str] = {}

        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._send_lock = threading.Lock()

    def start(self) -> None:
        if self._server_socket is not None:
            return

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(16)
        server_socket.settimeout(0.25)

        self._server_socket = server_socket
        self.host, self.port = server_socket.getsockname()

        self._stop.clear()
        self._accept_thread = threading.Thread(target=self._accept_loop, name="tcp-session-server-accept", daemon=True)
        self._accept_thread.start()

    def stop(self) -> None:
        self._stop.set()

        server_socket = self._server_socket
        self._server_socket = None
        if server_socket is not None:
            try:
                server_socket.close()
            except OSError:
                pass

        with self._lock:
            open_connections = list(self._connections)

        for conn in open_connections:
            self._close_connection(conn)

        accept_thread = self._accept_thread
        self._accept_thread = None
        if accept_thread is not None and accept_thread.is_alive():
            accept_thread.join(timeout=0.75)

        with self._lock:
            client_threads = list(self._client_threads)
        for thread in client_threads:
            if thread.is_alive():
                thread.join(timeout=0.75)

    def _accept_loop(self) -> None:
        while not self._stop.is_set():
            server_socket = self._server_socket
            if server_socket is None:
                return

            try:
                conn, _ = server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                return

            conn.settimeout(0.25)
            with self._lock:
                self._connections.add(conn)

            client_thread = threading.Thread(target=self._client_loop, args=(conn,), daemon=True)
            with self._lock:
                self._client_threads.add(client_thread)
            client_thread.start()

    def _client_loop(self, conn: socket.socket) -> None:
        buffer = ""
        try:
            while not self._stop.is_set():
                try:
                    chunk = conn.recv(4096)
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

                    response = self.manager.process_message(message)
                    events = response.get("events", []) if isinstance(response, dict) else []
                    if not isinstance(events, list):
                        continue

                    for event in events:
                        if not isinstance(event, dict):
                            continue
                        self._register_connection_from_event(conn, event)
                        self._dispatch_event(conn, event)
        finally:
            self._close_connection(conn)
            with self._lock:
                current = threading.current_thread()
                if current in self._client_threads:
                    self._client_threads.remove(current)

    def _register_connection_from_event(self, conn: socket.socket, event: dict[str, Any]) -> None:
        event_type = event.get("event_type")
        payload = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}

        if event_type not in {"host_created", "join_accepted", "reconnect_accepted"}:
            return

        candidate_player_id = payload.get("player_id")
        if not isinstance(candidate_player_id, str) or not candidate_player_id:
            candidate_player_id = event.get("player_id") if isinstance(event.get("player_id"), str) else None

        if not candidate_player_id:
            return

        with self._lock:
            self._player_connections[candidate_player_id] = conn
            self._socket_players[conn] = candidate_player_id

    def _dispatch_event(self, source_conn: socket.socket, event: dict[str, Any]) -> None:
        target_conn: socket.socket | None = None
        target_player_id = event.get("player_id")

        with self._lock:
            if isinstance(target_player_id, str) and target_player_id:
                target_conn = self._player_connections.get(target_player_id)

        if target_conn is None:
            target_conn = source_conn

        raw = (json.dumps(event, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            with self._send_lock:
                target_conn.sendall(raw)
        except OSError:
            self._close_connection(target_conn)

    def _close_connection(self, conn: socket.socket) -> None:
        with self._lock:
            if conn in self._connections:
                self._connections.remove(conn)
            player_id = self._socket_players.pop(conn, None)
            if player_id:
                mapped = self._player_connections.get(player_id)
                if mapped is conn:
                    self._player_connections.pop(player_id, None)

        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            conn.close()
        except OSError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ChessChampion TCP session server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Bind TCP port (default: 8765)")
    args = parser.parse_args()

    server = TcpSessionServer(args.host, args.port)
    server.start()
    print(f"TcpSessionServer listening on {server.host}:{server.port}")

    try:
        while True:
            if server._stop.wait(1.0):
                break
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


if __name__ == "__main__":
    main()