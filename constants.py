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

# Time control presets: (name, minutes, increment_seconds)
TIME_CONTROL_PRESETS = [
    ("Bullet 1+0", 1, 0),
    ("Bullet 2+1", 2, 1),
    ("Blitz 3+0", 3, 0),
    ("Blitz 3+2", 3, 2),
    ("Blitz 5+0", 5, 0),
    ("Rapid 10+0", 10, 0),
    ("Rapid 10+5", 10, 5),
    ("Rapid 15+10", 15, 10),
    ("Classical 30+0", 30, 0),
    ("Untimed", 0, 0),
]

ASSETS_PATH = os.path.join(os.path.dirname(__file__), 'assets')