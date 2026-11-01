"""
Alfa-Beta Pruning Ajanı

Minimax algoritmasının optimize edilmiş versiyonu.
2048'i adversarial game olarak modeller:
- MAX: Oyuncu (en iyi hamleyi seçer)
- MIN: Rastgele spawn (en kötü pozisyona tile koyar varsayımı)

Not: 2048'de MIN aslında rastgele, akıllı değil.
Bu yüzden alfa-beta biraz pesimist/savunmacı oynar.
Daha gerçekçi bir yaklaşım için expectimax kullanılabilir.
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
def alphabeta_max(grid, depth, alpha, beta):
    """MAX katmanı - oyuncu hamlesi."""
    if depth == 0 or not has_valid_moves(grid):
        return evaluate(grid), 1
    
    max_score = -1e18
    nodes = 1
    
    for dir_num in range(4):
        new_grid, _ = execute_move(grid, dir_num)
        
        if grids_equal(grid, new_grid):
            continue
        
        score, child_nodes = alphabeta_min(new_grid, depth - 1, alpha, beta)
        nodes += child_nodes
        
        if score > max_score:
            max_score = score
        
        if max_score >= beta:
            return max_score, nodes
        alpha = max(alpha, max_score)
    
    if max_score == -1e18:
        return evaluate(grid), nodes
    
    return max_score, nodes


@njit
def alphabeta_min(grid, depth, alpha, beta):
    """MIN katmanı - tile spawn."""
    if depth == 0:
        return evaluate(grid), 1
    
    empty_count = get_empty_cells(grid)
    
    if empty_count == 0:
        return alphabeta_max(grid, depth, alpha, beta)
    
    min_score = 1e18
    nodes = 1
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i, j] != 0:
                continue
            
            # 2 koy
            grid[i, j] = 2
            score, child_nodes = alphabeta_max(grid, depth - 1, alpha, beta)
            grid[i, j] = 0
            nodes += child_nodes
            
            if score < min_score:
                min_score = score
            
            if min_score <= alpha:
                return min_score, nodes
            beta = min(beta, min_score)
            
            # 4 koy
            grid[i, j] = 4
            score, child_nodes = alphabeta_max(grid, depth - 1, alpha, beta)
            grid[i, j] = 0
            nodes += child_nodes
            
            if score < min_score:
                min_score = score
            
            if min_score <= alpha:
                return min_score, nodes
            beta = min(beta, min_score)
    
    return min_score, nodes


class AlphaBetaAgent(BaseAgent):
    """Alfa-Beta pruning kullanan AI ajan."""
    
    name = "Alfa-Beta"
    description = "Minimax + Alfa-Beta budama"
    
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
        alpha = float('-inf')
        beta = float('inf')
        
        for move in available_moves:
            dir_num = DIRECTION_MAP[move]
            new_grid, _ = execute_move(board.grid, dir_num)
            
            score, nodes = alphabeta_min(new_grid, self.depth - 1, alpha, beta)
            self.nodes_explored += nodes
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
        
        self.move_count += 1
        self.thinking_time += time.perf_counter() - start_time
        
        return best_move
    
    def get_stats(self) -> dict:
        stats = super().get_stats()
        stats['nodes_explored'] = self.nodes_explored
        stats['depth'] = self.depth
        return stats
