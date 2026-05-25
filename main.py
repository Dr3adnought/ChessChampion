"""
ChessChampion - A chess game with AI opponent.
Now using refactored architecture with proper separation of concerns.
"""
import os
import pygame

from app_metadata import APP_NAME, APP_VERSION
from ai.ai_player import AIPlayer
from game.champion_chess import ChessGame
from game.menu import Menu, GameOverMenu
from game.network import (
    SessionManagerClientAdapter,
    SessionManagerHub,
    apply_authoritative_clock,
    apply_authoritative_move,
    apply_authoritative_state,
    build_move_intent_payload,
)
from game.paths import ensure_user_data_layout
from game.promotion_dialog import PromotionDialog
from game.save_load.service import load_game, list_saves, save_game
from game.types import Color, GameStatus, PieceType, Position
from game.animation import AnimationManager
from constants import *


pygame.init()
ensure_user_data_layout()

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"{APP_NAME} {APP_VERSION}")

# In-process online hub for local host/join wiring until network transport is externalized.
ONLINE_HUB = SessionManagerHub()

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
    if game_mode == 'online':
        return {
            'mode': 'online',
            'players': {
                'white': 'Online White',
                'black': 'Online Black',
            },
            'ai': {
                'enabled': False,
                'color': 'black',
                'difficulty': 'none',
                'depth': 0,
            },
        }

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


def build_runtime_session_meta(
    game_mode: str,
    difficulty: str,
    ai_player_color: str | None,
    ai_depth: int,
    online_session: dict | None = None,
) -> dict:
    """Build persisted session metadata, including online reconnect context when available."""
    session_meta = build_session_meta(game_mode, difficulty, ai_player_color or 'black', ai_depth)
    if game_mode == 'online':
        network = online_session if isinstance(online_session, dict) else {}
        session_meta['network'] = {
            'role': str(network.get('role', '')),
            'invite_code': str(network.get('invite_code', '')),
            'side': str(network.get('side', '')),
            'game_id': str(network.get('game_id', '')),
            'player_id': str(network.get('player_id', '')),
            'resume_token': str(network.get('resume_token', '')),
            'resume_token_expires_at_utc': str(network.get('resume_token_expires_at_utc', '')),
            'last_seen_event_id': str(network.get('last_seen_event_id', '')),
        }
    return session_meta


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


def bootstrap_online_client(
    role: str,
    invite_code: str,
    time_minutes: int,
    time_increment: int,
) -> tuple[SessionManagerClientAdapter | None, str, int, int, str | None, bool, dict]:
    """Initialize in-process online adapter flow and return status text."""
    adapter = SessionManagerClientAdapter(ONLINE_HUB)
    adapter.connect()
    session = {
        'role': role,
        'invite_code': invite_code.strip().upper(),
        'side': None,
        'game_id': None,
        'player_id': None,
        'resume_token': None,
        'resume_token_expires_at_utc': None,
        'last_seen_event_id': '',
    }

    if role == 'host':
        adapter.send(
            'host_create',
            {
                'requested_side': 'white',
                'time_control': {'minutes': time_minutes, 'increment': time_increment},
            },
        )
        events = adapter.poll()
        host_created = next((e for e in events if e.event_type == 'host_created'), None)
        if not host_created:
            adapter.disconnect()
            return None, 'Online host setup failed', time_minutes, time_increment, None, False, session

        _update_online_session(session, host_created, adapter)

        invite = host_created.payload.get('invite_code', '')
        side = host_created.payload.get('host_side', 'white')
        return adapter, f'Online host ready. Invite code: {invite}', time_minutes, time_increment, side, False, session

    join_code = invite_code.strip().upper()
    if not join_code:
        adapter.disconnect()
        return None, 'Join failed: invite code is required', time_minutes, time_increment, None, False, session

    adapter.send('join_request', {'invite_code': join_code})
    events = adapter.poll()
    join_accepted = next((e for e in events if e.event_type == 'join_accepted'), None)
    game_start = next((e for e in events if e.event_type == 'game_start'), None)

    if not join_accepted:
        adapter.disconnect()
        return None, f'Join failed for code {join_code}', time_minutes, time_increment, None, False, session

    _update_online_session(session, join_accepted, adapter)
    if game_start:
        _update_online_session(session, game_start, adapter)

    resolved_minutes = time_minutes
    resolved_increment = time_increment
    if game_start:
        tc = game_start.payload.get('time_control', {})
        try:
            resolved_minutes = int(tc.get('minutes', resolved_minutes))
            resolved_increment = int(tc.get('increment', resolved_increment))
        except (TypeError, ValueError):
            pass

    side = join_accepted.payload.get('side', 'black')
    started = game_start is not None
    return adapter, f'Joined online session {join_code}', resolved_minutes, resolved_increment, side, started, session


