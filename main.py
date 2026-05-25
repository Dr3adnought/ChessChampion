"""
ChessChampion - A chess game with AI opponent.
Now using refactored architecture with proper separation of concerns.
"""
import os
import pygame

from ai.ai_player import AIPlayer
from game.champion_chess import ChessGame
from game.menu import Menu, GameOverMenu
from game.paths import ensure_user_data_layout
from game.promotion_dialog import PromotionDialog
from game.save_load.service import load_game, list_saves, save_game
from game.types import GameStatus, Position
from game.animation import AnimationManager
from constants import *


pygame.init()
ensure_user_data_layout()

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


def build_session_meta(game_mode: str, difficulty: str, ai_player_color: str, ai_depth: int) -> dict:
    """Build session metadata used by save/load services."""
    if game_mode == 'pvai':
        white_name = 'AI' if ai_player_color == 'white' else 'Player'
        black_name = 'AI' if ai_player_color == 'black' else 'Player'
        return {
            'mode': 'pvai',
            'players': {
                'white': white_name,
                'black': black_name,
            },
            'ai': {
                'enabled': True,
                'color': ai_player_color,
                'difficulty': difficulty,
                'depth': ai_depth,
            },
        }

    return {
        'mode': 'pvp',
        'players': {
            'white': 'Player 1',
            'black': 'Player 2',
        },
        'ai': {
            'enabled': False,
            'color': 'black',
            'difficulty': 'none',
            'depth': 0,
        },
    }


def perform_autosave(game: ChessGame, session_meta: dict) -> bool:
    """Write rolling autosave file and return success state."""
    result = save_game(
        game,
        source='autosave',
        save_id='autosave',
        file_name='autosave.json',
        session_meta=session_meta,
    )
    if result.get('success'):
        print("Autosave complete")
        return True

    print(result.get('error', 'Autosave failed'))
    return False

# Load piece images once
PIECES = load_pieces()

# Main game loop
game_active = True

