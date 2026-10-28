"""Oyun mantığı - saf fonksiyonlar, side effect yok."""

import numpy as np
from numba import njit
from constants import GRID_SIZE


@njit
def slide_row_left(row):
    """Bir satırı sola kaydır ve birleştir. Yeni satır ve kazanılan skoru döndür."""
    # Sıfırları filtrele
    non_zero = []
    for x in row:
        if x != 0:
            non_zero.append(x)
    
    # Birleştir
    merged = []
    score = 0
    skip = False
    
    for i in range(len(non_zero)):
        if skip:
            skip = False
            continue
        if i + 1 < len(non_zero) and non_zero[i] == non_zero[i + 1]:
            merged.append(non_zero[i] * 2)
            score += non_zero[i] * 2
            skip = True
        else:
            merged.append(non_zero[i])
    
    # Sıfırlarla doldur
    while len(merged) < GRID_SIZE:
        merged.append(0)
    
    result = np.zeros(GRID_SIZE, dtype=np.int64)
    for i in range(len(merged)):
        result[i] = merged[i]
    
    return result, score


@njit
def move_left(grid):
    """Tüm ızgarayı sola kaydır."""
    new_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int64)
    total_score = 0
    
    for i in range(GRID_SIZE):
        new_row, score = slide_row_left(grid[i])
        new_grid[i] = new_row
        total_score += score
    
    return new_grid, total_score


@njit
def move_right(grid):
    """Tüm ızgarayı sağa kaydır."""
    new_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int64)
    total_score = 0
    
    for i in range(GRID_SIZE):
        reversed_row = grid[i][::-1].copy()
        new_row, score = slide_row_left(reversed_row)
        new_grid[i] = new_row[::-1]
        total_score += score
    
    return new_grid, total_score


@njit
def move_up(grid):
    """Tüm ızgarayı yukarı kaydır."""
    new_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int64)
    total_score = 0
    
    for j in range(GRID_SIZE):
        col = grid[:, j].copy()
        new_col, score = slide_row_left(col)
        new_grid[:, j] = new_col
        total_score += score
    
    return new_grid, total_score


@njit
def move_down(grid):
    """Tüm ızgarayı aşağı kaydır."""
    new_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int64)
    total_score = 0
    
    for j in range(GRID_SIZE):
        col = grid[:, j][::-1].copy()
        new_col, score = slide_row_left(col)
        new_grid[:, j] = new_col[::-1]
        total_score += score
    
    return new_grid, total_score


@njit
def execute_move(grid, direction):
    """Verilen yönde hareket et. Yeni grid ve skoru döndür."""
    if direction == 0:  # left
        return move_left(grid)
    elif direction == 1:  # right
        return move_right(grid)
    elif direction == 2:  # up
        return move_up(grid)
    elif direction == 3:  # down
        return move_down(grid)
    return grid.copy(), 0


@njit
def grids_equal(grid1, grid2):
    """İki ızgara eşit mi kontrol et."""
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid1[i, j] != grid2[i, j]:
                return False
    return True


@njit
def get_empty_cells(grid):
    """Boş hücre sayısını döndür."""
    count = 0
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] == 0:
                count += 1
    return count


@njit
def get_empty_positions(grid):
    """Boş hücrelerin pozisyonlarını döndür."""
    positions = []
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] == 0:
                positions.append((i, j))
    return positions


@njit
def has_valid_moves(grid):
    """Geçerli hamle var mı kontrol et."""
    # Boş hücre var mı?
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] == 0:
                return True
    
    # Yan yana aynı değerler var mı?
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            current = grid[i, j]
            # Sağ komşu
            if j + 1 < GRID_SIZE and grid[i, j + 1] == current:
                return True
            # Alt komşu
            if i + 1 < GRID_SIZE and grid[i + 1, j] == current:
                return True
    
    return False


@njit
def get_max_tile(grid):
    """En büyük kutucuk değerini döndür."""
    max_val = 0
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] > max_val:
                max_val = grid[i, j]
    return max_val


# Yön sabitleri
DIR_LEFT = 0
DIR_RIGHT = 1
DIR_UP = 2
DIR_DOWN = 3

DIRECTION_MAP = {
    'left': DIR_LEFT,
    'right': DIR_RIGHT,
    'up': DIR_UP,
    'down': DIR_DOWN,
}

DIRECTION_NAMES = ['left', 'right', 'up', 'down']