def _update_online_session(session: dict, network_event, adapter: SessionManagerClientAdapter | None = None) -> None:
    """Capture reconnect/session identity from authoritative online events."""
    if not isinstance(session, dict):
        return

    payload = network_event.payload if hasattr(network_event, 'payload') else {}
    if not isinstance(payload, dict):
        payload = {}

    if adapter is not None:
        if adapter.game_id:
            session['game_id'] = adapter.game_id
        if adapter.player_id:
            session['player_id'] = adapter.player_id

    event_id = getattr(network_event, 'event_id', '')
    if isinstance(event_id, str) and event_id:
        session['last_seen_event_id'] = event_id

    invite_code = payload.get('invite_code')
    if isinstance(invite_code, str) and invite_code:
        session['invite_code'] = invite_code

    game_id = payload.get('game_id')
    if isinstance(game_id, str) and game_id:
        session['game_id'] = game_id

    player_id = payload.get('player_id')
    if isinstance(player_id, str) and player_id:
        session['player_id'] = player_id

    side = payload.get('side') or payload.get('host_side') or session.get('side')
    if side in ('white', 'black'):
        session['side'] = side

    resume_token = payload.get('new_resume_token') or payload.get('resume_token')
    if isinstance(resume_token, str) and resume_token:
        session['resume_token'] = resume_token

    resume_expires = payload.get('resume_token_expires_at_utc')
    if isinstance(resume_expires, str) and resume_expires:
        session['resume_token_expires_at_utc'] = resume_expires


def reconnect_online_client(session: dict) -> tuple[SessionManagerClientAdapter | None, str, dict | None]:
    """Create a fresh adapter and resume an online session using the stored resume token."""
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    resume_token = session.get('resume_token')
    if not isinstance(game_id, str) or not game_id:
        return None, 'Reconnect unavailable: missing game id', None
    if not isinstance(player_id, str) or not player_id:
        return None, 'Reconnect unavailable: missing player id', None
    if not isinstance(resume_token, str) or not resume_token:
        return None, 'Reconnect unavailable: missing resume token', None

    adapter = SessionManagerClientAdapter(ONLINE_HUB)
    adapter.connect()
    adapter.send(
        'reconnect_request',
        {
            'game_id': game_id,
            'player_id': player_id,
            'resume_token': resume_token,
            'last_seen_event_id': session.get('last_seen_event_id', ''),
        },
    )
    events = adapter.poll()
    accepted = next((e for e in events if e.event_type == 'reconnect_accepted'), None)
    if not accepted:
        rejected = next((e for e in events if e.event_type == 'reconnect_rejected'), None)
        adapter.disconnect()
        if rejected:
            reason = rejected.payload.get('reason', 'reconnect rejected')
            return None, f'Reconnect failed: {reason}', None
        return None, 'Reconnect failed: no server acknowledgement', None

    _update_online_session(session, accepted, adapter)
    return adapter, 'Online session resumed', accepted.payload


def restore_online_session_from_meta(session_meta: dict | None) -> tuple[dict | None, str | None]:
    """Extract reconnectable online session metadata from a loaded save session payload."""
    if not isinstance(session_meta, dict):
        return None, None
    if session_meta.get('mode') != 'online':
        return None, None

    network = session_meta.get('network', {})
    if not isinstance(network, dict):
        return None, None

    restored = {
        'role': str(network.get('role', '')),
        'invite_code': str(network.get('invite_code', '')).upper(),
        'side': str(network.get('side', '')),
        'game_id': str(network.get('game_id', '')),
        'player_id': str(network.get('player_id', '')),
        'resume_token': str(network.get('resume_token', '')),
        'resume_token_expires_at_utc': str(network.get('resume_token_expires_at_utc', '')),
        'last_seen_event_id': str(network.get('last_seen_event_id', '')),
    }
    side = restored.get('side') if restored.get('side') in ('white', 'black') else None
    return restored, side


