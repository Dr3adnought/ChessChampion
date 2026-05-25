import unittest

from game.champion_chess import ChessGame
from game.network.online_sync import (
    apply_authoritative_clock,
    apply_authoritative_move,
    apply_authoritative_state,
    build_move_intent_payload,
)
from game.types import PieceType, Position


class OnlineSyncUnitTests(unittest.TestCase):
    def test_build_move_intent_contains_expected_state(self):
        game = ChessGame()
        payload = build_move_intent_payload(
            game,
            from_pos=Position(6, 4),
            to_pos=Position(4, 4),
        )

        self.assertEqual(payload["move"]["from"], "e2")
        self.assertEqual(payload["move"]["to"], "e4")
        self.assertEqual(payload["expected_halfmove"], 0)
        self.assertTrue(payload["expected_position_hash"].startswith("sha256:"))

    def test_apply_authoritative_move_applies_legal_move(self):
        game = ChessGame()
        applied = apply_authoritative_move(
            game,
            {"from": "e2", "to": "e4", "promotion": None},
        )

        self.assertTrue(applied)
        self.assertEqual(game.turn, "black")
        self.assertIsNotNone(game.last_move)

    def test_apply_authoritative_move_rejects_illegal_move(self):
        game = ChessGame()
        applied = apply_authoritative_move(
            game,
            {"from": "e2", "to": "e5", "promotion": None},
        )

        self.assertFalse(applied)
        self.assertEqual(game.turn, "white")

    def test_apply_authoritative_clock_updates_timer(self):
        game = ChessGame(5, 0)
        apply_authoritative_clock(
            game,
            {"white_ms": 299000, "black_ms": 300000, "active": "black"},
        )

        self.assertAlmostEqual(game.timer.white_time, 299.0, places=3)
        self.assertAlmostEqual(game.timer.black_time, 300.0, places=3)
        self.assertEqual(game.timer.current_player.value, "black")
        self.assertFalse(game.timer.is_paused)

    def test_apply_authoritative_state_replaces_board_and_turn(self):
        game = ChessGame()
        state_payload = {
            "board": [[None for _ in range(8)] for _ in range(8)],
            "current_turn": "black",
            "castling_rights": "-",
            "en_passant_target": None,
            "half_move_clock": 7,
            "full_move_number": 14,
            "last_move": {"from": "a2", "to": "a4"},
        }

        applied = apply_authoritative_state(game, state_payload)

        self.assertTrue(applied)
        self.assertEqual(game.turn, "black")
        self.assertEqual(game.game_state.half_move_clock, 7)
        self.assertEqual(game.game_state.full_move_number, 14)
        self.assertIsNotNone(game.last_move)


if __name__ == "__main__":
    unittest.main()
