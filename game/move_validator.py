"""
Move validation logic separated from game state.
"""
from typing import List, Optional
import copy

from game.types import Color, Position, Move, MoveType
from game.board import Board
from game.pieces import Piece


class MoveValidator:
    """
    Validates chess moves according to the rules of chess.
    Handles check detection, checkmate, stalemate, and special moves.
    """
    
    def __init__(self, board: Board):
        self.board = board
    
    def is_king_in_check(self, color: Color) -> bool:
        """Check if the king of the given color is in check."""
        king_pos = self.board.find_king(color)
        if king_pos is None:
            return False
        
        opponent_color = color.opposite()
        return self.board.is_position_attacked(king_pos, opponent_color)
    
    def is_move_legal(self, move: Move) -> bool:
        """
        Check if a move is legal (doesn't leave king in check).
        This is the final validation after piece movement rules.
        """
        piece = self.board.get_piece(move.from_pos)
        if piece is None:
            return False
        
        # Special handling for castling
        if move.move_type in [MoveType.CASTLING_KINGSIDE, MoveType.CASTLING_QUEENSIDE]:
            return self._validate_castling(move, piece.color)
        
        # Simulate the move
        temp_board = self.board.copy()
        self._execute_move_on_board(temp_board, move)
        
        # Check if king is in check after the move
        validator = MoveValidator(temp_board)
        return not validator.is_king_in_check(piece.color)
    
    def _validate_castling(self, move: Move, color: Color) -> bool:
        """Validate castling move with all special rules."""
        # King must not be in check currently
        if self.is_king_in_check(color):
            return False
        
        # Determine side
        is_kingside = move.move_type == MoveType.CASTLING_KINGSIDE
        
        # Check castling rights
        if not self.board.castling_rights.can_castle(color, is_kingside):
            return False
        
        # Get castling parameters from lookup
        row = move.from_pos.row
        params = self._get_castling_params(is_kingside)
        
        # Validate path is clear
        if not self._is_castling_path_clear(row, params):
            return False
        
        # Validate rook is in position
        if not self._is_rook_valid(row, params['rook_col'], color):
            return False
        
        # Validate king path is not under attack
        if not self._is_castling_path_safe(row, params['king_path'], color):
            return False
        
        return True
    
    def _get_castling_params(self, is_kingside: bool) -> dict:
        """Get castling parameters (columns and paths) based on side."""
        if is_kingside:
            return {
                'rook_col': 7,
                'king_path': [5, 6],  # f and g files
                'clear_cols': [5, 6]   # Squares that must be empty
            }
        else:
            return {
                'rook_col': 0,
                'king_path': [3, 2],  # d and c files
                'clear_cols': [1, 2, 3]  # b, c, d files must be empty
            }
    
    def _is_castling_path_clear(self, row: int, params: dict) -> bool:
        """Check if all squares between king and rook are empty."""
        for col in params['clear_cols']:
            if self.board.get_piece(Position(row, col)) is not None:
                return False
        return True
    
    def _is_rook_valid(self, row: int, rook_col: int, color: Color) -> bool:
        """Check if rook is present and correct color."""
        rook = self.board.get_piece(Position(row, rook_col))
        return (rook is not None and 
                rook.piece_type.value == 'rook' and 
                rook.color == color)
    
    def _is_castling_path_safe(self, row: int, path_cols: list, color: Color) -> bool:
        """Check if king doesn't pass through or land on attacked squares."""
        opponent_color = color.opposite()
        for col in path_cols:
            if self.board.is_position_attacked(Position(row, col), opponent_color):
                return False
        return True
    
    def get_legal_moves(self, position: Position) -> List[Move]:
        """Get all legal moves for the piece at the given position."""
        piece = self.board.get_piece(position)
        if piece is None:
            return []
        
        # Get possible moves from piece
        possible_moves = piece.get_possible_moves(position, self.board)
        
        # Filter out illegal moves (that would leave king in check)
        legal_moves = []
        for move in possible_moves:
            if self.is_move_legal(move):
                legal_moves.append(move)
        
        return legal_moves
    
    def get_all_legal_moves(self, color: Color) -> List[Move]:
        """Get all legal moves for all pieces of the given color."""
        all_moves = []
        
        for position, piece in self.board.get_all_pieces(color):
            moves = self.get_legal_moves(position)
            all_moves.extend(moves)
        
        return all_moves
    
    def has_legal_moves(self, color: Color) -> bool:
        """Check if the given color has any legal moves."""
        return len(self.get_all_legal_moves(color)) > 0
    
    def _execute_move_on_board(self, board: Board, move: Move):
        """
        Execute a move on a board (used for simulation).
        This is a simplified version that handles the basic move execution.
        """
        piece = board.get_piece(move.from_pos)
        if piece is None:
            return
        
        if move.move_type == MoveType.CASTLING_KINGSIDE:
            # Move king
            board.move_piece(move.from_pos, move.to_pos)
            # Move rook
            row = move.from_pos.row
            rook_from = Position(row, 7)
            rook_to = Position(row, 5)
            board.move_piece(rook_from, rook_to)
        
        elif move.move_type == MoveType.CASTLING_QUEENSIDE:
            # Move king
            board.move_piece(move.from_pos, move.to_pos)
            # Move rook
            row = move.from_pos.row
            rook_from = Position(row, 0)
            rook_to = Position(row, 3)
            board.move_piece(rook_from, rook_to)
        
        elif move.move_type == MoveType.EN_PASSANT:
            # Move pawn
            board.move_piece(move.from_pos, move.to_pos)
            # Remove captured pawn
            captured_pawn_pos = Position(move.from_pos.row, move.to_pos.col)
            board.remove_piece(captured_pawn_pos)
        
        elif move.move_type == MoveType.PROMOTION:
            # Remove pawn
            board.remove_piece(move.from_pos)
            # Place promoted piece
            from game.pieces import create_piece
            promoted_piece = create_piece(piece.color, move.promotion_piece)
            board.set_piece(move.to_pos, promoted_piece)
        
        else:
            # Normal move or capture
            board.move_piece(move.from_pos, move.to_pos)
