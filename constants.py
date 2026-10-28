# Ekran ayarları
BOARD_SIZE = 500
WINDOW_WIDTH = BOARD_SIZE
WINDOW_HEIGHT = 560  # Board + status bar

GRID_SIZE = 4
GRID_PADDING = 10
CELL_SIZE = (BOARD_SIZE - (GRID_SIZE + 1) * GRID_PADDING) // GRID_SIZE

# Renkler
BACKGROUND_COLOR = (187, 173, 160)
EMPTY_CELL_COLOR = (205, 193, 180)
TEXT_COLOR_DARK = (119, 110, 101)
TEXT_COLOR_LIGHT = (249, 246, 242)

# Kutucuk renkleri (2048 üstü için de ekledim)
TILE_COLORS = {
    0: (205, 193, 180),
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
    4096: (60, 58, 50),
    8192: (60, 58, 50),
    16384: (60, 58, 50),
    32768: (60, 58, 50),
    65536: (60, 58, 50),
}

# Font boyutları
FONT_SIZES = {
    2: 55,
    4: 55,
    8: 55,
    16: 50,
    32: 50,
    64: 50,
    128: 45,
    256: 45,
    512: 45,
    1024: 35,
    2048: 35,
    4096: 30,
    8192: 30,
    16384: 25,
    32768: 25,
    65536: 22,
}

# Yönler
DIRECTIONS = {
    'up': (-1, 0),
    'down': (1, 0),
    'left': (0, -1),
    'right': (0, 1),
}

# FPS
FPS = 60
