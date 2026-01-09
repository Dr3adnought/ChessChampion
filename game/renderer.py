"""
Rendering logic separated from game logic.
"""
import pygame
from typing import Dict, Optional

from game.types import Color, Position, GameStatus
from game.board import Board
from game.game_state import GameState


class Renderer:
    """
    Handles all rendering/drawing operations for the chess game.
    Separates visual presentation from game logic.
    """
    
    def __init__(self, screen: pygame.Surface, square_size: int, piece_images: Dict[str, pygame.Surface]):
        """
        Initialize the renderer.
        
        Args:
            screen: Pygame surface to draw on
            square_size: Size of each square in pixels
            piece_images: Dictionary mapping piece names to images
        """
        self.screen = screen
        self.square_size = square_size
        self.piece_images = piece_images
        
        # Colors
        self.light_square_color = (238, 238, 210)
        self.dark_square_color = (118, 150, 86)
        self.highlight_color = (255, 255, 0, 100)
        self.legal_move_color = (100, 200, 100, 80)
        self.last_move_color = (255, 255, 100, 80)
        self.check_color = (255, 50, 50, 120)
        
        # Font for text
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
    
    def draw_board(self, game_state: GameState, legal_moves: Optional[list] = None, last_move: Optional[tuple] = None):
        """
        Draw the complete chess board with pieces.
        
        Args:
            game_state: Current game state
            legal_moves: List of legal move positions to highlight (optional)
            last_move: Tuple of (from_pos, to_pos) for last move highlighting
        """
        self._draw_squares(game_state)
        
        # Highlight last move
        if last_move:
            self._draw_last_move_highlight(last_move)
        
        # Highlight selected square
        if game_state.selected_position:
            self._draw_selected_highlight(game_state.selected_position)
        
        # Highlight legal moves
        if legal_moves:
            self._draw_legal_move_indicators(legal_moves)
        
        # Highlight king in check
        if game_state.game_status == GameStatus.CHECK:
            self._draw_check_highlight(game_state)
        
        # Draw pieces
        self._draw_pieces(game_state.board)
        
        # Draw coordinates
        self._draw_coordinates()
    
    def _draw_squares(self, game_state: GameState):
        """Draw the checkered board pattern."""
        for row in range(8):
            for col in range(8):
                color = self.light_square_color if (row + col) % 2 == 0 else self.dark_square_color
                rect = pygame.Rect(
                    col * self.square_size,
                    row * self.square_size,
                    self.square_size,
                    self.square_size
                )
                pygame.draw.rect(self.screen, color, rect)
    
    def _draw_pieces(self, board: Board):
        """Draw all pieces on the board."""
        for row in range(8):
            for col in range(8):
                position = Position(row, col)
                piece = board.get_piece(position)
                
                if piece:
                    piece_key = piece.to_string_notation()
                    piece_image = self.piece_images.get(piece_key)
                    
                    if piece_image:
                        x = col * self.square_size
                        y = row * self.square_size
                        self.screen.blit(piece_image, (x, y))
    
    def _draw_selected_highlight(self, position: Position):
        """Highlight the selected square."""
        surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
        surface.fill(self.highlight_color)
        x = position.col * self.square_size
        y = position.row * self.square_size
        self.screen.blit(surface, (x, y))
    
    def _draw_legal_move_indicators(self, legal_move_positions: list):
        """Draw indicators for legal move destinations."""
        for position in legal_move_positions:
            surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            
            # Draw a circle in the center for empty squares
            center_x = self.square_size // 2
            center_y = self.square_size // 2
            radius = self.square_size // 6
            pygame.draw.circle(surface, self.legal_move_color, (center_x, center_y), radius)
            
            x = position.col * self.square_size
            y = position.row * self.square_size
            self.screen.blit(surface, (x, y))
    
    def _draw_last_move_highlight(self, last_move: tuple):
        """Highlight the last move made."""
        from_pos, to_pos = last_move
        
        for position in [from_pos, to_pos]:
            surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            surface.fill(self.last_move_color)
            x = position.col * self.square_size
            y = position.row * self.square_size
            self.screen.blit(surface, (x, y))
    
    def _draw_check_highlight(self, game_state: GameState):
        """Highlight the king when in check."""
        king_pos = game_state.board.find_king(game_state.current_turn)
        if king_pos:
            surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            surface.fill(self.check_color)
            x = king_pos.col * self.square_size
            y = king_pos.row * self.square_size
            self.screen.blit(surface, (x, y))
    
    def _draw_coordinates(self):
        """Draw file (a-h) and rank (1-8) labels on the board."""
        # File labels (a-h) at bottom
        for col in range(8):
            label = chr(ord('a') + col)
            text = self.small_font.render(label, True, (100, 100, 100))
            x = col * self.square_size + self.square_size - 20
            y = 7 * self.square_size + self.square_size - 20
            self.screen.blit(text, (x, y))
        
        # Rank labels (1-8) on left
        for row in range(8):
            label = str(8 - row)
            text = self.small_font.render(label, True, (100, 100, 100))
            x = 5
            y = row * self.square_size + 5
            self.screen.blit(text, (x, y))
    
    def draw_game_over_message(self, game_state: GameState):
        """Draw game over message on the screen."""
        if not game_state.is_game_over():
            return
        
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Determine message
        if game_state.game_status == GameStatus.CHECKMATE:
            winner = game_state.get_winner()
            message = f"Checkmate! {winner.value.capitalize()} wins!"
        elif game_state.game_status == GameStatus.STALEMATE:
            message = "Stalemate! It's a draw!"
        elif game_state.game_status == GameStatus.DRAW:
            message = "Draw by 50-move rule!"
        else:
            message = "Game Over!"
        
        # Render text
        text = self.font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(text, text_rect)
    
    def draw_turn_indicator(self, game_state: GameState):
        """Draw an indicator showing whose turn it is."""
        if game_state.is_game_over():
            return
        
        turn_text = f"{game_state.current_turn.value.capitalize()}'s turn"
        text = self.small_font.render(turn_text, True, (50, 50, 50))
        
        # Draw at top of screen
        self.screen.blit(text, (10, 10))
    
    def set_colors(self, light_square: tuple, dark_square: tuple, highlight: tuple):
        """Set custom board colors."""
        self.light_square_color = light_square
        self.dark_square_color = dark_square
        self.highlight_color = highlight
