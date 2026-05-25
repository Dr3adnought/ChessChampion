"""Menu system for Chess Champion."""
import pygame
from typing import Tuple, Optional
from constants import TIME_CONTROL_PRESETS


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
        self.small_font = pygame.font.Font(None, 28)
        
        # Colors - Black & Gold Theme
        self.bg_color = (20, 20, 20)  # Deep black
        self.title_color = (255, 215, 0)  # Bright gold
        self.label_color = (212, 175, 55)  # Metallic gold
        
        # Button colors - Gold with black text
        self.mode_color = (212, 175, 55)  # Metallic gold
        self.mode_hover = (255, 215, 0)  # Bright gold
        self.difficulty_color = (184, 134, 11)  # Dark gold
        self.difficulty_hover = (212, 175, 55)  # Metallic gold
        self.color_btn_color = (212, 175, 55)  # Metallic gold
        self.color_btn_hover = (255, 215, 0)  # Bright gold
        self.start_color = (255, 215, 0)  # Bright gold
        self.start_hover = (255, 235, 50)  # Lighter gold
        
        # Selection state
        self.selected_mode = 'pvai'  # Default: Player vs AI
        self.selected_difficulty = 'medium'  # Default
        self.selected_color = 'white'  # Default
        self.selected_time_control = 4  # Default: Blitz 5+0 (index in TIME_CONTROL_PRESETS)
        self.selected_online_role = 'host'  # Default role in online mode
        self.online_invite_code = ''
        self.online_invite_active = False
        
        # Menu state
        self.current_screen = 'mode'  # 'mode', 'settings', 'online', or 'time'
        
        # Create buttons
        self._create_buttons()
        
    def _create_buttons(self):
        """Create all menu buttons."""
        button_width = 180
        button_height = 50
        spacing = 20
        
        # Game mode buttons (wider to fit text, centered)
        mode_button_width = 220
        mode_start_x = (self.width - (mode_button_width * 3 + spacing * 2)) // 2
        mode_y = 200
        
        self.mode_buttons = {
            'pvai': Button(mode_start_x, mode_y, mode_button_width, button_height,
                          'Player vs AI', self.mode_color, self.mode_hover, (0, 0, 0)),
            'pvp': Button(mode_start_x + mode_button_width + spacing, mode_y,
                         mode_button_width, button_height, 'Player vs Player',
                         self.mode_color, self.mode_hover, (0, 0, 0)),
            'online': Button(mode_start_x + (mode_button_width + spacing) * 2, mode_y,
                         mode_button_width, button_height, 'Online PvP',
                         self.mode_color, self.mode_hover, (0, 0, 0))
        }
        
        # Mark default selection
        self.mode_buttons['pvai'].is_selected = True
        
        # Difficulty buttons (centered, side by side) - only for AI mode
        diff_start_x = (self.width - (button_width * 4 + spacing * 3)) // 2
        diff_y = 200
        
        self.difficulty_buttons = {
            'easy': Button(diff_start_x, diff_y, button_width, button_height, 
                          'Easy', self.difficulty_color, self.difficulty_hover, (0, 0, 0)),
            'medium': Button(diff_start_x + button_width + spacing, diff_y, 
                           button_width, button_height, 'Medium', 
                           self.difficulty_color, self.difficulty_hover, (0, 0, 0)),
            'hard': Button(diff_start_x + (button_width + spacing) * 2, diff_y, 
                          button_width, button_height, 'Hard', 
                          self.difficulty_color, self.difficulty_hover, (0, 0, 0)),
            'expert': Button(diff_start_x + (button_width + spacing) * 3, diff_y, 
                           button_width, button_height, 'Expert', 
                           self.difficulty_color, self.difficulty_hover, (0, 0, 0))
        }
        
        # Mark default selection
        self.difficulty_buttons['medium'].is_selected = True
        
        # Color selection buttons (centered, side by side)
        color_start_x = (self.width - (button_width * 2 + spacing)) // 2
        color_y = 350
        
        self.color_buttons = {
            'white': Button(color_start_x, color_y, button_width, button_height,
                          'Play as White', self.color_btn_color, self.color_btn_hover, (0, 0, 0)),
            'black': Button(color_start_x + button_width + spacing, color_y,
                          button_width, button_height, 'Play as Black', 
                          self.color_btn_color, self.color_btn_hover, (0, 0, 0))
        }
        
        # Mark default selection
        self.color_buttons['white'].is_selected = True
        
        # Online role buttons
        role_start_x = (self.width - (button_width * 2 + spacing)) // 2
        role_y = 280
        self.online_role_buttons = {
            'host': Button(role_start_x, role_y, button_width, button_height,
                           'Host', self.color_btn_color, self.color_btn_hover, (0, 0, 0)),
            'join': Button(role_start_x + button_width + spacing, role_y, button_width, button_height,
                           'Join', self.color_btn_color, self.color_btn_hover, (0, 0, 0)),
        }
        self.online_role_buttons['host'].is_selected = True

        self.invite_input_rect = pygame.Rect((self.width - 320) // 2, 380, 320, 50)

        # Start button (centered, larger)
        start_width = 300
        start_height = 60
        start_x = (self.width - start_width) // 2
        start_y = 650
        
        self.start_button = Button(start_x, start_y, start_width, start_height,
                                   'Continue', self.start_color, self.start_hover, (0, 0, 0))
        
        # Time control buttons (grid layout)
        self._create_time_control_buttons()
    
    def _create_time_control_buttons(self):
        """Create time control selection buttons."""
        self.time_control_buttons = []
        button_width = 140
        button_height = 50
        spacing = 15
        buttons_per_row = 4
        
        # Calculate starting position to center the grid
        total_width = buttons_per_row * button_width + (buttons_per_row - 1) * spacing
        start_x = (self.width - total_width) // 2
        start_y = 200
        
        for i, (name, _, _) in enumerate(TIME_CONTROL_PRESETS):
            row = i // buttons_per_row
            col = i % buttons_per_row
            x = start_x + col * (button_width + spacing)
            y = start_y + row * (button_height + spacing)
            
            button = Button(x, y, button_width, button_height, name,
                          (184, 134, 11), (212, 175, 55), (0, 0, 0))
            
            # Mark default selection (Blitz 5+0)
            if i == 4:
                button.is_selected = True
            
            self.time_control_buttons.append(button)
    
    def draw(self):
        """Draw the menu."""
        # Background
        self.screen.fill(self.bg_color)
        
        # Title
        title_text = self.title_font.render('Chess Champion', True, self.title_color)
        title_rect = title_text.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        if self.current_screen == 'mode':
            self._draw_mode_screen()
        elif self.current_screen == 'settings':
            self._draw_settings_screen()
        elif self.current_screen == 'online':
            self._draw_online_screen()
        elif self.current_screen == 'time':
            self._draw_time_control_screen()
    
    def _draw_mode_screen(self):
        """Draw game mode selection screen."""
        # Game mode label
        mode_label = self.label_font.render('Game Mode:', True, self.label_color)
        mode_label_rect = mode_label.get_rect(center=(self.width // 2, 150))
        self.screen.blit(mode_label, mode_label_rect)
        
        # Game mode buttons
        for button in self.mode_buttons.values():
            button.draw(self.screen, self.button_font)
        
        # Update button text for this screen
        self.start_button.text = 'Continue'
        self.start_button.draw(self.screen, self.button_font)

    def _draw_online_screen(self):
        """Draw online host/join setup screen."""
        role_label = self.label_font.render('Online Role:', True, self.label_color)
        role_label_rect = role_label.get_rect(center=(self.width // 2, 230))
        self.screen.blit(role_label, role_label_rect)

        for button in self.online_role_buttons.values():
            button.draw(self.screen, self.button_font)

        invite_label = self.small_font.render('Invite Code (Join only):', True, (200, 200, 200))
        self.screen.blit(invite_label, (self.invite_input_rect.x, self.invite_input_rect.y - 28))

        input_color = (255, 215, 0) if self.online_invite_active else (212, 175, 55)
        pygame.draw.rect(self.screen, input_color, self.invite_input_rect, border_radius=8)
        pygame.draw.rect(self.screen, (0, 0, 0), self.invite_input_rect, width=2, border_radius=8)

        invite_display = self.online_invite_code if self.online_invite_code else 'Enter invite code'
        text_color = (0, 0, 0) if self.online_invite_code else (60, 60, 60)
        invite_text = self.button_font.render(invite_display, True, text_color)
        invite_text_rect = invite_text.get_rect(midleft=(self.invite_input_rect.x + 10, self.invite_input_rect.centery))
        self.screen.blit(invite_text, invite_text_rect)

        info = self.small_font.render('Host selects time control next. Join uses host settings.', True, (150, 150, 150))
        info_rect = info.get_rect(center=(self.width // 2, 460))
        self.screen.blit(info, info_rect)

        self.start_button.text = 'Continue'
        self.start_button.draw(self.screen, self.button_font)
    
    def _draw_settings_screen(self):
        """Draw AI difficulty and color selection screen."""
        # Difficulty label
        diff_label = self.label_font.render('AI Difficulty:', True, self.label_color)
        diff_label_rect = diff_label.get_rect(center=(self.width // 2, 150))
        self.screen.blit(diff_label, diff_label_rect)
        
        # Difficulty buttons
        for button in self.difficulty_buttons.values():
            button.draw(self.screen, self.button_font)
        
        # Color selection label
        color_label = self.label_font.render('Your Color:', True, self.label_color)
        color_label_rect = color_label.get_rect(center=(self.width // 2, 300))
        self.screen.blit(color_label, color_label_rect)
        
        # Color buttons
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
        info_rect = info_text.get_rect(center=(self.width // 2, 450))
        self.screen.blit(info_text, info_rect)
        
        # Update button text for this screen
        self.start_button.text = 'Continue'
        self.start_button.draw(self.screen, self.button_font)
    
    def _draw_time_control_screen(self):
        """Draw time control selection screen."""
        # Time control label
        time_label = self.label_font.render('Time Control:', True, self.label_color)
        time_label_rect = time_label.get_rect(center=(self.width // 2, 150))
        self.screen.blit(time_label, time_label_rect)
        
        # Time control buttons
        for button in self.time_control_buttons:
            button.draw(self.screen, self.button_font)
        
        # Show description of selected time control
        name, minutes, increment = TIME_CONTROL_PRESETS[self.selected_time_control]
        if minutes == 0:
            description = "No time limit - Play at your own pace"
        else:
            inc_text = f"+{increment}s increment" if increment > 0 else "no increment"
            description = f"{minutes} minute{'s' if minutes > 1 else ''} per player, {inc_text}"
        
        desc_text = self.button_font.render(description, True, (150, 150, 150))
        desc_rect = desc_text.get_rect(center=(self.width // 2, 530))
        self.screen.blit(desc_text, desc_rect)
        
        # Update button text for this screen
        self.start_button.text = 'Start Game'
        self.start_button.draw(self.screen, self.button_font)
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[str, str, str, int, int, int, str, str]]:
        """
        Handle mouse click on menu.
        
        Args:
            mouse_pos: Position of mouse click
            
        Returns:
            Tuple of (mode, difficulty, ai_color, depth, time_minutes, time_increment) if start clicked, None otherwise
        """
        if self.current_screen == 'mode':
            return self._handle_mode_click(mouse_pos)
        elif self.current_screen == 'settings':
            return self._handle_settings_click(mouse_pos)
        elif self.current_screen == 'online':
            return self._handle_online_click(mouse_pos)
        elif self.current_screen == 'time':
            return self._handle_time_click(mouse_pos)
        return None
    
    def _handle_mode_click(self, mouse_pos: Tuple[int, int]) -> None:
        """Handle clicks on mode selection screen."""
        # Check game mode buttons
        for mode, button in self.mode_buttons.items():
            if button.is_clicked(mouse_pos):
                for btn in self.mode_buttons.values():
                    btn.is_selected = False
                button.is_selected = True
                self.selected_mode = mode
                return None
        
        # Check continue button
        if self.start_button.is_clicked(mouse_pos):
            if self.selected_mode == 'pvai':
                self.current_screen = 'settings'
            elif self.selected_mode == 'online':
                self.current_screen = 'online'
            else:
                self.current_screen = 'time'
        return None

    def _handle_online_click(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[str, str, str, int, int, int, str, str]]:
        """Handle online role/invite screen interactions."""
        for role, button in self.online_role_buttons.items():
            if button.is_clicked(mouse_pos):
                for btn in self.online_role_buttons.values():
                    btn.is_selected = False
                button.is_selected = True
                self.selected_online_role = role
                return None

        self.online_invite_active = self.invite_input_rect.collidepoint(mouse_pos)

        if self.start_button.is_clicked(mouse_pos):
            if self.selected_online_role == 'join':
                invite = self.online_invite_code.strip().upper()
                if invite:
                    return ('online', 'none', 'white', 0, 0, 0, 'join', invite)
                return None

            self.current_screen = 'time'
        return None
    
    def _handle_settings_click(self, mouse_pos: Tuple[int, int]) -> None:
        """Handle clicks on settings screen (difficulty and color)."""
        # Check difficulty buttons
        for difficulty, button in self.difficulty_buttons.items():
            if button.is_clicked(mouse_pos):
                for btn in self.difficulty_buttons.values():
                    btn.is_selected = False
                button.is_selected = True
                self.selected_difficulty = difficulty
                return None
        
        # Check color buttons
        for color, button in self.color_buttons.items():
            if button.is_clicked(mouse_pos):
                for btn in self.color_buttons.values():
                    btn.is_selected = False
                button.is_selected = True
                self.selected_color = color
                return None
        
        # Check continue button
        if self.start_button.is_clicked(mouse_pos):
            self.current_screen = 'time'
        return None
    
    def _handle_time_click(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[str, str, str, int, int, int, str, str]]:
        """Handle clicks on time control screen."""
        # Check time control buttons
        for i, button in enumerate(self.time_control_buttons):
            if button.is_clicked(mouse_pos):
                for btn in self.time_control_buttons:
                    btn.is_selected = False
                button.is_selected = True
                self.selected_time_control = i
                return None
        
        # Check start button
        if self.start_button.is_clicked(mouse_pos):
            # Get time control settings
            _, minutes, increment = TIME_CONTROL_PRESETS[self.selected_time_control]
            
            if self.selected_mode == 'pvp':
                return ('pvp', 'none', 'white', 0, minutes, increment, 'none', '')
            elif self.selected_mode == 'online':
                return ('online', 'none', 'white', 0, minutes, increment, self.selected_online_role, self.online_invite_code.strip().upper())
            else:
                # Map difficulty to depth
                depth_map = {'easy': 1, 'medium': 2, 'hard': 3, 'expert': 4}
                depth = depth_map[self.selected_difficulty]
                ai_color = 'black' if self.selected_color == 'white' else 'white'
                return ('pvai', self.selected_difficulty, ai_color, depth, minutes, increment, 'none', '')
        
        return None
    
    def run(self) -> Tuple[str, str, str, int, int, int, str, str]:
        """
        Run the menu and wait for user to start the game.
        
        Returns:
            Tuple of (mode, difficulty, ai_color, depth, time_minutes, time_increment, online_role, invite_code)
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
                elif event.type == pygame.KEYDOWN and self.current_screen == 'online' and self.online_invite_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.online_invite_code = self.online_invite_code[:-1]
                    elif event.key == pygame.K_RETURN:
                        result = self._handle_online_click((self.start_button.rect.centerx, self.start_button.rect.centery))
                        if result:
                            return result
                    else:
                        if len(event.unicode) == 1 and event.unicode.isalnum() and len(self.online_invite_code) < 12:
                            self.online_invite_code += event.unicode.upper()
            
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
        
        # Colors - Black & Gold Theme
        self.overlay_color = (0, 0, 0, 180)  # Semi-transparent black
        self.title_color = (255, 215, 0)  # Bright gold
        self.subtitle_color = (212, 175, 55)  # Metallic gold
        
        # Button colors
        self.new_game_color = (212, 175, 55)  # Metallic gold
        self.new_game_hover = (255, 215, 0)  # Bright gold
        self.end_game_color = (60, 60, 60)  # Dark gray
        self.end_game_hover = (80, 80, 80)  # Lighter gray
        
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
            'New Game', self.new_game_color, self.new_game_hover, (0, 0, 0)
        )
        
        self.end_game_button = Button(
            start_x, start_y + button_height + spacing, 
            button_width, button_height,
            'End Game', self.end_game_color, self.end_game_hover, (200, 200, 200)
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
