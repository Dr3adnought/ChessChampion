import unittest

from game.network.protocol_contract import PROTOCOL_VERSION, validate_envelope


class NetworkProtocolContractUnitTests(unittest.TestCase):
    def _valid_message(self) -> dict:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "event_type": "move_intent",
            "event_id": "evt_1",
            "sent_at_utc": "2026-05-25T21:05:00Z",
            "game_id": "game_1",
            "player_id": "player_1",
            "sequence": 1,
            "payload": {"move": {"from": "e2", "to": "e4", "promotion": None}},
        }

    def test_valid_envelope_passes(self):
        ok, error = validate_envelope(self._valid_message())
        self.assertTrue(ok)
        self.assertIsNone(error)

    def test_missing_required_field_fails(self):
        msg = self._valid_message()
        del msg["event_id"]

        ok, error = validate_envelope(msg)
        self.assertFalse(ok)
        self.assertIn("missing required field", error)

    def test_invalid_version_fails(self):
        msg = self._valid_message()
        msg["protocol_version"] = "9.9"

        ok, error = validate_envelope(msg)
        self.assertFalse(ok)
        self.assertIn("unsupported protocol_version", error)

    def test_invalid_event_type_fails(self):
        msg = self._valid_message()
        msg["event_type"] = "unknown_event"

        ok, error = validate_envelope(msg)
        self.assertFalse(ok)
        self.assertIn("unsupported event_type", error)


if __name__ == "__main__":
    unittest.main()
