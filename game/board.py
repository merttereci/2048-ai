"""Board sınıfı - oyun state'ini yönetir."""

import random
import numpy as np
from constants import GRID_SIZE
from game.logic import (
    execute_move,
    grids_equal,
    get_empty_cells,
    get_empty_positions,
    has_valid_moves,
    get_max_tile,
    DIRECTION_MAP,
    DIRECTION_NAMES,
)


class Board:
    """2048 oyun tahtası."""
    
    def __init__(self, grid=None):
        """Yeni bir tahta oluştur veya mevcut grid ile başlat."""
        if grid is None:
            self.grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int64)
            self._add_random_tile()
            self._add_random_tile()
        else:
            if isinstance(grid, np.ndarray):
                self.grid = grid.copy()
            else:
                self.grid = np.array(grid, dtype=np.int64)
        
        self.score = 0
        self.game_over = False
        self.won = False
    
    def _add_random_tile(self) -> bool:
        """Rastgele boş bir hücreye 2 veya 4 ekle. Başarılıysa True döndür."""
        positions = get_empty_positions(self.grid)
        if not positions:
            return False
        
        row, col = random.choice(positions)
        self.grid[row, col] = 4 if random.random() < 0.1 else 2
        return True
    
    def move(self, direction: str) -> bool:
        """
        Verilen yönde hareket et.
        Hareket geçerliyse True, değilse False döndür.
        """
        if self.game_over:
            return False
        
        old_grid = self.grid.copy()
        dir_num = DIRECTION_MAP[direction]
        new_grid, score = execute_move(self.grid, dir_num)
        
        # Hareket geçerli mi?
        if grids_equal(old_grid, new_grid):
            return False
        
        self.grid = new_grid
        self.score += score
        self._add_random_tile()
        
        # 2048'e ilk ulaşıldığında işaretle, oyun devam eder
        if not self.won and get_max_tile(self.grid) >= 2048:
            self.won = True
        
        # Oyun durumu kontrolü (2048 cap yok, gidebildiği yere kadar)
        if not has_valid_moves(self.grid):
            self.game_over = True
        
        return True
    
    def copy(self) -> 'Board':
        """Tahtanın derin kopyasını döndür (ajan simülasyonu için)."""
        new_board = Board(self.grid)
        new_board.score = self.score
        new_board.game_over = self.game_over
        new_board.won = self.won
        return new_board
    
    def get_available_moves(self) -> list[str]:
        """Geçerli hamlelerin listesini döndür."""
        if self.game_over:
            return []
        
        moves = []
        for direction in DIRECTION_NAMES:
            dir_num = DIRECTION_MAP[direction]
            new_grid, _ = execute_move(self.grid, dir_num)
            if not grids_equal(self.grid, new_grid):
                moves.append(direction)
        
        return moves
    
    def get_state(self) -> dict:
        """Oyun durumunu sözlük olarak döndür."""
        return {
            'grid': self.grid.copy(),
            'score': self.score,
            'game_over': self.game_over,
            'won': self.won,
            'max_tile': get_max_tile(self.grid),
        }
    
    def reset(self) -> None:
        """Oyunu sıfırla."""
        self.grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int64)
        self.score = 0
        self.game_over = False
        self.won = False
        self._add_random_tile()
        self._add_random_tile()
