"""
Expectimax Ajanı

Alfa-Beta'dan farkı: MIN katmanı yerine CHANCE katmanı var.
Rastgele spawn'u olasılık ağırlıklı değerlendirir.

Ağaç yapısı:
    MAX (oyuncu hamlesi)
     |
    CHANCE (rastgele spawn: %90 -> 2, %10 -> 4)
     |
    MAX (oyuncu hamlesi)
     ...

Daha gerçekçi ama daha yavaş (budama zor).
"""

import time
import numpy as np
from numba import njit
from agents.base_agent import BaseAgent
from agents.heuristics import evaluate
from game.board import Board
from game.logic import execute_move, grids_equal, get_empty_cells, has_valid_moves, DIRECTION_MAP
from constants import GRID_SIZE


@njit
def expectimax_max(grid, depth):
    """MAX katmanı - oyuncu en iyi hamleyi seçer."""
    if depth == 0 or not has_valid_moves(grid):
        return evaluate(grid), 1
    
    max_score = -1e18
    nodes = 1
    
    for dir_num in range(4):
        new_grid, _ = execute_move(grid, dir_num)
        
        if grids_equal(grid, new_grid):
            continue
        
        score, child_nodes = expectimax_chance(new_grid, depth - 1)
        nodes += child_nodes
        
        if score > max_score:
            max_score = score
    
    if max_score == -1e18:
        return evaluate(grid), nodes
    
    return max_score, nodes


@njit
def expectimax_chance(grid, depth):
    """CHANCE katmanı - rastgele tile spawn."""
    if depth == 0:
        return evaluate(grid), 1
    
    empty_count = get_empty_cells(grid)
    
    if empty_count == 0:
        return expectimax_max(grid, depth)
    
    total_score = 0.0
    prob_per_cell = 1.0 / empty_count
    nodes = 1
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] != 0:
                continue
            
            # 2 spawn (%90)
            grid[i, j] = 2
            score_2, child_nodes = expectimax_max(grid, depth - 1)
            nodes += child_nodes
            
            # 4 spawn (%10)
            grid[i, j] = 4
            score_4, child_nodes = expectimax_max(grid, depth - 1)
            nodes += child_nodes
            
            grid[i, j] = 0
            
            cell_score = 0.9 * score_2 + 0.1 * score_4
            total_score += prob_per_cell * cell_score
    
    return total_score, nodes


class ExpectimaxAgent(BaseAgent):
    """Expectimax kullanan AI ajan."""
    
    name = "Expectimax"
    description = "Olasılık ağırlıklı arama"
    
    def __init__(self, depth: int = 4):
        super().__init__()
        if depth < 1:
            raise ValueError("Derinlik en az 1 olmali")
        self.depth = depth
        self.nodes_explored = 0
    
    def get_move(self, board: Board) -> str | None:
        """En iyi hamleyi bul."""
        start_time = time.perf_counter()
        self.nodes_explored = 0
        
        available_moves = board.get_available_moves()
        if not available_moves:
            return None
        
        best_move = None
        best_score = float('-inf')
        
        for move in available_moves:
            dir_num = DIRECTION_MAP[move]
            new_grid, _ = execute_move(board.grid, dir_num)
            
            score, nodes = expectimax_chance(new_grid, self.depth - 1)
            self.nodes_explored += nodes
            
            if score > best_score:
                best_score = score
                best_move = move
        
        self.move_count += 1
        self.thinking_time += time.perf_counter() - start_time
        
        return best_move
    
    def get_stats(self) -> dict:
        stats = super().get_stats()
        stats['nodes_explored'] = self.nodes_explored
        stats['depth'] = self.depth
        return stats
