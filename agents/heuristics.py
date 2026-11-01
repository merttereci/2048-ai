"""
Heuristik fonksiyonları - board değerlendirme.

Kullanılan heuristikler:
1. Monotonluk: Satır/sütunların artan veya azalan sırada olması
2. Boş hücre sayısı: Daha fazla boşluk = daha fazla manevra
3. Birleştirme potansiyeli: Yan yana eşit değerler
4. Köşe bonusu: En büyük kutucuk köşede mi?
5. Pürüzsüzlük: Komşu hücreler arası fark (düşük = iyi)
6. Yılan deseni: Kutucukların sol üst köşeden başlayan yılan sırasına dizilmesi
"""

import math
import numpy as np
from numba import njit
from constants import GRID_SIZE


@njit
def monotonicity(grid):
    """
    Monotonluk skoru.
    Satır ve sütunların artan/azalan sırada olması tercih edilir.
    Yüksek skor = daha monoton = daha iyi.
    """
    score = 0
    
    # Satırlar için
    for i in range(GRID_SIZE):
        inc = 0
        dec = 0
        for j in range(GRID_SIZE - 1):
            if grid[i, j] <= grid[i, j + 1]:
                inc += 1
            if grid[i, j] >= grid[i, j + 1]:
                dec += 1
        score += max(inc, dec)
    
    # Sütunlar için
    for j in range(GRID_SIZE):
        inc = 0
        dec = 0
        for i in range(GRID_SIZE - 1):
            if grid[i, j] <= grid[i + 1, j]:
                inc += 1
            if grid[i, j] >= grid[i + 1, j]:
                dec += 1
        score += max(inc, dec)
    
    return score


@njit
def empty_cells(grid):
    """Boş hücre sayısı. Daha fazla = daha iyi."""
    count = 0
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] == 0:
                count += 1
    return count


@njit
def merge_potential(grid):
    """
    Birleştirme potansiyeli.
    Yan yana (yatay/dikey) eşit değerli hücre sayısı.
    """
    count = 0
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] == 0:
                continue
            # Sağ komşu
            if j + 1 < GRID_SIZE and grid[i, j] == grid[i, j + 1]:
                count += 1
            # Alt komşu
            if i + 1 < GRID_SIZE and grid[i, j] == grid[i + 1, j]:
                count += 1
    
    return count


@njit
def corner_bonus(grid):
    """
    Köşe bonusu.
    En büyük kutucuk köşede ise bonus ver.
    """
    max_val = 0
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] > max_val:
                max_val = grid[i, j]
    
    corners = [
        grid[0, 0], grid[0, GRID_SIZE - 1],
        grid[GRID_SIZE - 1, 0], grid[GRID_SIZE - 1, GRID_SIZE - 1]
    ]
    
    for c in corners:
        if c == max_val:
            return max_val
    return 0


@njit
def smoothness(grid):
    """
    Pürüzsüzlük (negatif skor).
    Komşu hücreler arası fark ne kadar az o kadar iyi.
    Log2 kullanarak büyük farkları cezalandır.
    """
    penalty = 0.0
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] == 0:
                continue
            
            val = math.log2(grid[i, j]) if grid[i, j] > 0 else 0
            
            # Sağ komşu
            if j + 1 < GRID_SIZE and grid[i, j + 1] != 0:
                neighbor = math.log2(grid[i, j + 1])
                penalty += abs(val - neighbor)
            
            # Alt komşu
            if i + 1 < GRID_SIZE and grid[i + 1, j] != 0:
                neighbor = math.log2(grid[i + 1, j])
                penalty += abs(val - neighbor)
    
    return -penalty


@njit
def snake_pattern(grid):
    """
    Yılan deseni bonusu.
    Sol üst köşeden başlayıp yılan gibi inen bir sıralama.
    Bu desen 2048'de çok etkili.
    """
    weights = np.array([
        [2**15, 2**14, 2**13, 2**12],
        [2**8,  2**9,  2**10, 2**11],
        [2**7,  2**6,  2**5,  2**4],
        [2**0,  2**1,  2**2,  2**3],
    ], dtype=np.float64)
    
    score = 0.0
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            score += grid[i, j] * weights[i, j]
    
    return score


@njit
def evaluate(grid):
    """
    Board'u değerlendir.
    
    Returns:
        Değerlendirme skoru (yüksek = iyi)
    """
    w_empty = 270.0
    w_mono = 47.0
    w_smooth = 10.0
    w_merge = 700.0
    w_corner = 1.0
    w_snake = 0.1
    
    score = 0.0
    score += w_empty * empty_cells(grid)
    score += w_mono * monotonicity(grid)
    score += w_smooth * smoothness(grid)
    score += w_merge * merge_potential(grid)
    score += w_corner * corner_bonus(grid)
    score += w_snake * snake_pattern(grid)
    
    return score
