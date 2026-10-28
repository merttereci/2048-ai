"""Pygame renderer - sadece oyun tahtası."""

import pygame
from constants import (
    BOARD_SIZE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    GRID_SIZE,
    GRID_PADDING,
    CELL_SIZE,
    BACKGROUND_COLOR,
    TILE_COLORS,
    TEXT_COLOR_DARK,
    TEXT_COLOR_LIGHT,
    FONT_SIZES,
)


class PygameRenderer:
    """Pygame ile oyun çizimi."""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("2048")
        
        self.status_bar_height = 60
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        
        self.fonts = {}
        self._init_fonts()
    
    def _init_fonts(self) -> None:
        """Fontları başlat."""
        for value, size in FONT_SIZES.items():
            self.fonts[value] = pygame.font.Font(None, size)
        
        self.status_font = pygame.font.Font(None, 30)
        self.game_over_font = pygame.font.Font(None, 60)
    
    def _get_tile_color(self, value: int) -> tuple[int, int, int]:
        """Kutucuk rengini döndür."""
        if value in TILE_COLORS:
            return TILE_COLORS[value]
        return (60, 58, 50)
    
    def _get_text_color(self, value: int) -> tuple[int, int, int]:
        """Metin rengini döndür."""
        return TEXT_COLOR_DARK if value <= 4 else TEXT_COLOR_LIGHT
    
    def _get_font(self, value: int) -> pygame.font.Font:
        """Değere uygun fontu döndür."""
        if value in self.fonts:
            return self.fonts[value]
        return pygame.font.Font(None, 22)
    
    def _draw_tile(self, value: int, row: int, col: int) -> None:
        """Tek bir kutucuk çiz."""
        x = GRID_PADDING + col * (CELL_SIZE + GRID_PADDING)
        y = GRID_PADDING + row * (CELL_SIZE + GRID_PADDING) + self.status_bar_height
        
        color = self._get_tile_color(value)
        pygame.draw.rect(
            self.screen,
            color,
            (x, y, CELL_SIZE, CELL_SIZE),
            border_radius=8
        )
        
        if value != 0:
            font = self._get_font(value)
            text_color = self._get_text_color(value)
            text = font.render(str(value), True, text_color)
            text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
            self.screen.blit(text, text_rect)
    
    def draw_board(self, grid: list[list[int]]) -> None:
        """Tahtayı çiz."""
        board_rect = (0, self.status_bar_height, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(self.screen, BACKGROUND_COLOR, board_rect, border_radius=10)
        
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                self._draw_tile(grid[row][col], row, col)
    
    def draw_status_bar(self, text: str) -> None:
        """Durum çubuğunu çiz."""
        pygame.draw.rect(
            self.screen,
            (250, 248, 239),
            (0, 0, WINDOW_WIDTH, self.status_bar_height)
        )
        
        text_surface = self.status_font.render(text, True, TEXT_COLOR_DARK)
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, self.status_bar_height // 2))
        self.screen.blit(text_surface, text_rect)
    
    def draw_game_over(self) -> None:
        """Oyun sonu ekranı."""
        overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, self.status_bar_height))
        
        text = self.game_over_font.render("Oyun Bitti!", True, (255, 255, 255))
        text_rect = text.get_rect(center=(BOARD_SIZE // 2, self.status_bar_height + BOARD_SIZE // 2 - 30))
        self.screen.blit(text, text_rect)
        
        restart_text = self.status_font.render("R: Yeniden | Q: Cikis", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(BOARD_SIZE // 2, self.status_bar_height + BOARD_SIZE // 2 + 30))
        self.screen.blit(restart_text, restart_rect)
    
    def render(self, grid: list[list[int]], status_text: str, game_over: bool = False) -> None:
        """Tam ekranı render et."""
        self.screen.fill((250, 248, 239))
        self.draw_status_bar(status_text)
        self.draw_board(grid)
        
        if game_over:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def quit(self) -> None:
        """Pygame'i kapat."""
        pygame.quit()
