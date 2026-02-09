"""
ChessChampion - A chess game with AI opponent.
Now using refactored architecture with proper separation of concerns.
"""
import os
import pygame

from ai.ai_player import AIPlayer
from game.champion_chess import ChessGame
from game.menu import Menu, GameOverMenu
from game.types import GameStatus, Position
from game.animation import AnimationManager
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
    game_mode, difficulty, ai_color, ai_depth = menu.run()

    if game_mode == 'pvp':
        print("\nStarting Player vs Player game")
        print("White moves first - Pass and play!\n")
    else:
        print(f"\nStarting game with {difficulty.upper()} difficulty")
        print(f"You are playing as {('WHITE' if ai_color == 'black' else 'BLACK')}")
        print(f"AI depth: {ai_depth}\n")

    # Initialize the game
    game = ChessGame()

    # Initialize AI player only for PvAI mode
    AI_PLAYER_COLOR = ai_color if game_mode == 'pvai' else None
    ai_player = AIPlayer(game, AI_PLAYER_COLOR, depth=ai_depth) if game_mode == 'pvai' else None

    # Initialize animation manager
    animation_manager = AnimationManager()
    
    # Track pending move (after player clicks, before animation completes)
    player_move_pending = False
    ai_move_pending = False
    
    # If AI plays white, it should move first (only for PvAI)
    ai_should_move_first = (game_mode == 'pvai' and AI_PLAYER_COLOR == 'white')

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
                elif not game.game_over and not animation_manager.is_busy():
                    # Only allow clicks when not animating
                    mouse_x, mouse_y = event.pos
                    clicked_col = mouse_x // SQUARE_SIZE
                    clicked_row = mouse_y // SQUARE_SIZE
                    
                    # Store the previous board state for comparison
                    old_turn = game.turn
                    
                    # Pass AI color only in PvAI mode to prevent interaction during AI turn
                    game.handle_click(clicked_row, clicked_col, ai_player_color=AI_PLAYER_COLOR)
                    
                    # Check if a move was made (turn changed)
                    if old_turn != game.turn:
                        # Player made a move, trigger animation
                        if game.last_move:
                            from_pos, to_pos = game.last_move
                            piece = game.board.get_piece(to_pos)
                            if piece:
                                piece_key = piece.to_string_notation()
                                piece_image = PIECES.get(piece_key)
                                if piece_image:
                                    animation_manager.start_animation(from_pos, to_pos, piece_image, SQUARE_SIZE, duration_ms=400)
                        
                        # Mark that AI should move after animation completes (only in PvAI mode)
                        if game_mode == 'pvai':
                            ai_move_pending = True

        # Handle AI move after player animation completes and delay (only in PvAI mode)
        if game_mode == 'pvai' and ai_move_pending and not animation_manager.is_busy():
            # Player animation is done, add a delay before AI thinks
            animation_manager.start_delay(800)  # 800ms delay to show player's move
            ai_move_pending = False
            player_move_pending = True
        
        # Handle AI first move (when AI plays white) - only in PvAI mode
        if game_mode == 'pvai' and ai_should_move_first and not animation_manager.is_busy() and not game.game_over and game.turn == AI_PLAYER_COLOR:
            # Store old board state before AI move
            old_turn = game.turn
            
            ai_player.make_move()
            
            # Trigger AI move animation
            if game.last_move and old_turn != game.turn:
                from_pos, to_pos = game.last_move
                piece = game.board.get_piece(to_pos)
                if piece:
                    piece_key = piece.to_string_notation()
                    piece_image = PIECES.get(piece_key)
                    if piece_image:
                        animation_manager.start_animation(from_pos, to_pos, piece_image, SQUARE_SIZE, duration_ms=400)
            
            ai_should_move_first = False  # Only do this once
        
        # AI makes a move after delay (subsequent moves) - only in PvAI mode
        if game_mode == 'pvai' and player_move_pending and not animation_manager.is_busy() and not game.game_over and game.turn == AI_PLAYER_COLOR:
            # Store old board state before AI move
            old_turn = game.turn
            
            ai_player.make_move()
            
            # Trigger AI move animation
            if game.last_move and old_turn != game.turn:
                from_pos, to_pos = game.last_move
                piece = game.board.get_piece(to_pos)
                if piece:
                    piece_key = piece.to_string_notation()
                    piece_image = PIECES.get(piece_key)
                    if piece_image:
                        animation_manager.start_animation(from_pos, to_pos, piece_image, SQUARE_SIZE, duration_ms=400)
            
            player_move_pending = False

        # Draw everything
        # If animating, exclude the "from" position so we don't draw duplicate piece
        animating_from_pos = None
        if animation_manager.is_animating():
            animating_from_pos = animation_manager.current_animation.to_pos  # Exclude destination (piece is there after move)
        
        game.draw(SCREEN, SQUARE_SIZE, LIGHT_COLOR_SQUARE, DARK_COLOR_SQUARE, HIGHLIGHT_COLOR, PIECES, animating_from_pos)
        
        # Draw captured pieces sidebar
        if game.renderer:
            game.renderer.draw_captured_pieces_sidebar(game.game_state, BOARD_SIZE, SIDEBAR_WIDTH)
        
        # Draw the animated piece on top
        if animation_manager.is_animating():
            animation_manager.draw_animation(SCREEN)
        
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

