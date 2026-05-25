import unittest

from game.network.protocol_contract import PROTOCOL_VERSION
from game.network.session_manager import SessionManager


class SessionManagerUnitTests(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager()
        self.client_seq = 0

    def _message(self, *, event_type: str, game_id: str, player_id: str, payload: dict) -> dict:
        self.client_seq += 1
        return {
            "protocol_version": PROTOCOL_VERSION,
            "event_type": event_type,
            "event_id": f"evt_client_{self.client_seq}",
            "sent_at_utc": "2026-05-25T21:05:00Z",
            "game_id": game_id,
            "player_id": player_id,
            "sequence": self.client_seq,
            "payload": payload,
        }

    def _create_host_and_join(self):
        host_create = self.manager.process_message(
            self._message(
                event_type="host_create",
                game_id="pending",
                player_id="pending-host",
                payload={"requested_side": "white", "time_control": {"minutes": 5, "increment": 0}},
            )
        )
        self.assertTrue(host_create["ok"])
        host_event = host_create["events"][0]

        game_id = host_event["payload"]["game_id"]
        host_player_id = host_event["payload"]["player_id"]

        join_result = self.manager.process_message(
            self._message(
                event_type="join_request",
                game_id=game_id,
                player_id="pending-guest",
                payload={"invite_code": host_event["payload"]["invite_code"]},
            )
        )
        self.assertTrue(join_result["ok"])

        join_accepted = next(e for e in join_result["events"] if e["event_type"] == "join_accepted")
        guest_player_id = join_accepted["payload"]["player_id"]

        return {
            "game_id": game_id,
            "host_player_id": host_player_id,
            "guest_player_id": guest_player_id,
            "host_event": host_event,
            "join_events": join_result["events"],
        }

    def test_host_create_and_join_emit_game_start(self):
        result = self._create_host_and_join()
        start_events = [e for e in result["join_events"] if e["event_type"] == "game_start"]
        self.assertEqual(len(start_events), 2)
        self.assertIn("state", start_events[0]["payload"])
        self.assertIn("board", start_events[0]["payload"]["state"])

    def test_move_intent_accepted_for_legal_move(self):
        setup = self._create_host_and_join()

        sync = self.manager.process_message(
            self._message(
                event_type="state_resync_request",
                game_id=setup["game_id"],
                player_id=setup["host_player_id"],
                payload={},
            )
        )
        self.assertTrue(sync["ok"])
        state = sync["events"][0]["payload"]

        move_result = self.manager.process_message(
            self._message(
                event_type="move_intent",
                game_id=setup["game_id"],
                player_id=setup["host_player_id"],
                payload={
                    "move": {"from": "e2", "to": "e4", "promotion": None},
                    "expected_halfmove": state["halfmove"],
                    "expected_position_hash": state["position_hash"],
                },
            )
        )
        self.assertTrue(move_result["ok"])
        self.assertTrue(all(e["event_type"] == "move_accepted" for e in move_result["events"]))

    def test_move_intent_rejected_for_hash_mismatch(self):
        setup = self._create_host_and_join()

        move_result = self.manager.process_message(
            self._message(
                event_type="move_intent",
                game_id=setup["game_id"],
                player_id=setup["host_player_id"],
                payload={
                    "move": {"from": "e2", "to": "e4", "promotion": None},
                    "expected_halfmove": 99,
                    "expected_position_hash": "sha256:not-real",
                },
            )
        )
        self.assertTrue(move_result["ok"])
        self.assertEqual(move_result["events"][0]["event_type"], "move_rejected")
        self.assertEqual(move_result["events"][0]["payload"]["reason"], "state_desync")
        self.assertIn("authoritative_state", move_result["events"][0]["payload"])

    def test_state_resync_includes_authoritative_state_snapshot(self):
        setup = self._create_host_and_join()

        sync = self.manager.process_message(
            self._message(
                event_type="state_resync_request",
                game_id=setup["game_id"],
                player_id=setup["host_player_id"],
                payload={},
            )
        )
        self.assertTrue(sync["ok"])
        payload = sync["events"][0]["payload"]
        self.assertIn("state", payload)
        self.assertIn("board", payload["state"])

    def test_reconnect_rotates_resume_token(self):
        setup = self._create_host_and_join()
        old_token = setup["host_event"]["payload"]["resume_token"]

        reconnect = self.manager.process_message(
            self._message(
                event_type="reconnect_request",
                game_id=setup["game_id"],
                player_id=setup["host_player_id"],
                payload={"game_id": setup["game_id"], "player_id": setup["host_player_id"], "resume_token": old_token},
            )
        )
        self.assertTrue(reconnect["ok"])
        accepted = reconnect["events"][0]
        self.assertEqual(accepted["event_type"], "reconnect_accepted")
        self.assertNotEqual(accepted["payload"]["new_resume_token"], old_token)
        self.assertIn("state", accepted["payload"])
        self.assertIn("board", accepted["payload"]["state"]["state"])


if __name__ == "__main__":
    unittest.main()
