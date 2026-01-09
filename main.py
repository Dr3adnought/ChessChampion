"""
ChessChampion - A chess game with AI opponent.
Now using refactored architecture with proper separation of concerns.
"""
import pygame

from ai.ai_player import AIPlayer
from game.champion_chess import ChessGame
from game.menu import Menu, GameOverMenu
from game.types import GameStatus
from constants import *


pygame.init()

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Champion")

def load_pieces():
    """Load and scale piece images."""
    pieces = {}
    piece_names = [
        'b_pawn', 'b_rook', 'b_knight', 'b_bishop', 'b_queen', 'b_king',
        'w_pawn', 'w_rook', 'w_knight', 'w_bishop', 'w_queen', 'w_king'
    ]
    
    def load_and_scale_image(image_name):
        try:
            image_path = os.path.join(ASSETS_PATH, f"{image_name}.png")
            image = pygame.image.load(image_path).convert_alpha()
            image = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
            return image
        except pygame.error as e:
            print(f"Error loading image {image_name}.png: {e}")
            print(f"Please ensure '{image_path}' exists and is a valid image file.")
            placeholder = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(placeholder, (255, 0, 0, 128), placeholder.get_rect())
            font = pygame.font.Font(None, 24)
            text = font.render("?", True, (0, 0, 0))
            text_rect = text.get_rect(center=placeholder.get_rect().center)
            placeholder.blit(text, text_rect)
            return placeholder
    
    for name in piece_names:
        pieces[name] = load_and_scale_image(name)
    
    return pieces

# Load piece images once
PIECES = load_pieces()

# Main game loop
game_active = True

while game_active:
    # Show menu and get player choices
    menu = Menu(SCREEN, WIDTH, HEIGHT)
    difficulty, ai_color, ai_depth = menu.run()

    print(f"\nStarting game with {difficulty.upper()} difficulty")
    print(f"You are playing as {('WHITE' if ai_color == 'black' else 'BLACK')}")
    print(f"AI depth: {ai_depth}\n")

    # Initialize the game
    game = ChessGame()

    # Initialize AI player with selected difficulty
    AI_PLAYER_COLOR = ai_color
    ai_player = AIPlayer(game, AI_PLAYER_COLOR, depth=ai_depth)

    # Game loop
    running = True
    clock = pygame.time.Clock()
    game_over_menu_shown = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                game_active = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game.game_over and game_over_menu_shown:
                    # Handle game over menu clicks
                    winner = None
                    if game.game_state.game_status == GameStatus.CHECKMATE:
                        # Determine winner
                        winner = 'white' if game.game_state.current_turn.value == 'black' else 'black'
                    
                    game_over_menu = GameOverMenu(SCREEN, WIDTH, HEIGHT, winner)
                    choice = game_over_menu.handle_click(event.pos)
                    
                    if choice == 'new_game':
                        running = False  # Exit current game loop to restart
                    elif choice == 'end_game':
                        running = False
                        game_active = False
                elif not game.game_over:
                    mouse_x, mouse_y = event.pos
                    clicked_col = mouse_x // SQUARE_SIZE
                    clicked_row = mouse_y // SQUARE_SIZE
                    game.handle_click(clicked_row, clicked_col, ai_player_color=AI_PLAYER_COLOR)

        # AI makes a move if it's their turn
        if not game.game_over and game.turn == AI_PLAYER_COLOR:
            pygame.time.wait(500)  # Brief pause so moves are visible
            ai_player.make_move()

        # Draw everything
        game.draw(SCREEN, SQUARE_SIZE, LIGHT_COLOR_SQUARE, DARK_COLOR_SQUARE, HIGHLIGHT_COLOR, PIECES)
        
        # Show game over menu if game ended
        if game.game_over:
            if not game_over_menu_shown:
                # Wait a moment before showing menu
                pygame.time.wait(1000)
                game_over_menu_shown = True
            
            # Determine winner for menu
            winner = None
            if game.game_state.game_status == GameStatus.CHECKMATE:
                winner = 'white' if game.game_state.current_turn.value == 'black' else 'black'
            
            game_over_menu = GameOverMenu(SCREEN, WIDTH, HEIGHT, winner)
            game_over_menu.draw(SCREEN)
        
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(60)

# Clean exit
pygame.quit()
print("Game ended. Thanks for playing!")

