import random
import unittest

from game.champion_chess import ChessGame
from game.save_load.serializer import deserialize_game, serialize_game


class SerializationParityUnitTests(unittest.TestCase):
    def _play_random_legal_game(self, seed: int, plies: int = 24) -> ChessGame:
        random.seed(seed)
        game = ChessGame(0, 0)

        for _ in range(plies):
            legal_moves = game.game_state.get_all_legal_moves()
            if not legal_moves:
                break

            move = random.choice(legal_moves)
            moved = game.game_state.make_move(move)
            self.assertTrue(moved)
            game.last_move = (move.from_pos, move.to_pos)

            if game.game_over:
                break

        return game

    def _assert_payload_equivalent(self, payload_a: dict, payload_b: dict):
        self.assertEqual(payload_a["schema_version"], payload_b["schema_version"])
        self.assertEqual(payload_a["session"], payload_b["session"])
        self.assertEqual(payload_a["clock"], payload_b["clock"])
        self.assertEqual(payload_a["position"], payload_b["position"])
        self.assertEqual(payload_a["captures"], payload_b["captures"])
        self.assertEqual(payload_a["history"], payload_b["history"])

    def test_random_legal_games_round_trip_serialization_parity(self):
        for seed in (7, 21, 42):
            with self.subTest(seed=seed):
                original = self._play_random_legal_game(seed)

                payload_1 = serialize_game(
                    original,
                    save_id=f"parity-{seed}-1",
                    source="manual",
                    session_meta={"mode": "pvp", "players": {"white": "W", "black": "B"}},
                )

                restored = deserialize_game(payload_1)["game"]
                payload_2 = serialize_game(
                    restored,
                    save_id=f"parity-{seed}-2",
                    source="manual",
                    session_meta={"mode": "pvp", "players": {"white": "W", "black": "B"}},
                )

                self._assert_payload_equivalent(payload_1, payload_2)


if __name__ == "__main__":
    unittest.main()
