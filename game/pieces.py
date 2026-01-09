"""
Chess piece classes with their movement logic.
"""
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

from game.types import Color, PieceType, Position, Move, MoveType

if TYPE_CHECKING:
    from game.board import Board


class Piece(ABC):
    """Abstract base class for all chess pieces."""
    
    def __init__(self, color: Color, piece_type: PieceType):
        self.color = color
        self.piece_type = piece_type
    
    @abstractmethod
    def get_possible_moves(self, position: Position, board: 'Board') -> List[Move]:
        """
        Get all possible moves for this piece from the given position.
        This does not check for check/checkmate - just raw piece movement.
        """
        pass
    
    def get_piece_value(self) -> int:
        """Get the material value of this piece."""
        values = {
            PieceType.PAWN: 100,
            PieceType.KNIGHT: 320,
            PieceType.BISHOP: 330,
            PieceType.ROOK: 500,
            PieceType.QUEEN: 900,
            PieceType.KING: 20000
        }
        return values[self.piece_type]
    
    def to_string_notation(self) -> str:
        """Convert to string notation like 'w_pawn' for compatibility."""
        return f"{self.color.value[0]}_{ self.piece_type.value}"
    
    def __str__(self) -> str:
        return f"{self.color.value.capitalize()} {self.piece_type.value.capitalize()}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.color}, {self.piece_type})"


class Pawn(Piece):
    """Pawn piece with its unique movement rules."""
    
    def __init__(self, color: Color):
        super().__init__(color, PieceType.PAWN)
    
    def get_possible_moves(self, position: Position, board: 'Board') -> List[Move]:
        moves = []
        direction = -1 if self.color == Color.WHITE else 1
        start_row = 6 if self.color == Color.WHITE else 1
        
        # Single square forward
        new_row = position.row + direction
        if 0 <= new_row < 8:
            forward_pos = Position(new_row, position.col)
            if board.get_piece(forward_pos) is None:
                # Check for promotion
                if new_row == 0 or new_row == 7:
                    for promo_piece in [PieceType.QUEEN, PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP]:
                        moves.append(Move(position, forward_pos, MoveType.PROMOTION, promo_piece))
                else:
                    moves.append(Move(position, forward_pos, MoveType.NORMAL))
                
                # Double square forward from starting position
                if position.row == start_row:
                    double_row = position.row + 2 * direction
                    double_pos = Position(double_row, position.col)
                    if board.get_piece(double_pos) is None:
                        moves.append(Move(position, double_pos, MoveType.PAWN_DOUBLE))
        
        # Captures (diagonal)
        for col_delta in [-1, 1]:
            new_col = position.col + col_delta
            new_row = position.row + direction
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                capture_pos = Position(new_row, new_col)
                target_piece = board.get_piece(capture_pos)
                
                # Normal capture
                if target_piece and target_piece.color != self.color:
                    if new_row == 0 or new_row == 7:
                        for promo_piece in [PieceType.QUEEN, PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP]:
                            moves.append(Move(position, capture_pos, MoveType.PROMOTION, promo_piece, target_piece))
                    else:
                        moves.append(Move(position, capture_pos, MoveType.CAPTURE, captured_piece=target_piece))
                
                # En passant
                elif target_piece is None and board.en_passant_target == capture_pos:
                    en_passant_pawn_pos = Position(position.row, new_col)
                    en_passant_pawn = board.get_piece(en_passant_pawn_pos)
                    moves.append(Move(position, capture_pos, MoveType.EN_PASSANT, captured_piece=en_passant_pawn))
        
        return moves


class Rook(Piece):
    """Rook piece - moves horizontally and vertically."""
    
    def __init__(self, color: Color):
        super().__init__(color, PieceType.ROOK)
    
    def get_possible_moves(self, position: Position, board: 'Board') -> List[Move]:
        moves = []
        
        # Horizontal and vertical directions
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            new_row, new_col = position.row + dr, position.col + dc
            
            while 0 <= new_row < 8 and 0 <= new_col < 8:
                new_pos = Position(new_row, new_col)
                target_piece = board.get_piece(new_pos)
                
                if target_piece is None:
                    moves.append(Move(position, new_pos, MoveType.NORMAL))
                elif target_piece.color != self.color:
                    moves.append(Move(position, new_pos, MoveType.CAPTURE, captured_piece=target_piece))
                    break
                else:
                    break
                
                new_row += dr
                new_col += dc
        
        return moves


