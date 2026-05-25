import unittest

from game.network.session_manager import SessionManager
from game.network.transport_shim import SessionManagerClientAdapter, SessionManagerHub


class NetworkTransportShimUnitTests(unittest.TestCase):
    def setUp(self):
        self.hub = SessionManagerHub(SessionManager())
        self.host = SessionManagerClientAdapter(self.hub)
        self.guest = SessionManagerClientAdapter(self.hub)
        self.host.connect()
        self.guest.connect()

    def tearDown(self):
        self.host.disconnect()
        self.guest.disconnect()

    def test_host_create_then_join_routes_game_start(self):
        self.host.send(
            "host_create",
            {"requested_side": "white", "time_control": {"minutes": 5, "increment": 0}},
        )
        host_events = self.host.poll()
        self.assertTrue(any(e.event_type == "host_created" for e in host_events))

        host_created = next(e for e in host_events if e.event_type == "host_created")
        invite_code = host_created.payload["invite_code"]

        self.guest.send("join_request", {"invite_code": invite_code})
        guest_events = self.guest.poll()
        host_events_after_join = self.host.poll()

        self.assertTrue(any(e.event_type == "join_accepted" for e in guest_events))
        self.assertTrue(any(e.event_type == "game_start" for e in guest_events))
        self.assertTrue(any(e.event_type == "game_start" for e in host_events_after_join))

    def test_move_from_host_broadcasts_move_accepted(self):
        self.host.send(
            "host_create",
            {"requested_side": "white", "time_control": {"minutes": 5, "increment": 0}},
        )
        invite_code = next(e for e in self.host.poll() if e.event_type == "host_created").payload["invite_code"]
        self.guest.send("join_request", {"invite_code": invite_code})
        self.guest.poll()
        self.host.poll()

        self.host.send("state_resync_request", {})
        state = next(e for e in self.host.poll() if e.event_type == "state_resync")

        self.host.send(
            "move_intent",
            {
                "move": {"from": "e2", "to": "e4", "promotion": None},
                "expected_halfmove": state.payload["halfmove"],
                "expected_position_hash": state.payload["position_hash"],
            },
        )

        host_events = self.host.poll()
        guest_events = self.guest.poll()
        self.assertTrue(any(e.event_type == "move_accepted" for e in host_events))
        self.assertTrue(any(e.event_type == "move_accepted" for e in guest_events))

    def test_reconnect_with_new_adapter_restores_session_state(self):
        self.host.send(
            "host_create",
            {"requested_side": "white", "time_control": {"minutes": 5, "increment": 0}},
        )
        host_created = next(e for e in self.host.poll() if e.event_type == "host_created")
        invite_code = host_created.payload["invite_code"]
        old_token = host_created.payload["resume_token"]

        self.guest.send("join_request", {"invite_code": invite_code})
        self.guest.poll()
        self.host.poll()

        game_id = self.host.game_id
        player_id = self.host.player_id

        self.host.disconnect()

        replacement = SessionManagerClientAdapter(self.hub)
        replacement.connect()
        try:
            replacement.send(
                "reconnect_request",
                {
                    "game_id": game_id,
                    "player_id": player_id,
                    "resume_token": old_token,
                    "last_seen_event_id": "",
                },
            )

            events = replacement.poll()
            accepted = next(e for e in events if e.event_type == "reconnect_accepted")
            self.assertIn("state", accepted.payload)
            self.assertIn("clock", accepted.payload["state"])
            self.assertIn("board", accepted.payload["state"]["state"])
            self.assertNotEqual(accepted.payload["new_resume_token"], old_token)
            self.assertEqual(replacement.game_id, game_id)
            self.assertEqual(replacement.player_id, player_id)
        finally:
            replacement.disconnect()


if __name__ == "__main__":
    unittest.main()
