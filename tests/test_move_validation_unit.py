import unittest

from game.board import Board
from game.game_state import GameState
from game.pieces import create_piece
from game.types import CastlingRights, Color, MoveType, PieceType, Position


class MoveValidationUnitTests(unittest.TestCase):
    def _empty_board(self) -> Board:
        board = Board()
        for row in range(8):
            for col in range(8):
                board.set_piece(Position(row, col), None)
        board.en_passant_target = None
        board.castling_rights = CastlingRights(0)
        return board

    def test_castling_not_allowed_when_king_is_in_check(self):
        board = self._empty_board()
        board.set_piece(Position(7, 4), create_piece(Color.WHITE, PieceType.KING))  # e1
        board.set_piece(Position(7, 7), create_piece(Color.WHITE, PieceType.ROOK))  # h1
        board.set_piece(Position(0, 4), create_piece(Color.BLACK, PieceType.ROOK))  # e8 checking along file
        board.castling_rights = CastlingRights(CastlingRights.WHITE_KINGSIDE)

        state = GameState(board)
        legal_moves = state.get_legal_moves_for_position(Position(7, 4))

        self.assertFalse(any(m.move_type == MoveType.CASTLING_KINGSIDE for m in legal_moves))

    def test_en_passant_blocked_if_it_exposes_own_king(self):
        board = self._empty_board()
        board.set_piece(Position(7, 4), create_piece(Color.WHITE, PieceType.KING))  # e1
        board.set_piece(Position(0, 4), create_piece(Color.BLACK, PieceType.ROOK))  # e8
        board.set_piece(Position(3, 4), create_piece(Color.WHITE, PieceType.PAWN))  # e5
        board.set_piece(Position(3, 3), create_piece(Color.BLACK, PieceType.PAWN))  # d5
        board.en_passant_target = Position(2, 3)  # d6 (capturable by e5 pawn)

        state = GameState(board)
        legal_moves = state.get_legal_moves_for_position(Position(3, 4))

        self.assertFalse(any(m.move_type == MoveType.EN_PASSANT for m in legal_moves))

    def test_pinned_piece_cannot_move_and_expose_king(self):
        board = self._empty_board()
        board.set_piece(Position(7, 4), create_piece(Color.WHITE, PieceType.KING))  # e1
        board.set_piece(Position(6, 4), create_piece(Color.WHITE, PieceType.KNIGHT))  # e2 pinned
        board.set_piece(Position(0, 4), create_piece(Color.BLACK, PieceType.ROOK))  # e8

        state = GameState(board)
        legal_moves = state.get_legal_moves_for_position(Position(6, 4))

        self.assertEqual(legal_moves, [])


if __name__ == "__main__":
    unittest.main()
