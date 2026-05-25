import json
import socket
import threading
import time
import unittest

from game.network.protocol_contract import PROTOCOL_VERSION
from game.network.tcp_adapter import TcpJsonNetworkAdapter


class _MockTcpProtocolServer:
    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(1)
        self.host, self.port = self._sock.getsockname()
        self.received: list[dict] = []
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stop = threading.Event()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            pass
        if self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def _run(self):
        try:
            conn, _ = self._sock.accept()
        except OSError:
            return

        with conn:
            conn.settimeout(0.25)
            buffer = ""
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

                    message = json.loads(line)
                    self.received.append(message)
                    event_type = message.get("event_type")

                    if event_type == "host_create":
                        response = {
                            "protocol_version": PROTOCOL_VERSION,
                            "event_type": "host_created",
                            "event_id": "evt_server_host_created",
                            "sent_at_utc": "2026-05-25T21:05:01Z",
                            "game_id": "game_tcp_1",
                            "player_id": "player_tcp_1",
                            "sequence": 1,
                            "payload": {
                                "game_id": "game_tcp_1",
                                "player_id": "player_tcp_1",
                                "invite_code": "ABCD12",
                                "host_side": "white",
                                "resume_token": "rt_tcp_1",
                                "resume_token_expires_at_utc": "2026-05-25T22:00:00Z",
                            },
                        }
                        conn.sendall((json.dumps(response) + "\n").encode("utf-8"))


class TcpAdapterUnitTests(unittest.TestCase):
    def setUp(self):
        self.server = _MockTcpProtocolServer()
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_send_host_create_and_receive_host_created(self):
        adapter = TcpJsonNetworkAdapter(self.server.host, self.server.port)
        adapter.connect()
        try:
            adapter.send("host_create", {"requested_side": "white", "time_control": {"minutes": 5, "increment": 0}})

            deadline = time.time() + 1.5
            events = []
            while time.time() < deadline:
                events = adapter.poll()
                if events:
                    break
                time.sleep(0.02)

            self.assertTrue(events)
            self.assertEqual(events[0].event_type, "host_created")
            self.assertEqual(events[0].payload.get("invite_code"), "ABCD12")
            self.assertEqual(adapter.game_id, "game_tcp_1")
            self.assertEqual(adapter.player_id, "player_tcp_1")

            self.assertTrue(self.server.received)
            sent = self.server.received[0]
            self.assertEqual(sent.get("protocol_version"), PROTOCOL_VERSION)
            self.assertEqual(sent.get("event_type"), "host_create")
            self.assertIsInstance(sent.get("sequence"), int)
        finally:
            adapter.disconnect()


if __name__ == "__main__":
    unittest.main()
