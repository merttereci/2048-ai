"""Benchmark modülü - AI ajanlarını karşılaştır."""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.board import Board
from game.logic import has_valid_moves
from agents.alphabeta import AlphaBetaAgent
from agents.expectimax import ExpectimaxAgent


def run_single_game(agent, board):
    """Tek bir oyun çalıştır (GUI yok)."""
    while has_valid_moves(board.grid):
        move = agent.get_move(board)
        if move:
            board.move(move)
        else:
            break
    
    stats = agent.get_stats()
    return {
        'score': board.score,
        'max_tile': int(board.get_state()['max_tile']),
        'moves': stats['move_count'],
        'time': stats['thinking_time'],
    }


def run_benchmark(agent_class, agent_name: str, depth: int, num_games: int):
    """Benchmark çalıştır."""
    print(f"\n{agent_name} (d={depth}) - {num_games} oyun basliyor...")
    print("-" * 40)
    
    results = []
    for i in range(num_games):
        random.seed(i)  # Her oyun kendi numarasıyla tohumlanır, iki ajan aynı başlangıçları görür
        board = Board()
        agent = agent_class(depth=depth)
        result = run_single_game(agent, board)
        results.append(result)
        print(f"  Oyun {i+1}/{num_games}: Skor={result['score']:,} Max={result['max_tile']} Sure={result['time']:.1f}s")
    
    # Özet
    scores = [r['score'] for r in results]
    max_tiles = [r['max_tile'] for r in results]
    times = [r['time'] for r in results]
    moves = [r['moves'] for r in results]
    
    print(f"\n{'='*40}")
    print(f"{agent_name} (d={depth}) - {num_games} Oyun Ozeti")
    print(f"{'='*40}")
    print(f"Skor     - Ort: {sum(scores)//len(scores):,}  Min: {min(scores):,}  Max: {max(scores):,}")
    print(f"Max Tile - En cok: {max(max_tiles)}  Dagilim: {sorted(set(max_tiles), reverse=True)}")
    print(f"Sure     - Ort: {sum(times)/len(times):.1f}s  Toplam: {sum(times):.1f}s")
    print(f"Hamle    - Ort: {sum(moves)//len(moves)}")
    
    return results


def ask_int(prompt: str, default: int) -> int:
    """Pozitif tam sayı sor. Geçersiz ya da 1'den küçük girişte varsayılanı kullan."""
    raw = input(prompt).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 1 else default


def warm_up():
    """Numba derlemesini ölçümden önce yap, yoksa ilk oyunların süresine eklenir."""
    for agent_class in (AlphaBetaAgent, ExpectimaxAgent):
        agent_class(depth=2).get_move(Board())


def main():
    """Benchmark ana fonksiyonu."""
    print("\n" + "=" * 50)
    print("           2048 - Benchmark Modu")
    print("=" * 50)
    
    num_games = ask_int("\nKac oyun? (varsayilan 10): ", 10)
    ab_depth = ask_int("Alfa-Beta derinligi (varsayilan 4): ", 4)
    ex_depth = ask_int("Expectimax derinligi (varsayilan 4): ", 4)
    
    print("\nNumba derleniyor...")
    warm_up()
    
    print("\nBenchmark basliyor... (GUI yok)")
    
    ab_results = run_benchmark(AlphaBetaAgent, "Alfa-Beta", ab_depth, num_games)
    ex_results = run_benchmark(ExpectimaxAgent, "Expectimax", ex_depth, num_games)
    
    # Karşılaştırma
    ab_avg = sum(r['score'] for r in ab_results) // len(ab_results)
    ex_avg = sum(r['score'] for r in ex_results) // len(ex_results)
    
    print(f"\n{'='*50}")
    print("KARSILASTIRMA")
    print(f"{'='*50}")
    print(f"Alfa-Beta (d={ab_depth})  : {ab_avg:,} ort skor")
    print(f"Expectimax (d={ex_depth}) : {ex_avg:,} ort skor")
    
    if ab_avg > ex_avg:
        print(f"Kazanan: Alfa-Beta (+{ab_avg - ex_avg:,})")
    elif ex_avg > ab_avg:
        print(f"Kazanan: Expectimax (+{ex_avg - ab_avg:,})")
    else:
        print("Berabere!")


if __name__ == "__main__":
    main()
