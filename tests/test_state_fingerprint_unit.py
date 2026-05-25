import unittest

from game.champion_chess import ChessGame
from game.state_fingerprint import fingerprint_game_state
from game.types import Position


class StateFingerprintUnitTests(unittest.TestCase):
    def test_fingerprint_is_deterministic_for_same_state(self):
        game = ChessGame()

        first = fingerprint_game_state(game)
        second = fingerprint_game_state(game)

        self.assertEqual(first, second)

    def test_fingerprint_changes_after_move(self):
        game = ChessGame()

        before = fingerprint_game_state(game)
        from_pos = Position(6, 4)
        legal_moves = game.game_state.get_legal_moves_for_position(from_pos)
        target_move = next(move for move in legal_moves if move.to_pos == Position(4, 4))
        moved = game.game_state.make_move(target_move)
        self.assertTrue(moved)
        after = fingerprint_game_state(game)

        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
