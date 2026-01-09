"""
Main chess game controller coordinating all components.
This is the refactored version using clean architecture.
"""
import pygame
from typing import Optional, List

from game.types import Color, Position, Move, GameStatus, MoveType, PieceType
from game.board import Board
from game.game_state import GameState
from game.renderer import Renderer


class ChessGame:
    """
    Main game controller that coordinates the board, game state, and rendering.
    Acts as the facade for the chess game system.
    """
    
    def __init__(self):
        """Initialize the chess game with all components."""
        # Create board and set up pieces
        self.board = Board()
        self.board.setup_initial_position()
        
        # Create game state
        self.game_state = GameState(self.board)
        
        # Renderer will be set later when screen is available
        self.renderer: Optional[Renderer] = None
        
        # Track last move for highlighting
        self.last_move: Optional[tuple[Position, Position]] = None
    
    def set_renderer(self, renderer: Renderer):
        """Set the renderer for drawing the game."""
        self.renderer = renderer
    
    @property
    def turn(self) -> str:
        """Get current turn as string for backwards compatibility."""
        return self.game_state.current_turn.value
    
    @property
    def game_over(self) -> bool:
        """Check if game is over."""
        return self.game_state.is_game_over()

    
    def handle_click(self, clicked_row: int, clicked_col: int, ai_player_color: Optional[str] = None):
        """
        Handle mouse click on the board.
        
        Args:
            clicked_row: Row that was clicked (0-7)
            clicked_col: Column that was clicked (0-7)
            ai_player_color: If set, prevents interaction when it's AI's turn
        """
        if self.game_state.is_game_over():
            print("Game is over!")
            return
        
        # Prevent interaction during AI turn
        if ai_player_color and self.turn == ai_player_color:
            return
        
        clicked_position = Position(clicked_row, clicked_col)
        piece_at_click = self.board.get_piece(clicked_position)
        
        # If we have a piece selected, try to move it
        if self.game_state.selected_position:
            # Check if move is legal
            legal_moves = self.game_state.get_legal_moves_for_position(self.game_state.selected_position)
            target_move = None
            
            for move in legal_moves:
                if move.to_pos == clicked_position:
                    # Handle pawn promotion - default to queen for now
                    if move.move_type == MoveType.PROMOTION:
                        # If there are multiple promotion options, pick queen
                        if move.promotion_piece == PieceType.QUEEN:
                            target_move = move
                            break
                    else:
                        target_move = move
                        break
            
            if target_move:
                # Get piece type before move for notation
                piece = self.board.get_piece(target_move.from_pos)
                piece_type = piece.piece_type if piece else None
                
                # Execute the move
                if self.game_state.make_move(target_move):
                    self.last_move = (target_move.from_pos, target_move.to_pos)
                    if piece_type:
                        print(f"Move: {self.game_state.get_move_notation(target_move, piece_type)}")
                    
                    # Check game status
                    if self.game_state.game_status == GameStatus.CHECKMATE:
                        winner = self.game_state.get_winner()
                        print(f"\n!!! CHECKMATE !!! {winner.value.upper()} WINS!")
                    elif self.game_state.game_status == GameStatus.STALEMATE:
                        print("\n!!! STALEMATE !!! It's a DRAW!")
                    elif self.game_state.game_status == GameStatus.CHECK:
                        print(f"!!! {self.game_state.current_turn.value.upper()} KING IS IN CHECK !!!")
                    elif self.game_state.game_status == GameStatus.DRAW:
                        print("\n!!! DRAW by 50-move rule!")
                    
                    self.game_state.selected_position = None
                else:
                    print("Move failed")
            else:
                # Not a valid move, check if clicking another piece of same color
                if piece_at_click and piece_at_click.color.value == self.turn:
                    self.game_state.selected_position = clicked_position
                else:
                    self.game_state.selected_position = None
        else:
            # No piece selected, try to select one
            if piece_at_click and piece_at_click.color.value == self.turn:
                self.game_state.selected_position = clicked_position
            else:
                print(f"It's {self.turn}'s turn. Cannot select opponent's piece or empty square.")
    
    def draw(self, screen: pygame.Surface, square_size: int, light_color: tuple, dark_color: tuple,
             highlight_color: tuple, pieces_images: dict):
        """
        Draw the game board. Backwards compatible with old interface.
        
        Args:
            screen: Pygame screen surface
            square_size: Size of each square
            light_color: Light square color
            dark_color: Dark square color
            highlight_color: Highlight color for selected square
            pieces_images: Dictionary of piece images
        """
        # Create renderer if not exists
        if self.renderer is None:
            self.renderer = Renderer(screen, square_size, pieces_images)
            self.renderer.set_colors(light_color, dark_color, highlight_color)
        
        # Get legal moves for selected piece
        legal_move_positions = []
        if self.game_state.selected_position:
            legal_moves = self.game_state.get_legal_moves_for_position(self.game_state.selected_position)
            legal_move_positions = [move.to_pos for move in legal_moves]
        
        # Draw the board
        self.renderer.draw_board(self.game_state, legal_move_positions, self.last_move)
        
        # Draw game over message if applicable
        if self.game_state.is_game_over():
            self.renderer.draw_game_over_message(self.game_state)
    
    def get_all_legal_moves(self, color_str: str) -> List[tuple]:
        """
        Get all legal moves for a color (backwards compatible).
        
        Args:
            color_str: 'white' or 'black'
        
        Returns:
            List of ((start_row, start_col), (end_row, end_col)) tuples
        """
        color = Color.WHITE if color_str == 'white' else Color.BLACK
        moves = self.game_state.validator.get_all_legal_moves(color)
        
        # Convert to old format
        return [((m.from_pos.row, m.from_pos.col), (m.to_pos.row, m.to_pos.col)) for m in moves]
    
    def move_piece(self, start_row: int, start_col: int, end_row: int, end_col: int):
        """
        Move a piece (for AI compatibility).
        
        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
        """
        from_pos = Position(start_row, start_col)
        to_pos = Position(end_row, end_col)
        
        # Find the matching legal move
        legal_moves = self.game_state.get_legal_moves_for_position(from_pos)
        
        for move in legal_moves:
            if move.to_pos == to_pos:
                # For promotions, default to queen
                if move.move_type == MoveType.PROMOTION and move.promotion_piece == PieceType.QUEEN:
                    if self.game_state.make_move(move):
                        self.last_move = (from_pos, to_pos)
                        return
                elif move.move_type != MoveType.PROMOTION:
                    if self.game_state.make_move(move):
                        self.last_move = (from_pos, to_pos)
                        return
    
    def check_game_end_conditions(self):
        """Check game end conditions (for AI compatibility)."""
        # Game state automatically updates status after moves
        pass
    
    def is_valid_move(self, start_row: int, start_col: int, end_row: int, end_col: int) -> bool:
        """
        Check if a move is valid (for AI compatibility).
        
        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
        
        Returns:
            True if move is legal
        """
        from_pos = Position(start_row, start_col)
        to_pos = Position(end_row, end_col)
        
        legal_moves = self.game_state.get_legal_moves_for_position(from_pos)
        
        for move in legal_moves:
            if move.to_pos == to_pos:
                return True
        
        return False
