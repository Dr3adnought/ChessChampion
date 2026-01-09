"""
Core data types and enums for the chess game.
"""
from enum import Enum, auto
from typing import Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from game.pieces import Piece


class Color(Enum):
    """Represents piece colors."""
    WHITE = "white"
    BLACK = "black"
    
    def opposite(self) -> 'Color':
        """Returns the opposite color."""
        return Color.BLACK if self == Color.WHITE else Color.WHITE
    
    def __str__(self) -> str:
        return self.value


class PieceType(Enum):
    """Represents chess piece types."""
    PAWN = "pawn"
    ROOK = "rook"
    KNIGHT = "knight"
    BISHOP = "bishop"
    QUEEN = "queen"
    KING = "king"
    
    def __str__(self) -> str:
        return self.value


class GameStatus(Enum):
    """Represents the current status of the game."""
    ACTIVE = auto()
    CHECK = auto()
    CHECKMATE = auto()
    STALEMATE = auto()
    DRAW = auto()


class MoveType(Enum):
    """Represents special move types."""
    NORMAL = auto()
    CAPTURE = auto()
    CASTLING_KINGSIDE = auto()
    CASTLING_QUEENSIDE = auto()
    EN_PASSANT = auto()
    PROMOTION = auto()
    PAWN_DOUBLE = auto()


@dataclass(frozen=True)
class Position:
    """
    Represents a position on the chess board.
    Row and column are 0-indexed (0-7).
    """
    row: int
    col: int
    
    def __post_init__(self):
        if not (0 <= self.row < 8 and 0 <= self.col < 8):
            raise ValueError(f"Invalid position: ({self.row}, {self.col})")
    
    def to_algebraic(self) -> str:
        """Convert to algebraic notation (e.g., 'e4')."""
        return f"{chr(ord('a') + self.col)}{8 - self.row}"
    
    @staticmethod
    def from_algebraic(notation: str) -> 'Position':
        """Create Position from algebraic notation (e.g., 'e4')."""
        if len(notation) != 2:
            raise ValueError(f"Invalid algebraic notation: {notation}")
        col = ord(notation[0].lower()) - ord('a')
        row = 8 - int(notation[1])
        return Position(row, col)
    
    def __str__(self) -> str:
        return self.to_algebraic()


@dataclass
class Move:
    """
    Represents a chess move with all necessary information.
    """
    from_pos: Position
    to_pos: Position
    move_type: MoveType = MoveType.NORMAL
    promotion_piece: Optional[PieceType] = None
    captured_piece: Optional['Piece'] = None
    
    def to_algebraic(self, piece_type: PieceType, is_capture: bool = False) -> str:
        """Convert move to algebraic notation."""
        piece_symbol = '' if piece_type == PieceType.PAWN else piece_type.value[0].upper()
        capture_symbol = 'x' if is_capture else ''
        
        if self.move_type == MoveType.CASTLING_KINGSIDE:
            return "O-O"
        elif self.move_type == MoveType.CASTLING_QUEENSIDE:
            return "O-O-O"
        
        promotion = f"={self.promotion_piece.value[0].upper()}" if self.promotion_piece else ""
        return f"{piece_symbol}{capture_symbol}{self.to_pos.to_algebraic()}{promotion}"
    
    def __str__(self) -> str:
        return f"{self.from_pos} -> {self.to_pos}"


class CastlingRights:
    """Tracks castling rights for both players using bit flags."""
    
    WHITE_KINGSIDE = 0b0001
    WHITE_QUEENSIDE = 0b0010
    BLACK_KINGSIDE = 0b0100
    BLACK_QUEENSIDE = 0b1000
    
    def __init__(self, rights: int = 0b1111):
        """Initialize with all castling rights by default."""
        self._rights = rights
    
    def can_castle(self, color: Color, kingside: bool) -> bool:
        """Check if castling is allowed for the given color and side."""
        if color == Color.WHITE:
            flag = self.WHITE_KINGSIDE if kingside else self.WHITE_QUEENSIDE
        else:
            flag = self.BLACK_KINGSIDE if kingside else self.BLACK_QUEENSIDE
        return bool(self._rights & flag)
    
    def remove_rights(self, color: Color, kingside: Optional[bool] = None):
        """Remove castling rights. If kingside is None, remove both."""
        if kingside is None:
            # Remove both sides for this color
            if color == Color.WHITE:
                self._rights &= ~(self.WHITE_KINGSIDE | self.WHITE_QUEENSIDE)
            else:
                self._rights &= ~(self.BLACK_KINGSIDE | self.BLACK_QUEENSIDE)
        else:
            if color == Color.WHITE:
                flag = self.WHITE_KINGSIDE if kingside else self.WHITE_QUEENSIDE
            else:
                flag = self.BLACK_KINGSIDE if kingside else self.BLACK_QUEENSIDE
            self._rights &= ~flag
    
    def copy(self) -> 'CastlingRights':
        """Create a copy of the castling rights."""
        return CastlingRights(self._rights)
    
    def __str__(self) -> str:
        """FEN-style castling rights string."""
        result = ""
        if self._rights & self.WHITE_KINGSIDE:
            result += "K"
        if self._rights & self.WHITE_QUEENSIDE:
            result += "Q"
        if self._rights & self.BLACK_KINGSIDE:
            result += "k"
        if self._rights & self.BLACK_QUEENSIDE:
            result += "q"
        return result or "-"
