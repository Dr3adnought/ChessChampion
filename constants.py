import os

# Board dimensions
BOARD_SIZE = 800
SQUARE_SIZE = BOARD_SIZE // 8

# Sidebar for captured pieces
SIDEBAR_WIDTH = 200
WIDTH = BOARD_SIZE + SIDEBAR_WIDTH
HEIGHT = BOARD_SIZE

LIGHT_COLOR_SQUARE = (238, 238, 210)
DARK_COLOR_SQUARE = (118, 150, 86)
HIGHLIGHT_COLOR = (255, 255, 0, 100)

ASSETS_PATH = os.path.join(os.path.dirname(__file__), 'assets')