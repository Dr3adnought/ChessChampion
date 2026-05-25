import unittest

from game.champion_chess import ChessGame
from game.move_validator import MoveValidator
from game.pieces import create_piece
from game.save_load.service import delete_save, load_game, save_game
from game.types import Color, PieceType, Position


class SaveLoadRegressionTests(unittest.TestCase):
    def setUp(self):
        self.created_files = []

    def tearDown(self):
        for file_name in self.created_files:
            delete_save(file_name)

    def _save_and_load(self, game: ChessGame, save_id: str, file_name: str):
        save_result = save_game(
            game,
            source="manual",
            save_id=save_id,
            file_name=file_name,
            session_meta={"mode": "pvp", "players": {"white": "P1", "black": "P2"}},
        )
        self.assertTrue(save_result.get("success"), save_result.get("error", "save failed"))
        self.created_files.append(file_name)

        load_result = load_game(file_name)
        self.assertTrue(load_result.get("success"), load_result.get("error", "load failed"))
        return load_result["game"]

    def test_en_passant_availability_preserved(self):
        game = ChessGame()
        game.move_piece(6, 4, 4, 4)  # e2 -> e4 (creates en passant target e3)

        loaded_game = self._save_and_load(game, "sl10-en-passant", "sl10-en-passant.json")

        self.assertIsNotNone(loaded_game.board.en_passant_target)
        self.assertEqual(loaded_game.board.en_passant_target.to_algebraic(), "e3")

    def test_castling_rights_preserved(self):
        game = ChessGame()
        game.move_piece(6, 0, 5, 0)  # a2 -> a3
        game.move_piece(1, 0, 2, 0)  # a7 -> a6
        game.move_piece(7, 0, 6, 0)  # a1 -> a2 (white queenside rook moved)

        loaded_game = self._save_and_load(game, "sl10-castling", "sl10-castling.json")

        self.assertFalse(loaded_game.board.castling_rights.can_castle(Color.WHITE, kingside=False))
        self.assertTrue(loaded_game.board.castling_rights.can_castle(Color.WHITE, kingside=True))

    def test_promotion_history_and_undo_redo_survive_load(self):
        game = ChessGame()

        # Build a minimal legal board that allows immediate white promotion.
        for row in range(8):
            for col in range(8):
                game.board.set_piece(Position(row, col), None)

        game.board.set_piece(Position(7, 4), create_piece(Color.WHITE, PieceType.KING))
        game.board.set_piece(Position(0, 4), create_piece(Color.BLACK, PieceType.KING))
        game.board.set_piece(Position(1, 0), create_piece(Color.WHITE, PieceType.PAWN))

        game.game_state.current_turn = Color.WHITE
        game.game_state.move_history.clear()
        game.game_state.redo_stack.clear()
        game.game_state.selected_position = None
        game.game_state.validator = MoveValidator(game.board)

        promoted = game.execute_promotion(Position(1, 0), Position(0, 0), PieceType.QUEEN)
        self.assertTrue(promoted)

        loaded_game = self._save_and_load(game, "sl10-promotion", "sl10-promotion.json")

        self.assertTrue(loaded_game.game_state.can_undo())
        self.assertTrue(loaded_game.game_state.undo_move())

        piece_a7 = loaded_game.board.get_piece(Position(1, 0))
        piece_a8 = loaded_game.board.get_piece(Position(0, 0))
        self.assertIsNotNone(piece_a7)
        self.assertEqual(piece_a7.piece_type, PieceType.PAWN)
        self.assertIsNone(piece_a8)

        self.assertTrue(loaded_game.game_state.can_redo())
        self.assertTrue(loaded_game.game_state.redo_move())

        promoted_piece = loaded_game.board.get_piece(Position(0, 0))
        self.assertIsNotNone(promoted_piece)
        self.assertEqual(promoted_piece.piece_type, PieceType.QUEEN)

    def test_timed_game_state_and_timeout_survive_load(self):
        game = ChessGame(1, 0)
        game.timer.start_turn(Color.WHITE)
        game.timer.white_time = -0.5

        loaded_game = self._save_and_load(game, "sl10-timer", "sl10-timer.json")

        self.assertTrue(loaded_game.timer.is_timed)
        self.assertEqual(loaded_game.timer.current_player, Color.WHITE)
        self.assertTrue(loaded_game.timer.is_time_out(Color.WHITE))


if __name__ == "__main__":
    unittest.main()
