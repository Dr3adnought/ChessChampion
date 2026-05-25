import time
import unittest

from game.network.tcp_adapter import TcpJsonNetworkAdapter
from game.network.tcp_session_server import TcpSessionServer


class TcpSessionServerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.server = TcpSessionServer("127.0.0.1", 0)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def _wait_for_event(self, adapter: TcpJsonNetworkAdapter, event_type: str, timeout: float = 2.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            events = adapter.poll()
            for event in events:
                if event.event_type == event_type:
                    return event
            time.sleep(0.02)
        self.fail(f"timed out waiting for event_type={event_type}")

    def test_host_join_move_and_reconnect_round_trip(self):
        host = TcpJsonNetworkAdapter(self.server.host, self.server.port)
        guest = TcpJsonNetworkAdapter(self.server.host, self.server.port)
        host_reconnect = TcpJsonNetworkAdapter(self.server.host, self.server.port)

        host.connect()
        guest.connect()

        try:
            host.send("host_create", {"requested_side": "white", "time_control": {"minutes": 5, "increment": 0}})
            host_created = self._wait_for_event(host, "host_created")

            game_id = host_created.payload["game_id"]
            host_player_id = host_created.payload["player_id"]
            invite_code = host_created.payload["invite_code"]
            old_resume_token = host_created.payload["resume_token"]

            guest.send("join_request", {"invite_code": invite_code})
            join_accepted = self._wait_for_event(guest, "join_accepted")
            self.assertEqual(join_accepted.payload["game_id"], game_id)

            host_game_start = self._wait_for_event(host, "game_start")

            host.send(
                "move_intent",
                {
                    "move": {"from": "e2", "to": "e4", "promotion": None},
                    "expected_halfmove": host_game_start.payload["halfmove"],
                    "expected_position_hash": host_game_start.payload["position_hash"],
                },
            )

            host_move_accepted = self._wait_for_event(host, "move_accepted")
            guest_move_accepted = self._wait_for_event(guest, "move_accepted")
            self.assertEqual(host_move_accepted.payload["move"]["from"], "e2")
            self.assertEqual(guest_move_accepted.payload["move"]["to"], "e4")

            host.disconnect()
            host_reconnect.connect()
            host_reconnect.send(
                "reconnect_request",
                {
                    "game_id": game_id,
                    "player_id": host_player_id,
                    "resume_token": old_resume_token,
                },
            )

            reconnect_accepted = self._wait_for_event(host_reconnect, "reconnect_accepted")
            self.assertIn("state", reconnect_accepted.payload)
            self.assertNotEqual(reconnect_accepted.payload["new_resume_token"], old_resume_token)
        finally:
            host.disconnect()
            guest.disconnect()
            host_reconnect.disconnect()


if __name__ == "__main__":
    unittest.main()