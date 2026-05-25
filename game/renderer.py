"""
Rendering logic separated from game logic.
"""
import pygame
from typing import Dict, Optional, List

from game.types import Color, Position, GameStatus, PieceType
from game.board import Board
from game.game_state import GameState
from game.timer import TimeControl


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
        
        # Undo/Redo button rectangles
        self.undo_button_rect = None
        self.redo_button_rect = None

        # Save/Load button rectangles
        self.save_button_rect = None
        self.load_button_rect = None
        self.reconnect_button_rect = None
    
    def draw_board(self, game_state: GameState, legal_moves: Optional[list] = None, 
                   last_move: Optional[tuple] = None, animating_position: Optional[Position] = None):
        """
        Draw the complete chess board with pieces.
        
        Args:
            game_state: Current game state
            legal_moves: List of legal move positions to highlight (optional)
            last_move: Tuple of (from_pos, to_pos) for last move highlighting
            animating_position: Position to exclude from drawing (for animation)
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
        
        # Draw pieces (excluding animated piece)
        self._draw_pieces(game_state.board, exclude_position=animating_position)
        
        # Draw coordinates
        self._draw_coordinates()
    
    def draw_timers(self, timer: TimeControl, sidebar_x: int, sidebar_width: int, current_turn: Color):
        """
        Draw chess timers for both players in the sidebar.
        
        Args:
            timer: TimeControl object with time information
            sidebar_x: X position where sidebar starts
            sidebar_width: Width of the sidebar
            current_turn: Current player's turn for highlighting
        """
        if not timer.is_timed:
            return
        
        timer_font = pygame.font.Font(None, 48)
        label_font = pygame.font.Font(None, 24)
        
        # Calculate positions (at top of sidebar, above captured pieces section)
        black_timer_y = 180
        white_timer_y = black_timer_y + 80
        
        # Draw Black's timer
        black_time_str = timer.format_time(Color.BLACK)
        black_color = timer.get_display_color(Color.BLACK)
        black_bg = (40, 40, 40) if current_turn == Color.BLACK else (30, 30, 30)
        
        # Background rectangle for black timer
        black_bg_rect = pygame.Rect(sidebar_x + 10, black_timer_y - 10, sidebar_width - 20, 60)
        pygame.draw.rect(self.screen, black_bg, black_bg_rect, border_radius=8)
        if current_turn == Color.BLACK:
            pygame.draw.rect(self.screen, (100, 100, 100), black_bg_rect, width=2, border_radius=8)
        
        # Black label
        black_label = label_font.render("Black", True, (200, 200, 200))
        self.screen.blit(black_label, (sidebar_x + 20, black_timer_y))
        
        # Black time
        black_time_surface = timer_font.render(black_time_str, True, black_color)
        black_time_rect = black_time_surface.get_rect(centerx=sidebar_x + sidebar_width // 2, y=black_timer_y + 15)
        self.screen.blit(black_time_surface, black_time_rect)
        
        # Draw White's timer
        white_time_str = timer.format_time(Color.WHITE)
        white_color = timer.get_display_color(Color.WHITE)
        white_bg = (40, 40, 40) if current_turn == Color.WHITE else (30, 30, 30)
        
        # Background rectangle for white timer
        white_bg_rect = pygame.Rect(sidebar_x + 10, white_timer_y - 10, sidebar_width - 20, 60)
        pygame.draw.rect(self.screen, white_bg, white_bg_rect, border_radius=8)
        if current_turn == Color.WHITE:
            pygame.draw.rect(self.screen, (100, 100, 100), white_bg_rect, width=2, border_radius=8)
        
        # White label
        white_label = label_font.render("White", True, (200, 200, 200))
        self.screen.blit(white_label, (sidebar_x + 20, white_timer_y))
        
        # White time
        white_time_surface = timer_font.render(white_time_str, True, white_color)
        white_time_rect = white_time_surface.get_rect(centerx=sidebar_x + sidebar_width // 2, y=white_timer_y + 15)
        self.screen.blit(white_time_surface, white_time_rect)
    
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
    
    def _draw_pieces(self, board: Board, exclude_position: Optional[Position] = None):
        """
        Draw all pieces on the board.
        
        Args:
            board: The board to draw pieces from
            exclude_position: Optional position to skip (for animated piece)
        """
        for row in range(8):
            for col in range(8):
                position = Position(row, col)
                
                # Skip the animated piece position
                if exclude_position and position == exclude_position:
                    continue
                
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
    
    def draw_captured_pieces_sidebar(self, game_state: GameState, sidebar_x: int, sidebar_width: int):
        """
        Draw the captured pieces sidebar.
        
        Args:
            game_state: Current game state with captured pieces
            sidebar_x: X position where sidebar starts
            sidebar_width: Width of the sidebar
        """
        # Background for sidebar
        sidebar_bg_color = (50, 50, 50)
        sidebar_rect = pygame.Rect(sidebar_x, 0, sidebar_width, self.screen.get_height())
        pygame.draw.rect(self.screen, sidebar_bg_color, sidebar_rect)
        
        # Draw title
        title_font = pygame.font.Font(None, 28)
        title = title_font.render("Captured Pieces", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=sidebar_x + sidebar_width // 2, y=20)
        self.screen.blit(title, title_rect)
        
        # Piece values for material count
        piece_values = {
            PieceType.PAWN: 1,
            PieceType.KNIGHT: 3,
            PieceType.BISHOP: 3,
            PieceType.ROOK: 5,
            PieceType.QUEEN: 9,
        }
        
        # Draw pieces captured by white (black pieces)
        y_offset = 70
        label = self.small_font.render("By White:", True, (200, 200, 200))
        self.screen.blit(label, (sidebar_x + 10, y_offset))
        y_offset += 30
        
        captured_by_white_sorted = sorted(game_state.captured_by_white, 
                                         key=lambda p: piece_values.get(p, 0), reverse=True)
        y_offset = self._draw_captured_pieces_list(captured_by_white_sorted, Color.BLACK, 
                                                   sidebar_x, y_offset, sidebar_width)
        
        # Calculate material advantage
        white_material = sum(piece_values.get(p, 0) for p in game_state.captured_by_white)
        black_material = sum(piece_values.get(p, 0) for p in game_state.captured_by_black)
        advantage = white_material - black_material
        
        if advantage > 0:
            adv_text = f"+{advantage}"
            adv_color = (100, 255, 100)
        elif advantage < 0:
            adv_text = f"{advantage}"
            adv_color = (255, 100, 100)
        else:
            adv_text = "="
            adv_color = (200, 200, 200)
        
        adv_surface = self.small_font.render(adv_text, True, adv_color)
        self.screen.blit(adv_surface, (sidebar_x + sidebar_width - 40, y_offset - 25))
        
        # Draw pieces captured by black (white pieces)
        y_offset += 30
        label = self.small_font.render("By Black:", True, (200, 200, 200))
        self.screen.blit(label, (sidebar_x + 10, y_offset))
        y_offset += 30
        
        captured_by_black_sorted = sorted(game_state.captured_by_black,
                                         key=lambda p: piece_values.get(p, 0), reverse=True)
        self._draw_captured_pieces_list(captured_by_black_sorted, Color.WHITE,
                                       sidebar_x, y_offset, sidebar_width)
    
    def _draw_captured_pieces_list(self, captured_pieces: List[PieceType], piece_color: Color,
                                   sidebar_x: int, y_start: int, sidebar_width: int) -> int:
        """
        Draw a list of captured pieces.
        
        Args:
            captured_pieces: List of captured piece types
            piece_color: Color of the pieces (opposite of capturer)
            sidebar_x: X position of sidebar
            y_start: Starting Y position
            sidebar_width: Width of the sidebar
            
        Returns:
            Final Y position after drawing
        """
        if not captured_pieces:
            no_pieces_text = self.small_font.render("None", True, (120, 120, 120))
            self.screen.blit(no_pieces_text, (sidebar_x + 20, y_start))
            return y_start + 30
        
        # Piece size for sidebar (smaller than board pieces)
        piece_size = 40
        pieces_per_row = (sidebar_width - 20) // piece_size
        
        x = sidebar_x + 10
        y = y_start
        count = 0
        
        for piece_type in captured_pieces:
            # Get piece image
            color_prefix = 'w' if piece_color == Color.WHITE else 'b'
            piece_name_map = {
                PieceType.PAWN: 'pawn',
                PieceType.KNIGHT: 'knight',
                PieceType.BISHOP: 'bishop',
                PieceType.ROOK: 'rook',
                PieceType.QUEEN: 'queen',
            }
            piece_name = f"{color_prefix}_{piece_name_map.get(piece_type, 'pawn')}"
            piece_image = self.piece_images.get(piece_name)
            
            if piece_image:
                # Scale down the piece image
                scaled_image = pygame.transform.scale(piece_image, (piece_size, piece_size))
                self.screen.blit(scaled_image, (x, y))
            
            x += piece_size
            count += 1
            
            # Move to next row if needed
            if count % pieces_per_row == 0:
                x = sidebar_x + 10
                y += piece_size
        
        return y + piece_size + 10
    
    def draw_undo_redo_buttons(self, game_state: GameState, sidebar_x: int, sidebar_width: int, board_height: int):
        """
        Draw undo and redo buttons in the sidebar.
        
        Args:
            game_state: Current game state to check if undo/redo available
            sidebar_x: X position where sidebar starts
            sidebar_width: Width of the sidebar
            board_height: Height of the board for positioning
        """
        button_width = (sidebar_width - 30) // 2
        button_height = 40
        spacing = 10
        y_pos = board_height - 60
        
        # Undo button
        undo_x = sidebar_x + 10
        self.undo_button_rect = pygame.Rect(undo_x, y_pos, button_width, button_height)
        
        # Color based on availability
        if game_state.can_undo():
            undo_color = (70, 130, 180)  # Blue when active
            text_color = (255, 255, 255)
        else:
            undo_color = (100, 100, 100)  # Gray when disabled
            text_color = (150, 150, 150)
        
        pygame.draw.rect(self.screen, undo_color, self.undo_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0, 0, 0), self.undo_button_rect, width=2, border_radius=5)
        
        undo_text = self.small_font.render("Undo", True, text_color)
        undo_text_rect = undo_text.get_rect(center=self.undo_button_rect.center)
        self.screen.blit(undo_text, undo_text_rect)
        
        # Redo button
        redo_x = sidebar_x + button_width + 20
        self.redo_button_rect = pygame.Rect(redo_x, y_pos, button_width, button_height)
        
        # Color based on availability
        if game_state.can_redo():
            redo_color = (70, 130, 180)  # Blue when active
            text_color = (255, 255, 255)
        else:
            redo_color = (100, 100, 100)  # Gray when disabled
            text_color = (150, 150, 150)
        
        pygame.draw.rect(self.screen, redo_color, self.redo_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0, 0, 0), self.redo_button_rect, width=2, border_radius=5)
        
        redo_text = self.small_font.render("Redo", True, text_color)
        redo_text_rect = redo_text.get_rect(center=self.redo_button_rect.center)
        self.screen.blit(redo_text, redo_text_rect)

    def draw_save_load_buttons(self, can_save: bool, can_load: bool, sidebar_x: int, sidebar_width: int, board_height: int):
        """
        Draw save and load buttons in the sidebar.

        Args:
            can_save: Whether save button should be active
            can_load: Whether load button should be active
            sidebar_x: X position where sidebar starts
            sidebar_width: Width of the sidebar
            board_height: Height of the board for positioning
        """
        button_width = (sidebar_width - 30) // 2
        button_height = 40
        y_pos = board_height - 110

        # Save button
        save_x = sidebar_x + 10
        self.save_button_rect = pygame.Rect(save_x, y_pos, button_width, button_height)

        if can_save:
            save_color = (46, 139, 87)  # Green when active
            save_text_color = (255, 255, 255)
        else:
            save_color = (100, 100, 100)
            save_text_color = (150, 150, 150)

        pygame.draw.rect(self.screen, save_color, self.save_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0, 0, 0), self.save_button_rect, width=2, border_radius=5)

        save_text = self.small_font.render("Save", True, save_text_color)
        save_text_rect = save_text.get_rect(center=self.save_button_rect.center)
        self.screen.blit(save_text, save_text_rect)

        # Load button
        load_x = sidebar_x + button_width + 20
        self.load_button_rect = pygame.Rect(load_x, y_pos, button_width, button_height)

        if can_load:
            load_color = (160, 82, 45)  # Brown when active
            load_text_color = (255, 255, 255)
        else:
            load_color = (100, 100, 100)
            load_text_color = (150, 150, 150)

        pygame.draw.rect(self.screen, load_color, self.load_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0, 0, 0), self.load_button_rect, width=2, border_radius=5)

        load_text = self.small_font.render("Load", True, load_text_color)
        load_text_rect = load_text.get_rect(center=self.load_button_rect.center)
        self.screen.blit(load_text, load_text_rect)

    def draw_online_controls(
        self,
        can_reconnect: bool,
        sidebar_x: int,
        sidebar_width: int,
        board_height: int,
        transport_label: str = "",
        invite_code: str = "",
        side: str = "",
        connection_state: str = "offline",
        status_detail: str = "",
    ):
        """Draw online status and reconnect controls in the sidebar."""
        panel_rect = pygame.Rect(sidebar_x + 10, board_height - 190, sidebar_width - 20, 70)
        pygame.draw.rect(self.screen, (38, 38, 38), panel_rect, border_radius=6)
        pygame.draw.rect(self.screen, (90, 90, 90), panel_rect, width=1, border_radius=6)

        side_label = side.capitalize() if side in ("white", "black") else "Pending"
        invite_label = invite_code if invite_code else "----"
        state_label = connection_state.replace('_', ' ').capitalize() if connection_state else 'Offline'
        transport_short = transport_label if transport_label else "shim://session-manager"
        if len(transport_short) > 26:
            transport_short = transport_short[:23] + "..."

        state_color = (170, 170, 170)
        if connection_state in ("connected", "resumed", "resynced"):
            state_color = (120, 210, 255)
        elif connection_state == "reconnecting":
            state_color = (255, 200, 120)
        elif connection_state == "disconnected":
            state_color = (255, 140, 140)

        title = self.small_font.render(f"Online: {side_label}", True, (220, 220, 220))
        state_text = self.small_font.render(state_label, True, state_color)
        hint = self.small_font.render(f"{transport_short} | Code {invite_label}", True, (170, 170, 170))
        self.screen.blit(title, (panel_rect.x + 10, panel_rect.y + 8))
        self.screen.blit(state_text, (panel_rect.right - state_text.get_width() - 10, panel_rect.y + 8))
        self.screen.blit(hint, (panel_rect.x + 10, panel_rect.y + 26))

        if status_detail:
            detail = status_detail
            if len(detail) > 26:
                detail = detail[:23] + "..."
            detail_text = self.small_font.render(detail, True, (190, 190, 190))
            self.screen.blit(detail_text, (panel_rect.x + 10, panel_rect.y + 44))

        button_height = 40
        button_y = board_height - 240
        self.reconnect_button_rect = pygame.Rect(sidebar_x + 10, button_y, sidebar_width - 20, button_height)

        if can_reconnect:
            reconnect_color = (72, 120, 185)
            reconnect_text_color = (255, 255, 255)
        else:
            reconnect_color = (100, 100, 100)
            reconnect_text_color = (150, 150, 150)

        pygame.draw.rect(self.screen, reconnect_color, self.reconnect_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0, 0, 0), self.reconnect_button_rect, width=2, border_radius=5)

        reconnect_text = self.small_font.render("Reconnect", True, reconnect_text_color)
        reconnect_text_rect = reconnect_text.get_rect(center=self.reconnect_button_rect.center)
        self.screen.blit(reconnect_text, reconnect_text_rect)
    
    def is_undo_button_clicked(self, pos: tuple) -> bool:
        """Check if undo button was clicked."""
        if self.undo_button_rect:
            return self.undo_button_rect.collidepoint(pos)
        return False
    
    def is_redo_button_clicked(self, pos: tuple) -> bool:
        """Check if redo button was clicked."""
        if self.redo_button_rect:
            return self.redo_button_rect.collidepoint(pos)
        return False

    def is_save_button_clicked(self, pos: tuple) -> bool:
        """Check if save button was clicked."""
        if self.save_button_rect:
            return self.save_button_rect.collidepoint(pos)
        return False

    def is_load_button_clicked(self, pos: tuple) -> bool:
        """Check if load button was clicked."""
        if self.load_button_rect:
            return self.load_button_rect.collidepoint(pos)
        return False

    def is_reconnect_button_clicked(self, pos: tuple) -> bool:
        """Check if reconnect button was clicked."""
        if self.reconnect_button_rect:
            return self.reconnect_button_rect.collidepoint(pos)
        return False