def apply_reconnect_result(
    game: ChessGame,
    online_session: dict | None,
    online_adapter: SessionManagerClientAdapter | None,
    online_side: str | None,
) -> tuple[SessionManagerClientAdapter | None, str | None, bool, bool, str, tuple[int, int, int]]:
    """Reconnect current online session and apply the returned authoritative snapshot."""
    if online_session is None:
        return online_adapter, online_side, False, False, 'Reconnect unavailable', (255, 120, 120)

    if online_adapter is not None:
        online_adapter.disconnect()

    resumed_adapter, reconnect_status, reconnect_payload = reconnect_online_client(online_session)
    if resumed_adapter is not None and reconnect_payload is not None:
        resumed_side = online_session.get('side', online_side)
        authoritative = reconnect_payload.get('state', {})
        apply_authoritative_state(game, authoritative.get('state', {}))
        apply_authoritative_clock(game, authoritative.get('clock', {}))
        return resumed_adapter, resumed_side, True, False, reconnect_status, (120, 210, 255)

    return None, online_side, False, False, reconnect_status, (255, 120, 120)

# Load piece images once
PIECES = load_pieces()

# Main game loop
game_active = True

while game_active:
    # Show menu and get player choices
    menu = Menu(SCREEN, WIDTH, HEIGHT)
    game_mode, difficulty, ai_color, ai_depth, time_minutes, time_increment, online_role, online_invite = menu.run()

    online_adapter = None
    online_side = None
    online_game_started = False
    online_pending_move = False
    online_session = None
    online_connection_state = 'offline'
    if game_mode == 'online':
        online_adapter, online_status, time_minutes, time_increment, online_side, online_game_started, online_session = bootstrap_online_client(
            online_role,
            online_invite,
            time_minutes,
            time_increment,
        )
        if online_adapter is None:
            print(f"\n{online_status}\n")
            continue
        online_connection_state = 'connected'
        print(f"\n{online_status}\n")

    if game_mode == 'pvp':
        print("\nStarting Player vs Player game")
        print("White moves first - Pass and play!\n")
    elif game_mode == 'online':
        print("\nStarting Online PvP session")
        print("Transport shim connected; gameplay remains local until remote board sync wiring.\n")
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
    if game_mode == 'online':
        status_message = 'Online mode connected. Use Reconnect or Ctrl+R if session recovery is needed'
        status_color = (120, 210, 255)
        status_message_until = pygame.time.get_ticks() + 5000

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not autosave_written:
                    session_meta = build_runtime_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth, online_session)
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
                    session_meta = build_runtime_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth, online_session)
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
                elif event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if game_mode == 'online' and online_session is not None:
                        online_connection_state = 'reconnecting'
                        online_adapter, online_side, online_game_started, online_pending_move, status_message, status_color = apply_reconnect_result(
                            game,
                            online_session,
                            online_adapter,
                            online_side,
                        )
                        online_connection_state = 'resumed' if online_adapter is not None else 'disconnected'
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
                                if loaded_mode not in ('pvp', 'pvai', 'online'):
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
                                    online_adapter = None
                                    online_session = None
                                    online_side = None
                                    online_game_started = False
                                    online_pending_move = False
                                    online_connection_state = 'offline'
                                elif game_mode == 'online':
                                    AI_PLAYER_COLOR = None
                                    ai_player = None
                                    difficulty = 'none'
                                    ai_depth = 0
                                    if online_adapter is not None:
                                        online_adapter.disconnect()
                                    online_adapter = None
                                    online_session, online_side = restore_online_session_from_meta(loaded_session)
                                    online_game_started = False
                                    online_pending_move = False
                                    online_connection_state = 'disconnected' if online_session else 'offline'
                                else:
                                    AI_PLAYER_COLOR = None
                                    ai_player = None
                                    difficulty = 'none'
                                    ai_depth = 0
                                    online_adapter = None
                                    online_session = None
                                    online_side = None
                                    online_game_started = False
                                    online_pending_move = False
                                    online_connection_state = 'offline'

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
                                if game_mode == 'online' and online_session is not None:
                                    status_message = f"Loaded online save: reconnect ready for {(online_side or 'unknown')}"
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
                            session_meta = build_runtime_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth, online_session)
                            autosave_written = perform_autosave(game, session_meta)
                        running = False  # Exit current game loop to restart
                    elif choice == 'end_game':
                        if not autosave_written:
                            session_meta = build_runtime_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth, online_session)
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
                            session_meta = build_runtime_session_meta(game_mode, difficulty, AI_PLAYER_COLOR, ai_depth, online_session)
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
                        elif game_mode == 'online' and game.renderer.is_reconnect_button_clicked(mouse_pos):
                            online_connection_state = 'reconnecting'
                            online_adapter, online_side, online_game_started, online_pending_move, status_message, status_color = apply_reconnect_result(
                                game,
                                online_session,
                                online_adapter,
                                online_side,
                            )
                            online_connection_state = 'resumed' if online_adapter is not None else 'disconnected'
                            status_message_until = pygame.time.get_ticks() + 3500
                            continue
                    
                    # Only allow board clicks when not animating
                    mouse_x, mouse_y = mouse_pos
                    clicked_col = mouse_x // SQUARE_SIZE
                    clicked_row = mouse_y // SQUARE_SIZE
                    
                    # Store the previous board state for comparison
                    old_turn = game.turn
                    
                    if game_mode == 'online' and online_adapter is not None:
                        if not online_game_started:
                            status_message = 'Online waiting for opponent to start'
                            status_color = (255, 200, 120)
                            status_message_until = pygame.time.get_ticks() + 2500
                            continue

                        if online_side not in ('white', 'black'):
                            status_message = 'Online side unresolved'
                            status_color = (255, 120, 120)
                            status_message_until = pygame.time.get_ticks() + 2500
                            continue

                        if online_pending_move:
                            status_message = 'Waiting for server move confirmation'
                            status_color = (200, 200, 200)
                            status_message_until = pygame.time.get_ticks() + 1800
                            continue

                        if game.game_state.current_turn.value != online_side:
                            status_message = "Not your turn"
                            status_color = (255, 200, 120)
                            status_message_until = pygame.time.get_ticks() + 1800
                            continue

                        clicked_position = Position(clicked_row, clicked_col)
                        selected = game.game_state.selected_position
                        piece_at_click = game.board.get_piece(clicked_position)

                        if selected:
                            legal_moves = game.game_state.get_legal_moves_for_position(selected)
                            promotion_moves = [
                                m for m in legal_moves if m.to_pos == clicked_position and m.move_type.name == 'PROMOTION'
                            ]

                            promotion_piece = None
                            if promotion_moves:
                                piece = game.board.get_piece(selected)
                                if piece:
                                    promotion_dialog = PromotionDialog(SCREEN, PIECES, piece.color)
                                    promotion_piece = promotion_dialog.run()

                            target_move = None
                            for move in legal_moves:
                                if move.to_pos != clicked_position:
                                    continue
                                if promotion_piece is None and move.promotion_piece is None:
                                    target_move = move
                                    break
                                if promotion_piece is not None and move.promotion_piece == promotion_piece:
                                    target_move = move
                                    break

                            if target_move:
                                payload = build_move_intent_payload(
                                    game,
                                    from_pos=target_move.from_pos,
                                    to_pos=target_move.to_pos,
                                    promotion_piece=target_move.promotion_piece,
                                )
                                online_adapter.send('move_intent', payload)
                                online_pending_move = True
                                game.game_state.selected_position = None
                                status_message = 'Online move sent'
                                status_color = (120, 210, 255)
                                status_message_until = pygame.time.get_ticks() + 1600
                            else:
                                if piece_at_click and piece_at_click.color.value == online_side:
                                    game.game_state.selected_position = clicked_position
                                else:
                                    game.game_state.selected_position = None
                        else:
                            if (
                                piece_at_click
                                and piece_at_click.color.value == online_side
                                and piece_at_click.color.value == game.game_state.current_turn.value
                            ):
                                game.game_state.selected_position = clicked_position
                            else:
                                game.game_state.selected_position = None

                    else:
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

        # Poll online events for status updates (Phase A shim).
        if game_mode == 'online' and online_adapter is not None:
            for network_event in online_adapter.poll():
                if online_session is not None:
                    _update_online_session(online_session, network_event, online_adapter)

                if network_event.event_type == 'game_start':
                    online_connection_state = 'connected'
                    status_message = 'Online game_start event received'
                    status_color = (120, 210, 255)
                    status_message_until = pygame.time.get_ticks() + 3000
                    online_game_started = True
                    apply_authoritative_state(game, network_event.payload.get('state', {}))
                    apply_authoritative_clock(game, network_event.payload.get('server_clock', {}))
                elif network_event.event_type == 'move_rejected':
                    status_message = f"Online reject: {network_event.payload.get('reason', 'unknown')}"
                    status_color = (255, 150, 120)
                    status_message_until = pygame.time.get_ticks() + 3000
                    online_pending_move = False
                    apply_authoritative_state(game, network_event.payload.get('authoritative_state', {}))
                    if network_event.payload.get('reason') == 'state_desync':
                        online_adapter.send('state_resync_request', {})
                elif network_event.event_type == 'move_accepted':
                    applied = apply_authoritative_move(game, network_event.payload.get('move', {}))
                    apply_authoritative_clock(game, network_event.payload.get('clock', {}))
                    if applied and game.last_move:
                        from_pos, to_pos = game.last_move
                        piece = game.board.get_piece(to_pos)
                        if piece:
                            piece_key = piece.to_string_notation()
                            piece_image = PIECES.get(piece_key)
                            if piece_image:
                                animation_manager.start_animation(from_pos, to_pos, piece_image, SQUARE_SIZE, duration_ms=400)
                    online_pending_move = False
                elif network_event.event_type == 'state_resync':
                    online_connection_state = 'resynced'
                    authoritative_hash = network_event.payload.get('position_hash', '')
                    status_message = f"Online resync hash: {authoritative_hash[:18]}..."
                    status_color = (120, 210, 255)
                    status_message_until = pygame.time.get_ticks() + 2500
                    apply_authoritative_state(game, network_event.payload.get('state', {}))
                    apply_authoritative_clock(game, network_event.payload.get('clock', {}))
                elif network_event.event_type == 'reconnect_accepted':
                    online_connection_state = 'resumed'
                    online_side = online_session.get('side', online_side) if online_session else online_side
                    online_game_started = True
                    online_pending_move = False
                    apply_authoritative_state(game, network_event.payload.get('state', {}).get('state', {}))
                    apply_authoritative_clock(game, network_event.payload.get('state', {}).get('clock', {}))
                    status_message = 'Online session resumed'
                    status_color = (120, 210, 255)
                    status_message_until = pygame.time.get_ticks() + 3000
                elif network_event.event_type == 'reconnect_rejected':
                    online_connection_state = 'disconnected'
                    status_message = f"Reconnect rejected: {network_event.payload.get('reason', 'unknown')}"
                    status_color = (255, 120, 120)
                    status_message_until = pygame.time.get_ticks() + 3000

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
            if game_mode == 'online':
                can_reconnect = bool(online_session and online_session.get('resume_token')) and not animation_manager.is_busy()
                game.renderer.draw_online_controls(
                    can_reconnect=can_reconnect,
                    sidebar_x=BOARD_SIZE,
                    sidebar_width=SIDEBAR_WIDTH,
                    board_height=HEIGHT,
                    invite_code=(online_session or {}).get('invite_code', ''),
                    side=(online_session or {}).get('side', ''),
                    connection_state=online_connection_state,
                    status_detail=status_message if pygame.time.get_ticks() <= status_message_until else '',
                )
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

    if online_adapter is not None:
        online_adapter.disconnect()

# Clean exit
pygame.quit()
print("Game ended. Thanks for playing!")

