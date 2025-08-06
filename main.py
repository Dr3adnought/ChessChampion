import pygame


from ai.ai_player import AIPlayer
from game.champion_chess import ChessGame
from constants import *


pygame.init()

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Champion")

PIECES = {}


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
    PIECES[name] = load_and_scale_image(name)



game = ChessGame()

AI_PLAYER_COLOR = 'black'
ai_player = AIPlayer(game, AI_PLAYER_COLOR)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            clicked_col = mouse_x // SQUARE_SIZE
            clicked_row = mouse_y // SQUARE_SIZE
            game.handle_click(clicked_row, clicked_col, ai_player_color=AI_PLAYER_COLOR)

    if not game.game_over and game.turn == AI_PLAYER_COLOR:
        pygame.time.wait(500)
        ai_player.make_move()

    game.draw(SCREEN, SQUARE_SIZE, LIGHT_COLOR_SQUARE, DARK_COLOR_SQUARE, HIGHLIGHT_COLOR, PIECES)
    pygame.display.flip()

# --- 5. Quit Pygame ---
pygame.quit()
print("Pygame window closed successfully.")
