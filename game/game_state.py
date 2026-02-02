"""
Game state management including turn tracking, move history, and game status.
"""
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from game.types import Color, Position, Move, GameStatus, MoveType, PieceType
from game.board import Board
from game.move_validator import MoveValidator
from game.pieces import create_piece

if TYPE_CHECKING:
    from game.pieces import Piece


@dataclass
class GameState:
    """
    Tracks the complete state of a chess game including:
    - Current turn
    - Move history
    - Game status (active, check, checkmate, stalemate)
    - Half-move clock (for 50-move rule)
    - Full move number
    - Captured pieces
    """
    board: Board
    current_turn: Color = Color.WHITE
    move_history: List[Move] = field(default_factory=list)
    game_status: GameStatus = GameStatus.ACTIVE
    half_move_clock: int = 0  # For 50-move rule
    full_move_number: int = 1
    selected_position: Optional[Position] = None
    captured_by_white: List[PieceType] = field(default_factory=list)  # Pieces captured by white
    captured_by_black: List[PieceType] = field(default_factory=list)  # Pieces captured by black
    
    def __post_init__(self):
        """Initialize the validator after the state is created."""
        self.validator = MoveValidator(self.board)
    
    def make_move(self, move: Move) -> bool:
        """
        Execute a move if it's legal.
        Returns True if move was successful, False otherwise.
        """
        # Verify it's the correct player's turn
        piece = self.board.get_piece(move.from_pos)
        if piece is None or piece.color != self.current_turn:
            return False
        
        # Verify move is legal
        if not self.validator.is_move_legal(move):
            return False
        
        # Execute the move
        self._execute_move(move)
        
        # Add to history
        self.move_history.append(move)
        
        # Update half-move clock
        if piece.piece_type == PieceType.PAWN or move.move_type == MoveType.CAPTURE:
            self.half_move_clock = 0
        else:
            self.half_move_clock += 1
        
        # Update full move number (increments after black's move)
        if self.current_turn == Color.BLACK:
            self.full_move_number += 1
        
        # Switch turns
        self.current_turn = self.current_turn.opposite()
        
        # Update validator for new board state
        self.validator = MoveValidator(self.board)
        
        # Update game status
        self._update_game_status()
        
        return True
    
    def _execute_move(self, move: Move):
        """Execute a move on the board, handling all special cases."""
        piece = self.board.get_piece(move.from_pos)
        
        # Track captured pieces
        if move.move_type == MoveType.CAPTURE or move.move_type == MoveType.PROMOTION:
            captured_piece = self.board.get_piece(move.to_pos)
            if captured_piece:
                if piece.color == Color.WHITE:
                    self.captured_by_white.append(captured_piece.piece_type)
                else:
                    self.captured_by_black.append(captured_piece.piece_type)
        
        # Clear en passant target from previous move
        self.board.en_passant_target = None
        
        # Dispatch to appropriate handler based on move type
        move_handlers = {
            MoveType.CASTLING_KINGSIDE: self._execute_castling_kingside,
            MoveType.CASTLING_QUEENSIDE: self._execute_castling_queenside,
            MoveType.EN_PASSANT: self._execute_en_passant,
            MoveType.PROMOTION: self._execute_promotion,
            MoveType.PAWN_DOUBLE: self._execute_pawn_double,
        }
        
        handler = move_handlers.get(move.move_type)
        if handler:
            handler(move, piece)
        else:
            # Normal move or capture
            self.board.move_piece(move.from_pos, move.to_pos)
        
        # Update castling rights based on piece movement
        self._update_castling_rights(move, piece)
    
    def _execute_castling_kingside(self, move: Move, piece: 'Piece'):
        """Execute kingside castling."""
        row = move.from_pos.row
        self.board.move_piece(move.from_pos, move.to_pos)  # Move king
        self.board.move_piece(Position(row, 7), Position(row, 5))  # Move rook
        self.board.castling_rights.remove_rights(piece.color)
    
    def _execute_castling_queenside(self, move: Move, piece: 'Piece'):
        """Execute queenside castling."""
        row = move.from_pos.row
        self.board.move_piece(move.from_pos, move.to_pos)  # Move king
        self.board.move_piece(Position(row, 0), Position(row, 3))  # Move rook
        self.board.castling_rights.remove_rights(piece.color)
    
    def _execute_en_passant(self, move: Move, piece: 'Piece'):
        """Execute en passant capture."""
        # Track captured pawn
        captured_pawn_pos = Position(move.from_pos.row, move.to_pos.col)
        captured_pawn = self.board.get_piece(captured_pawn_pos)
        if captured_pawn:
            if piece.color == Color.WHITE:
                self.captured_by_white.append(captured_pawn.piece_type)
            else:
                self.captured_by_black.append(captured_pawn.piece_type)
        
        self.board.move_piece(move.from_pos, move.to_pos)
        self.board.remove_piece(captured_pawn_pos)
    
    def _execute_promotion(self, move: Move, piece: 'Piece'):
        """Execute pawn promotion."""
        self.board.remove_piece(move.from_pos)
        promoted_piece = create_piece(piece.color, move.promotion_piece)
        self.board.set_piece(move.to_pos, promoted_piece)
    
    def _execute_pawn_double(self, move: Move, piece: 'Piece'):
        """Execute pawn double move and set en passant target."""
        self.board.move_piece(move.from_pos, move.to_pos)
        direction = -1 if piece.color == Color.WHITE else 1
        en_passant_row = move.from_pos.row + direction
        self.board.en_passant_target = Position(en_passant_row, move.from_pos.col)
    
    def _update_castling_rights(self, move: Move, piece: 'Piece'):
        """Update castling rights based on piece movement."""
        if piece.piece_type == PieceType.KING:
            self.board.castling_rights.remove_rights(piece.color)
        elif piece.piece_type == PieceType.ROOK:
            # Check if it's a corner rook
            if move.from_pos.col == 0:  # Queenside rook
                self.board.castling_rights.remove_rights(piece.color, False)
            elif move.from_pos.col == 7:  # Kingside rook
                self.board.castling_rights.remove_rights(piece.color, True)
    
    def _update_game_status(self):
        """Update the game status based on the current position."""
        # Check for checkmate/stalemate
        if not self.validator.has_legal_moves(self.current_turn):
            if self.validator.is_king_in_check(self.current_turn):
                self.game_status = GameStatus.CHECKMATE
            else:
                self.game_status = GameStatus.STALEMATE
        elif self.validator.is_king_in_check(self.current_turn):
            self.game_status = GameStatus.CHECK
        elif self.half_move_clock >= 100:  # 50-move rule (100 half-moves)
            self.game_status = GameStatus.DRAW
        else:
            self.game_status = GameStatus.ACTIVE
    
    def get_legal_moves_for_position(self, position: Position) -> List[Move]:
        """Get all legal moves for a piece at the given position."""
        return self.validator.get_legal_moves(position)
    
    def get_all_legal_moves(self) -> List[Move]:
        """Get all legal moves for the current player."""
        return self.validator.get_all_legal_moves(self.current_turn)
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.game_status in [GameStatus.CHECKMATE, GameStatus.STALEMATE, GameStatus.DRAW]
    
    def get_winner(self) -> Optional[Color]:
        """Get the winner if game is over by checkmate."""
        if self.game_status == GameStatus.CHECKMATE:
            return self.current_turn.opposite()
        return None
    
    def copy(self) -> 'GameState':
        """Create a deep copy of the game state."""
        new_state = GameState(
            board=self.board.copy(),
            current_turn=self.current_turn,
            move_history=self.move_history.copy(),
            game_status=self.game_status,
            half_move_clock=self.half_move_clock,
            full_move_number=self.full_move_number,
            selected_position=self.selected_position
        )
        return new_state
    
    def get_move_notation(self, move: Move, piece_type: Optional[PieceType] = None) -> str:
        """Get algebraic notation for a move."""
        # If piece_type not provided, try to get it from the destination (after move)
        if piece_type is None:
            piece = self.board.get_piece(move.to_pos)
            if piece:
                piece_type = piece.piece_type
            else:
                return "??"  # Unknown move
        
        is_capture = move.move_type == MoveType.CAPTURE or move.captured_piece is not None
        notation = move.to_algebraic(piece_type, is_capture)
        
        # Add check/checkmate symbol
        if self.game_status == GameStatus.CHECKMATE:
            notation += "#"
        elif self.game_status == GameStatus.CHECK:
            notation += "+"
        
        return notation