class Knight(Piece):
    """Knight piece - moves in L-shape."""
    
    def __init__(self, color: Color):
        super().__init__(color, PieceType.KNIGHT)
    
    def get_possible_moves(self, position: Position, board: 'Board') -> List[Move]:
        moves = []
        
        # All possible L-shaped moves
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for dr, dc in knight_moves:
            new_row = position.row + dr
            new_col = position.col + dc
            
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                new_pos = Position(new_row, new_col)
                target_piece = board.get_piece(new_pos)
                
                if target_piece is None:
                    moves.append(Move(position, new_pos, MoveType.NORMAL))
                elif target_piece.color != self.color:
                    moves.append(Move(position, new_pos, MoveType.CAPTURE, captured_piece=target_piece))
        
        return moves


class Bishop(Piece):
    """Bishop piece - moves diagonally."""
    
    def __init__(self, color: Color):
        super().__init__(color, PieceType.BISHOP)
    
    def get_possible_moves(self, position: Position, board: 'Board') -> List[Move]:
        moves = []
        
        # Diagonal directions
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for dr, dc in directions:
            new_row, new_col = position.row + dr, position.col + dc
            
            while 0 <= new_row < 8 and 0 <= new_col < 8:
                new_pos = Position(new_row, new_col)
                target_piece = board.get_piece(new_pos)
                
                if target_piece is None:
                    moves.append(Move(position, new_pos, MoveType.NORMAL))
                elif target_piece.color != self.color:
                    moves.append(Move(position, new_pos, MoveType.CAPTURE, captured_piece=target_piece))
                    break
                else:
                    break
                
                new_row += dr
                new_col += dc
        
        return moves


class Queen(Piece):
    """Queen piece - combines rook and bishop movement."""
    
    def __init__(self, color: Color):
        super().__init__(color, PieceType.QUEEN)
    
    def get_possible_moves(self, position: Position, board: 'Board') -> List[Move]:
        moves = []
        
        # Combination of rook and bishop directions
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),  # Rook-like
            (1, 1), (1, -1), (-1, 1), (-1, -1)  # Bishop-like
        ]
        
        for dr, dc in directions:
            new_row, new_col = position.row + dr, position.col + dc
            
            while 0 <= new_row < 8 and 0 <= new_col < 8:
                new_pos = Position(new_row, new_col)
                target_piece = board.get_piece(new_pos)
                
                if target_piece is None:
                    moves.append(Move(position, new_pos, MoveType.NORMAL))
                elif target_piece.color != self.color:
                    moves.append(Move(position, new_pos, MoveType.CAPTURE, captured_piece=target_piece))
                    break
                else:
                    break
                
                new_row += dr
                new_col += dc
        
        return moves


class King(Piece):
    """King piece - moves one square in any direction."""
    
    def __init__(self, color: Color):
        super().__init__(color, PieceType.KING)
    
    def get_possible_moves(self, position: Position, board: 'Board') -> List[Move]:
        moves = []
        
        # One square in all directions
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        for dr, dc in directions:
            new_row = position.row + dr
            new_col = position.col + dc
            
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                new_pos = Position(new_row, new_col)
                target_piece = board.get_piece(new_pos)
                
                if target_piece is None:
                    moves.append(Move(position, new_pos, MoveType.NORMAL))
                elif target_piece.color != self.color:
                    moves.append(Move(position, new_pos, MoveType.CAPTURE, captured_piece=target_piece))
        
        # Castling moves (will be validated separately)
        # Kingside
        if board.castling_rights.can_castle(self.color, True):
            castling_col = position.col + 2
            if 0 <= castling_col < 8:
                castling_pos = Position(position.row, castling_col)
                moves.append(Move(position, castling_pos, MoveType.CASTLING_KINGSIDE))
        
        # Queenside
        if board.castling_rights.can_castle(self.color, False):
            castling_col = position.col - 2
            if 0 <= castling_col < 8:
                castling_pos = Position(position.row, castling_col)
                moves.append(Move(position, castling_pos, MoveType.CASTLING_QUEENSIDE))
        
        return moves


def create_piece(color: Color, piece_type: PieceType) -> Piece:
    """Factory function to create pieces."""
    piece_classes = {
        PieceType.PAWN: Pawn,
        PieceType.ROOK: Rook,
        PieceType.KNIGHT: Knight,
        PieceType.BISHOP: Bishop,
        PieceType.QUEEN: Queen,
        PieceType.KING: King
    }
    return piece_classes[piece_type](color)


def piece_from_string(piece_str: str) -> Piece:
    """Create a piece from string notation like 'w_pawn'."""
    color_char, piece_name = piece_str.split('_')
    color = Color.WHITE if color_char == 'w' else Color.BLACK
    piece_type = PieceType(piece_name)
    return create_piece(color, piece_type)