while game_active:
    # Show menu and get player choices
    menu = Menu(SCREEN, WIDTH, HEIGHT)
    game_mode, difficulty, ai_color, ai_depth, time_minutes, time_increment = menu.run()

    if game_mode == 'pvp':
        print("\nStarting Player vs Player game")
        print("White moves first - Pass and play!\n")
    else:
        print(f"\nStarting game with {difficulty.upper()} difficulty")
        print(f"You are playing as {('WHITE' if ai_color == 'black' else 'BLACK')}")
        print(f"AI depth: {ai_depth}\n")
    
    if time_minutes > 0:
        print(f"Time Control: {time_minutes} min + {time_increment}s increment\n")
    else:
        print("Time Control: Untimed\n")

    # Initialize the game with time control
    game = ChessGame(time_minutes, time_increment)

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
    
    # Start timer for white (first player)
    if game.timer.is_timed:
        game.timer.start_turn(game.game_state.current_turn)

    # Game loop
    running = True
    clock = pygame.time.Clock()
    game_over_menu_shown = False

    # Save/Load UI state
    show_load_menu = False
    load_entries = []
    load_entry_rects = []
    load_menu_panel_rect = None

    # Prevent duplicate autosave writes on the same exit path
    autosave_written = False

    # Temporary status message state
    status_message = ""
    status_color = (255, 255, 255)
    status_message_until = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not autosave_written:
                    session_meta = build_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth)
                    autosave_written = perform_autosave(game, session_meta)
                running = False
                game_active = False
            elif event.type == pygame.KEYDOWN:
                # Handle keyboard shortcuts
                if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # Ctrl+Z: Undo
                    if not animation_manager.is_busy() and not game.game_over:
                        if game.game_state.undo_move():
                            print("Move undone")
                elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # Ctrl+Y: Redo
                    if not animation_manager.is_busy() and not game.game_over:
                        if game.game_state.redo_move():
                            print("Move redone")
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # Ctrl+S: Save game
                    session_meta = build_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth)
                    save_result = save_game(game, source='manual', session_meta=session_meta)
                    if save_result.get('success'):
                        status_message = f"Saved: {save_result.get('file_name')}"
                        status_color = (100, 220, 100)
                    else:
                        status_message = save_result.get('error', 'Save failed')
                        status_color = (255, 120, 120)
                    status_message_until = pygame.time.get_ticks() + 3500
                elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # Ctrl+L: Open load list
                    load_result = list_saves(include_warnings=True)
                    if load_result.get('success'):
                        load_entries = load_result.get('saves', [])
                        if load_entries:
                            show_load_menu = True
                        else:
                            status_message = "No saved games found"
                            status_color = (255, 200, 120)
                            status_message_until = pygame.time.get_ticks() + 3000
                    else:
                        status_message = load_result.get('error', 'Unable to list saves')
                        status_color = (255, 120, 120)
                        status_message_until = pygame.time.get_ticks() + 3500
                elif event.key == pygame.K_ESCAPE and show_load_menu:
                    show_load_menu = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if show_load_menu:
                    clicked_in_entry = False
                    for entry_rect, entry in load_entry_rects:
                        if entry_rect.collidepoint(event.pos):
                            clicked_in_entry = True
                            load_result = load_game(entry.get('file_name', ''))

                            if load_result.get('success'):
                                loaded_game = load_result.get('game')
                                loaded_session = load_result.get('session_meta', {})

                                game = loaded_game
                                game.renderer = None
                                animation_manager = AnimationManager()

                                loaded_mode = loaded_session.get('mode', 'pvp')
                                if loaded_mode not in ('pvp', 'pvai'):
                                    loaded_mode = 'pvp'

                                game_mode = loaded_mode
                                if game_mode == 'pvai':
                                    ai_meta = loaded_session.get('ai', {}) if isinstance(loaded_session.get('ai', {}), dict) else {}
                                    AI_PLAYER_COLOR = ai_meta.get('color', 'black')
                                    if AI_PLAYER_COLOR not in ('white', 'black'):
                                        AI_PLAYER_COLOR = 'black'

                                    try:
                                        ai_depth = int(ai_meta.get('depth', 2))
                                    except (TypeError, ValueError):
                                        ai_depth = 2

                                    difficulty = str(ai_meta.get('difficulty', 'medium'))
                                    ai_player = AIPlayer(game, AI_PLAYER_COLOR, depth=ai_depth)
                                else:
                                    AI_PLAYER_COLOR = None
                                    ai_player = None
                                    difficulty = 'none'
                                    ai_depth = 0

                                ai_move_pending = False
                                ai_should_move_first = False
                                player_move_pending = (
                                    game_mode == 'pvai'
                                    and AI_PLAYER_COLOR is not None
                                    and not game.game_over
                                    and game.turn == AI_PLAYER_COLOR
                                )
                                game_over_menu_shown = game.game_over

                                status_message = f"Loaded: {entry.get('file_name')}"
                                status_color = (100, 220, 100)
                                status_message_until = pygame.time.get_ticks() + 3500
                            else:
                                status_message = load_result.get('error', 'Load failed')
                                status_color = (255, 120, 120)
                                status_message_until = pygame.time.get_ticks() + 3500

                            show_load_menu = False
                            break

                    if not clicked_in_entry:
                        if load_menu_panel_rect and not load_menu_panel_rect.collidepoint(event.pos):
                            show_load_menu = False

                    continue

                if game.game_over and game_over_menu_shown:
                    # Handle game over menu clicks
                    winner = None
                    if game.game_state.game_status == GameStatus.CHECKMATE:
                        # Determine winner
                        winner = 'white' if game.game_state.current_turn.value == 'black' else 'black'
                    
                    game_over_menu = GameOverMenu(SCREEN, WIDTH, HEIGHT, winner)
                    choice = game_over_menu.handle_click(event.pos)
                    
                    if choice == 'new_game':
                        if not autosave_written:
                            session_meta = build_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth)
                            autosave_written = perform_autosave(game, session_meta)
                        running = False  # Exit current game loop to restart
                    elif choice == 'end_game':
                        if not autosave_written:
                            session_meta = build_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth)
                            autosave_written = perform_autosave(game, session_meta)
                        running = False
                        game_active = False
                elif not game.game_over and not animation_manager.is_busy():
                    mouse_pos = event.pos
                    
                    # Check if undo/redo buttons were clicked
                    if game.renderer:
                        if game.renderer.is_undo_button_clicked(mouse_pos):
                            if game.game_state.undo_move():
                                print("Move undone")
                            continue
                        elif game.renderer.is_redo_button_clicked(mouse_pos):
                            if game.game_state.redo_move():
                                print("Move redone")
                            continue
                        elif game.renderer.is_save_button_clicked(mouse_pos):
                            session_meta = build_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth)
                            save_result = save_game(game, source='manual', session_meta=session_meta)
                            if save_result.get('success'):
                                status_message = f"Saved: {save_result.get('file_name')}"
                                status_color = (100, 220, 100)
                            else:
                                status_message = save_result.get('error', 'Save failed')
                                status_color = (255, 120, 120)
                            status_message_until = pygame.time.get_ticks() + 3500
                            continue
                        elif game.renderer.is_load_button_clicked(mouse_pos):
                            load_result = list_saves(include_warnings=True)
                            if load_result.get('success'):
                                load_entries = load_result.get('saves', [])
                                if load_entries:
                                    show_load_menu = True
                                else:
                                    status_message = "No saved games found"
                                    status_color = (255, 200, 120)
                                    status_message_until = pygame.time.get_ticks() + 3000
                            else:
                                status_message = load_result.get('error', 'Unable to list saves')
                                status_color = (255, 120, 120)
                                status_message_until = pygame.time.get_ticks() + 3500
                            continue
                    
                    # Only allow board clicks when not animating
                    mouse_x, mouse_y = mouse_pos
                    clicked_col = mouse_x // SQUARE_SIZE
                    clicked_row = mouse_y // SQUARE_SIZE
                    
                    # Store the previous board state for comparison
                    old_turn = game.turn
                    
                    # Pass AI color only in PvAI mode to prevent interaction during AI turn
                    promotion_needed = game.handle_click(clicked_row, clicked_col, ai_player_color=AI_PLAYER_COLOR)
                    
                    # Check if promotion dialog is needed
                    if promotion_needed:
                        from_pos, to_pos, pawn_color = promotion_needed
                        
                        # Show promotion dialog
                        promotion_dialog = PromotionDialog(SCREEN, PIECES, pawn_color)
                        selected_piece = promotion_dialog.run()
                        
                        # Execute the promotion
                        if game.execute_promotion(from_pos, to_pos, selected_piece):
                            # Trigger animation
                            piece = game.board.get_piece(to_pos)
                            if piece:
                                piece_key = piece.to_string_notation()
                                piece_image = PIECES.get(piece_key)
                                if piece_image:
                                    animation_manager.start_animation(from_pos, to_pos, piece_image, SQUARE_SIZE, duration_ms=400)
                            
                            # Mark that AI should move after animation completes (only in PvAI mode)
                            if game_mode == 'pvai':
                                ai_move_pending = True
                    
                    # Check if a move was made (turn changed)
                    elif old_turn != game.turn:
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

        # Check for timeout
        if game.timer.is_timed and not game.game_over:
            if game.timer.is_time_out(game.game_state.current_turn):
                # Current player ran out of time - they lose
                print(f"\n!!! TIME OUT !!! {game.game_state.current_turn.value.upper()} LOSES ON TIME!")
                game.game_state.game_status = GameStatus.CHECKMATE  # Treat as game over
                game.timer.pause()
        
        # Pause timer during animations
        if animation_manager.is_busy() and game.timer.is_timed and not game.timer.is_paused:
            game.timer.pause()
        elif not animation_manager.is_busy() and game.timer.is_timed and game.timer.is_paused and not game.game_over:
            game.timer.resume()
        
        # Draw everything
        # If animating, exclude the "from" position so we don't draw duplicate piece
        animating_from_pos = None
        if animation_manager.is_animating():
            animating_from_pos = animation_manager.current_animation.to_pos  # Exclude destination (piece is there after move)
        
        game.draw(SCREEN, SQUARE_SIZE, LIGHT_COLOR_SQUARE, DARK_COLOR_SQUARE, HIGHLIGHT_COLOR, PIECES, animating_from_pos)
        
        # Draw captured pieces sidebar
        if game.renderer:
            # Draw timers
            game.renderer.draw_timers(game.timer, BOARD_SIZE, SIDEBAR_WIDTH, game.game_state.current_turn)
            
            game.renderer.draw_captured_pieces_sidebar(game.game_state, BOARD_SIZE, SIDEBAR_WIDTH)
            # Draw save/load buttons
            game.renderer.draw_save_load_buttons(
                can_save=not animation_manager.is_busy(),
                can_load=not animation_manager.is_busy(),
                sidebar_x=BOARD_SIZE,
                sidebar_width=SIDEBAR_WIDTH,
                board_height=HEIGHT,
            )
            # Draw undo/redo buttons
            game.renderer.draw_undo_redo_buttons(game.game_state, BOARD_SIZE, SIDEBAR_WIDTH, HEIGHT)

        # Draw load selection overlay
        load_entry_rects = []
        load_menu_panel_rect = None
        if show_load_menu:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            SCREEN.blit(overlay, (0, 0))

            panel_width = WIDTH - 120
            panel_height = HEIGHT - 160
            panel_x = (WIDTH - panel_width) // 2
            panel_y = (HEIGHT - panel_height) // 2
            load_menu_panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

            pygame.draw.rect(SCREEN, (35, 35, 35), load_menu_panel_rect, border_radius=8)
            pygame.draw.rect(SCREEN, (180, 180, 180), load_menu_panel_rect, width=2, border_radius=8)

            title_font = pygame.font.Font(None, 40)
            row_font = pygame.font.Font(None, 28)
            hint_font = pygame.font.Font(None, 24)

            title = title_font.render("Load Saved Game", True, (255, 215, 0))
            SCREEN.blit(title, (panel_x + 20, panel_y + 20))

            visible_entries = load_entries[:8]
            row_start_y = panel_y + 80
            row_height = 42

            for index, entry in enumerate(visible_entries):
                row_y = row_start_y + index * (row_height + 8)
                row_rect = pygame.Rect(panel_x + 20, row_y, panel_width - 40, row_height)

                row_color = (70, 70, 70)
                if row_rect.collidepoint(pygame.mouse.get_pos()):
                    row_color = (95, 95, 95)

                pygame.draw.rect(SCREEN, row_color, row_rect, border_radius=5)
                pygame.draw.rect(SCREEN, (130, 130, 130), row_rect, width=1, border_radius=5)

                summary_text = (
                    f"{index + 1}. {entry.get('file_name', 'unknown')} | "
                    f"{entry.get('updated_at_utc', '?')} | "
                    f"{entry.get('mode', 'pvp')}"
                )
                text_surface = row_font.render(summary_text, True, (230, 230, 230))
                SCREEN.blit(text_surface, (row_rect.x + 10, row_rect.y + 10))

                load_entry_rects.append((row_rect, entry))

            hint = hint_font.render("Click a save to load, or click outside to cancel", True, (200, 200, 200))
            SCREEN.blit(hint, (panel_x + 20, panel_y + panel_height - 35))

        # Draw status message
        if status_message and pygame.time.get_ticks() <= status_message_until:
            msg_font = pygame.font.Font(None, 30)
            msg_surface = msg_font.render(status_message, True, status_color)
            msg_bg = pygame.Rect(10, HEIGHT - 35, BOARD_SIZE - 20, 26)
            pygame.draw.rect(SCREEN, (0, 0, 0), msg_bg)
            SCREEN.blit(msg_surface, (15, HEIGHT - 32))
        
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

