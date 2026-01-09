"""
Board class for managing piece positions.
"""
from typing import Optional, List, Dict
import copy

from game.types import Color, PieceType, Position, CastlingRights
from game.pieces import Piece, create_piece, piece_from_string


class Board:
    """
    Manages the chess board state and piece positions.
    Provides methods to get/set pieces and query board state.
    """
    
    def __init__(self):
        """Initialize an empty board."""
        self._board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.castling_rights = CastlingRights()
        self.en_passant_target: Optional[Position] = None
        
    def setup_initial_position(self):
        """Set up the standard chess starting position."""
        # Black pieces (row 0-1)
        piece_order = [PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
                      PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK]
        
        for col, piece_type in enumerate(piece_order):
            self._board[0][col] = create_piece(Color.BLACK, piece_type)
            self._board[7][col] = create_piece(Color.WHITE, piece_type)
        
        for col in range(8):
            self._board[1][col] = create_piece(Color.BLACK, PieceType.PAWN)
            self._board[6][col] = create_piece(Color.WHITE, PieceType.PAWN)
    
    def get_piece(self, position: Position) -> Optional[Piece]:
        """Get the piece at the given position."""
        return self._board[position.row][position.col]
    
    def set_piece(self, position: Position, piece: Optional[Piece]):
        """Set a piece at the given position."""
        self._board[position.row][position.col] = piece
    
    def remove_piece(self, position: Position) -> Optional[Piece]:
        """Remove and return the piece at the given position."""
        piece = self._board[position.row][position.col]
        self._board[position.row][position.col] = None
        return piece
    
    def move_piece(self, from_pos: Position, to_pos: Position) -> Optional[Piece]:
        """
        Move a piece from one position to another.
        Returns the captured piece if any.
        """
        piece = self.remove_piece(from_pos)
        captured = self.remove_piece(to_pos)
        self.set_piece(to_pos, piece)
        return captured
    
    def find_king(self, color: Color) -> Optional[Position]:
        """Find the position of the king for the given color."""
        for row in range(8):
            for col in range(8):
                piece = self._board[row][col]
                if piece and piece.color == color and piece.piece_type == PieceType.KING:
                    return Position(row, col)
        return None
    
    def get_all_pieces(self, color: Optional[Color] = None) -> List[tuple[Position, Piece]]:
        """
        Get all pieces on the board, optionally filtered by color.
        Returns list of (position, piece) tuples.
        """
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self._board[row][col]
                if piece and (color is None or piece.color == color):
                    pieces.append((Position(row, col), piece))
        return pieces
    
    def is_position_attacked(self, position: Position, by_color: Color) -> bool:
        """
        Check if a position is attacked by any piece of the given color.
        This is used for check detection and castling validation.
        """
        # Check all pieces of the attacking color
        for piece_pos, piece in self.get_all_pieces(by_color):
            # Get possible moves for this piece
            possible_moves = piece.get_possible_moves(piece_pos, self)
            
            # Check if any move targets the position
            for move in possible_moves:
                if move.to_pos == position:
                    # Don't consider castling moves for attack detection
                    if move.move_type not in [move.move_type.CASTLING_KINGSIDE, 
                                             move.move_type.CASTLING_QUEENSIDE]:
                        return True
        
        return False
    
    def copy(self) -> 'Board':
        """Create a deep copy of the board."""
        new_board = Board()
        new_board._board = copy.deepcopy(self._board)
        new_board.castling_rights = self.castling_rights.copy()
        new_board.en_passant_target = self.en_passant_target
        return new_board
    
    def to_string_board(self) -> List[List[Optional[str]]]:
        """
        Convert to old string-based board format for backwards compatibility.
        Returns 8x8 list with strings like 'w_pawn' or None.
        """
        string_board = []
        for row in range(8):
            string_row = []
            for col in range(8):
                piece = self._board[row][col]
                if piece:
                    string_row.append(piece.to_string_notation())
                else:
                    string_row.append(None)
            string_board.append(string_row)
        return string_board
    
    @staticmethod
    def from_string_board(string_board: List[List[Optional[str]]]) -> 'Board':
        """
        Create a Board from old string-based format.
        Accepts 8x8 list with strings like 'w_pawn' or None.
        """
        board = Board()
        for row in range(8):
            for col in range(8):
                piece_str = string_board[row][col]
                if piece_str:
                    board._board[row][col] = piece_from_string(piece_str)
        return board
    
    def __str__(self) -> str:
        """String representation of the board for debugging."""
        result = []
        for row in range(8):
            row_str = f"{8 - row} "
            for col in range(8):
                piece = self._board[row][col]
                if piece:
                    # Use first letter of color and piece type
                    symbol = piece.color.value[0] + piece.piece_type.value[0].upper()
                    row_str += f"{symbol:3}"
                else:
                    row_str += " . "
            result.append(row_str)
        result.append("   a  b  c  d  e  f  g  h")
        return "\n".join(result)
