"""
Menu system for Chess Champion.
Allows players to select difficulty level and color before starting the game.
"""
import pygame
from typing import Tuple, Optional


class Button:
    """A clickable button for the menu."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 color: Tuple[int, int, int], hover_color: Tuple[int, int, int],
                 text_color: Tuple[int, int, int] = (255, 255, 255)):
        """
        Initialize a button.
        
        Args:
            x, y: Position of the button
            width, height: Size of the button
            text: Text to display on the button
            color: Normal button color
            hover_color: Color when mouse hovers over button
            text_color: Color of the text
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_selected = False
        self.selected_color = (100, 200, 100)  # Green for selected state
        
    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        """Draw the button on the screen."""
        mouse_pos = pygame.mouse.get_pos()
        is_hovering = self.rect.collidepoint(mouse_pos)
        
        # Choose color based on state
        if self.is_selected:
            current_color = self.selected_color
        elif is_hovering:
            current_color = self.hover_color
        else:
            current_color = self.color
        
        # Draw button rectangle
        pygame.draw.rect(screen, current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, width=2, border_radius=10)
        
        # Draw text
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if the button was clicked."""
        return self.rect.collidepoint(mouse_pos)


class Menu:
    """Main menu for Chess Champion."""
    
    def __init__(self, screen: pygame.Surface, width: int, height: int):
        """
        Initialize the menu.
        
        Args:
            screen: Pygame screen surface
            width, height: Screen dimensions
        """
        self.screen = screen
        self.width = width
        self.height = height
        
        # Fonts
        self.title_font = pygame.font.Font(None, 80)
        self.button_font = pygame.font.Font(None, 36)
        self.label_font = pygame.font.Font(None, 42)
        
        # Colors
        self.bg_color = (40, 40, 40)
        self.title_color = (255, 215, 0)  # Gold
        self.label_color = (200, 200, 200)
        
        # Button colors
        self.mode_color = (148, 0, 211)  # Dark violet
        self.mode_hover = (178, 30, 241)
        self.difficulty_color = (70, 130, 180)  # Steel blue
        self.difficulty_hover = (100, 160, 210)
        self.color_btn_color = (139, 69, 19)  # Saddle brown
        self.color_btn_hover = (169, 99, 49)
        self.start_color = (34, 139, 34)  # Forest green
        self.start_hover = (50, 205, 50)  # Lime green
        
        # Selection state
        self.selected_mode = 'pvai'  # Default: Player vs AI
        self.selected_difficulty = 'medium'  # Default
        self.selected_color = 'white'  # Default
        
        # Create buttons
        self._create_buttons()
        
    def _create_buttons(self):
        """Create all menu buttons."""
        button_width = 180
        button_height = 50
        spacing = 20
        
        # Game mode buttons (wider to fit text, centered, side by side)
        mode_button_width = 220
        mode_start_x = (self.width - (mode_button_width * 2 + spacing)) // 2
        mode_y = 200
        
        self.mode_buttons = {
            'pvai': Button(mode_start_x, mode_y, mode_button_width, button_height,
                          'Player vs AI', self.mode_color, self.mode_hover),
            'pvp': Button(mode_start_x + mode_button_width + spacing, mode_y,
                         mode_button_width, button_height, 'Player vs Player',
                         self.mode_color, self.mode_hover)
        }
        
        # Mark default selection
        self.mode_buttons['pvai'].is_selected = True
        
        # Difficulty buttons (centered, side by side) - only for AI mode
        diff_start_x = (self.width - (button_width * 4 + spacing * 3)) // 2
        diff_y = 330
        
        self.difficulty_buttons = {
            'easy': Button(diff_start_x, diff_y, button_width, button_height, 
                          'Easy', self.difficulty_color, self.difficulty_hover),
            'medium': Button(diff_start_x + button_width + spacing, diff_y, 
                           button_width, button_height, 'Medium', 
                           self.difficulty_color, self.difficulty_hover),
            'hard': Button(diff_start_x + (button_width + spacing) * 2, diff_y, 
                          button_width, button_height, 'Hard', 
                          self.difficulty_color, self.difficulty_hover),
            'expert': Button(diff_start_x + (button_width + spacing) * 3, diff_y, 
                           button_width, button_height, 'Expert', 
                           self.difficulty_color, self.difficulty_hover)
        }
        
        # Mark default selection
        self.difficulty_buttons['medium'].is_selected = True
        
        # Color selection buttons (centered, side by side)
        color_start_x = (self.width - (button_width * 2 + spacing)) // 2
        color_y = 480
        
        self.color_buttons = {
            'white': Button(color_start_x, color_y, button_width, button_height,
                          'Play as White', self.color_btn_color, self.color_btn_hover),
            'black': Button(color_start_x + button_width + spacing, color_y,
                          button_width, button_height, 'Play as Black', 
                          self.color_btn_color, self.color_btn_hover)
        }
        
        # Mark default selection
        self.color_buttons['white'].is_selected = True
        
        # Start button (centered, larger)
        start_width = 300
        start_height = 60
        start_x = (self.width - start_width) // 2
        start_y = 650
        
        self.start_button = Button(start_x, start_y, start_width, start_height,
                                   'Start Game', self.start_color, self.start_hover)
    
    def draw(self):
        """Draw the menu."""
        # Background
        self.screen.fill(self.bg_color)
        
        # Title
        title_text = self.title_font.render('Chess Champion', True, self.title_color)
        title_rect = title_text.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Game mode label
        mode_label = self.label_font.render('Game Mode:', True, self.label_color)
        mode_label_rect = mode_label.get_rect(center=(self.width // 2, 150))
        self.screen.blit(mode_label, mode_label_rect)
        
        # Game mode buttons
        for button in self.mode_buttons.values():
            button.draw(self.screen, self.button_font)
        
        # Only show difficulty and color selection for AI mode
        if self.selected_mode == 'pvai':
            # Difficulty label
            diff_label = self.label_font.render('AI Difficulty:', True, self.label_color)
            diff_label_rect = diff_label.get_rect(center=(self.width // 2, 280))
            self.screen.blit(diff_label, diff_label_rect)
            
            # Difficulty buttons
            for button in self.difficulty_buttons.values():
                button.draw(self.screen, self.button_font)
            
            # Color selection label
            color_label = self.label_font.render('Your Color:', True, self.label_color)
            color_label_rect = color_label.get_rect(center=(self.width // 2, 430))
            self.screen.blit(color_label, color_label_rect)
        
        # Color buttons (only for AI mode)
        if self.selected_mode == 'pvai':
            for button in self.color_buttons.values():
                button.draw(self.screen, self.button_font)
            
            # Difficulty info text
            difficulty_info = {
                'easy': 'Easy - Good for beginners',
                'medium': 'Medium - Balanced challenge',
                'hard': 'Hard - Strategic play required',
                'expert': 'Expert - Maximum challenge'
            }
            info_text = self.button_font.render(difficulty_info[self.selected_difficulty], 
                                               True, (150, 150, 150))
            info_rect = info_text.get_rect(center=(self.width // 2, 580))
            self.screen.blit(info_text, info_rect)
        else:
            # PvP mode info
            info_text = self.button_font.render('White moves first - Pass and play!', 
                                               True, (150, 150, 150))
            info_rect = info_text.get_rect(center=(self.width // 2, 280))
            self.screen.blit(info_text, info_rect)
        
        # Start button
        self.start_button.draw(self.screen, self.button_font)
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[str, str, str, int]]:
        """
        Handle mouse click on menu.
        
        Args:
            mouse_pos: Position of mouse click
            
        Returns:
            Tuple of (mode, difficulty, color, depth) if start button clicked, None otherwise
        """
        # Check game mode buttons
        for mode, button in self.mode_buttons.items():
            if button.is_clicked(mouse_pos):
                # Deselect all mode buttons
                for btn in self.mode_buttons.values():
                    btn.is_selected = False
                # Select clicked button
                button.is_selected = True
                self.selected_mode = mode
                return None
        
        # Check difficulty buttons (only relevant for AI mode)
        if self.selected_mode == 'pvai':
            for difficulty, button in self.difficulty_buttons.items():
                if button.is_clicked(mouse_pos):
                    # Deselect all difficulty buttons
                    for btn in self.difficulty_buttons.values():
                        btn.is_selected = False
                    # Select clicked button
                    button.is_selected = True
                    self.selected_difficulty = difficulty
                    return None
            
            # Check color buttons (only relevant for AI mode)
            for color, button in self.color_buttons.items():
                if button.is_clicked(mouse_pos):
                    # Deselect all color buttons
                    for btn in self.color_buttons.values():
                        btn.is_selected = False
                    # Select clicked button
                    button.is_selected = True
                    self.selected_color = color
                    return None
        
        # Check start button
        if self.start_button.is_clicked(mouse_pos):
            if self.selected_mode == 'pvp':
                # Player vs Player - no AI
                return ('pvp', 'none', 'white', 0)
            else:
                # Player vs AI
                # Map difficulty to depth
                depth_map = {
                    'easy': 1,
                    'medium': 2,
                    'hard': 3,
                    'expert': 4
                }
                depth = depth_map[self.selected_difficulty]
                
                # Determine AI color (opposite of player)
                ai_color = 'black' if self.selected_color == 'white' else 'white'
                
                return ('pvai', self.selected_difficulty, ai_color, depth)
        
        return None
    
    def run(self) -> Tuple[str, str, str, int]:
        """
        Run the menu and wait for user to start the game.
        
        Returns:
            Tuple of (mode, difficulty, ai_color, depth)
        """
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    result = self.handle_click(event.pos)
                    if result:
                        return result
            
            self.draw()
            pygame.display.flip()
            clock.tick(60)


class GameOverMenu:
    """Game over menu with New Game and End Game options."""
    
    def __init__(self, screen: pygame.Surface, width: int, height: int, winner: Optional[str] = None):
        """
        Initialize the game over menu.
        
        Args:
            screen: Pygame screen surface
            width, height: Screen dimensions
            winner: 'white', 'black', or None for stalemate
        """
        self.screen = screen
        self.width = width
        self.height = height
        self.winner = winner
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 48)
        self.button_font = pygame.font.Font(None, 40)
        
        # Colors
        self.overlay_color = (0, 0, 0, 180)  # Semi-transparent black
        self.title_color = (255, 215, 0)  # Gold
        self.subtitle_color = (200, 200, 200)
        
        # Button colors
        self.new_game_color = (34, 139, 34)  # Forest green
        self.new_game_hover = (50, 205, 50)  # Lime green
        self.end_game_color = (178, 34, 34)  # Firebrick red
        self.end_game_hover = (220, 20, 60)  # Crimson
        
        # Create buttons
        self._create_buttons()
    
    def _create_buttons(self):
        """Create menu buttons."""
        button_width = 250
        button_height = 60
        spacing = 30
        
        # Center buttons horizontally
        start_x = (self.width - button_width) // 2
        start_y = self.height // 2 + 50
        
        self.new_game_button = Button(
            start_x, start_y, button_width, button_height,
            'New Game', self.new_game_color, self.new_game_hover
        )
        
        self.end_game_button = Button(
            start_x, start_y + button_height + spacing, 
            button_width, button_height,
            'End Game', self.end_game_color, self.end_game_hover
        )
    
    def draw(self, game_surface: pygame.Surface):
        """
        Draw the game over menu as an overlay.
        
        Args:
            game_surface: The current game screen to draw over
        """
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(self.overlay_color)
        self.screen.blit(overlay, (0, 0))
        
        # Game Over title
        title_text = self.title_font.render('Game Over', True, self.title_color)
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 2 - 120))
        self.screen.blit(title_text, title_rect)
        
        # Winner/result subtitle
        if self.winner:
            result_text = f"{self.winner.upper()} Wins!"
            result_color = (255, 255, 255)
        else:
            result_text = "It's a Draw!"
            result_color = (200, 200, 200)
        
        subtitle = self.subtitle_font.render(result_text, True, result_color)
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, self.height // 2 - 50))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Draw buttons
        self.new_game_button.draw(self.screen, self.button_font)
        self.end_game_button.draw(self.screen, self.button_font)
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """
        Handle mouse click on menu.
        
        Args:
            mouse_pos: Position of mouse click
            
        Returns:
            'new_game' if New Game clicked, 'end_game' if End Game clicked, None otherwise
        """
        if self.new_game_button.is_clicked(mouse_pos):
            return 'new_game'
        elif self.end_game_button.is_clicked(mouse_pos):
            return 'end_game'
        return None
    
    def run(self) -> str:
        """
        Run the game over menu and wait for user choice.
        
        Returns:
            'new_game' or 'end_game'
        """
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'end_game'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    result = self.handle_click(event.pos)
                    if result:
                        return result
            
            self.draw(None)
            pygame.display.flip()
            clock.tick(60)
