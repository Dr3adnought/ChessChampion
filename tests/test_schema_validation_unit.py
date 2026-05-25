import unittest

from game.save_load.schema import SCHEMA_VERSION, validate_payload


def make_valid_payload() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "save_id": "unit-test-save",
        "created_at_utc": "2026-05-25T12:00:00Z",
        "updated_at_utc": "2026-05-25T12:05:00Z",
        "source": "manual",
        "app": {"name": "ChessChampion", "version": "1.0.0"},
        "session": {
            "mode": "pvp",
            "players": {"white": "P1", "black": "P2"},
            "ai": {"enabled": False, "color": "black", "difficulty": "none", "depth": 0},
        },
        "clock": {
            "is_timed": False,
            "base_seconds": 0,
            "increment_seconds": 0,
            "white_remaining_seconds": 0,
            "black_remaining_seconds": 0,
            "current_player": None,
            "is_paused": True,
        },
        "position": {
            "board": [[None for _ in range(8)] for _ in range(8)],
            "current_turn": "white",
            "game_status": "ACTIVE",
            "half_move_clock": 0,
            "full_move_number": 1,
            "castling_rights": "KQkq",
            "en_passant_target": None,
        },
        "captures": {
            "captured_by_white": [],
            "captured_by_black": [],
        },
        "history": {
            "moves": [],
            "redo_moves": [],
        },
        "artifacts": {},
    }


class SchemaValidationUnitTests(unittest.TestCase):
    def test_valid_payload_passes(self):
        payload = make_valid_payload()
        result = validate_payload(payload)

        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)

    def test_missing_required_field_fails(self):
        payload = make_valid_payload()
        del payload["history"]

        result = validate_payload(payload)

        self.assertFalse(result.valid)
        self.assertTrue(any("Missing required field: 'history'" in err.message for err in result.errors))

    def test_schema_version_mismatch_warns_but_is_valid(self):
        payload = make_valid_payload()
        payload["schema_version"] = "0.9.0"

        result = validate_payload(payload)

        self.assertTrue(result.valid)
        self.assertGreaterEqual(len(result.warnings), 1)

    def test_invalid_board_shape_fails(self):
        payload = make_valid_payload()
        payload["position"]["board"] = [[None for _ in range(8)] for _ in range(7)]

        result = validate_payload(payload)

        self.assertFalse(result.valid)
        self.assertTrue(any(err.path == "position.board" for err in result.errors))

    def test_online_session_with_network_metadata_passes(self):
        payload = make_valid_payload()
        payload["session"]["mode"] = "online"
        payload["session"]["ai"] = {"enabled": False, "color": "black", "difficulty": "none", "depth": 0}
        payload["session"]["network"] = {
            "role": "host",
            "invite_code": "ABCD12",
            "side": "white",
            "game_id": "game_123",
            "player_id": "player_123",
            "resume_token": "rt_123",
            "resume_token_expires_at_utc": "2026-05-25T12:30:00Z",
            "last_seen_event_id": "evt_123",
        }

        result = validate_payload(payload)

        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)


if __name__ == "__main__":
    unittest.main()
