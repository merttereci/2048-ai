"""2048 Oyunu - Ana giriş noktası."""

import sys
import os

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.board import Board
from game.game_manager import GameManager
from modes.classic import ClassicMode
from agents.alphabeta import AlphaBetaAgent
from agents.expectimax import ExpectimaxAgent


def print_menu():
    """Menüyü göster."""
    print("\n" + "=" * 50)
    print("              2048 - Pygame Edition")
    print("=" * 50)
    print("\nMod Sec:")
    print("  1. Manuel oyna")
    print("  2. Alfa-Beta AI izle")
    print("  3. Expectimax AI izle")
    print("  q. Cikis")
    print("=" * 50)


def print_controls(agent=None):
    """Kontrolleri göster."""
    print("\nKontroller:")
    print("  Oklar veya WASD : Hareket")
    print("  R               : Yeniden Basla")
    print("  Q / ESC         : Cikis")
    if agent:
        print("  SPACE           : Auto-play Ac/Kapa")
    print("\n" + "=" * 50)


def show_graphs(history: dict, agent_name: str, score: int, max_tile: int, depth: int):
    """Oyun sonu grafiklerini göster ve kaydet."""
    try:
        import matplotlib.pyplot as plt
        from datetime import datetime
    except ImportError:
        print("\nGrafik icin matplotlib gerekli: pip install matplotlib")
        return
    
    if not history['nodes']:
        print("\nGrafik icin yeterli veri yok.")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f'{agent_name} (d={depth}) | Skor: {score} | Max: {max_tile}', fontsize=14)
    
    moves = range(1, len(history['nodes']) + 1)
    
    # Nodes vs Hamle
    axes[0, 0].plot(moves, history['nodes'], 'b-', linewidth=0.8)
    axes[0, 0].set_xlabel('Hamle')
    axes[0, 0].set_ylabel('Nodes')
    axes[0, 0].set_title(f'Ziyaret Edilen Node (ort: {sum(history["nodes"])//len(history["nodes"]):,})')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Süre vs Hamle
    axes[0, 1].plot(moves, history['times'], 'r-', linewidth=0.8)
    axes[0, 1].set_xlabel('Hamle')
    axes[0, 1].set_ylabel('Sure (ms)')
    axes[0, 1].set_title(f'Hamle Suresi (ort: {sum(history["times"])/len(history["times"]):.1f}ms)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Skor vs Hamle
    axes[1, 0].plot(moves, history['scores'], 'g-', linewidth=0.8)
    axes[1, 0].set_xlabel('Hamle')
    axes[1, 0].set_ylabel('Skor')
    axes[1, 0].set_title('Skor Gelisimi')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Node dağılımı histogram
    axes[1, 1].hist(history['nodes'], bins=30, color='purple', alpha=0.7)
    axes[1, 1].set_xlabel('Nodes')
    axes[1, 1].set_ylabel('Frekans')
    axes[1, 1].set_title('Node Dagilimi')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Kaydet
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{agent_name.lower().replace('-', '')}_d{depth}_{score}_{timestamp}.png"
    plt.savefig(filename, dpi=150)
    print(f"\nGrafik kaydedildi: {filename}")
    
    plt.show()


def ask_depth(default: int = 4) -> int:
    """Arama derinliğini sor. Geçersiz ya da 1'den küçük girişte varsayılanı kullan."""
    print("Derinlik katman sayisidir, oyuncu hamlesi ve tas cikisi ayri sayilir.")
    print("Ornegin 4, iki oyuncu hamlesi ve iki tas cikisi ileriye bakar.")
    raw = input(f"Arama derinligi (varsayilan {default}): ").strip()
    try:
        depth = int(raw)
    except ValueError:
        return default
    return depth if depth >= 1 else default


def run_ai_game(agent, agent_name: str, depth: int):
    """AI oyunu çalıştır ve sonuçları göster."""
    # Numba derlemesini önceden yap, yoksa ilk hamlenin süresine eklenir
    print("\nNumba derleniyor...")
    agent.get_move(Board())
    agent.reset()
    
    board = Board()
    mode = ClassicMode(board)
    game = GameManager(mode, agent=agent)
    
    print_controls(agent)
    print(f"\n{agent_name} basliyor (derinlik: {depth})...")
    print("SPACE ile auto-play'i baslat!")
    
    game.run()
    
    # Terminal istatistikleri
    stats = agent.get_stats()
    print(f"\n--- {agent_name} Istatistikleri ---")
    print(f"Final Skor: {board.score}")
    print(f"En Yuksek Kutucuk: {board.get_state()['max_tile']}")
    print(f"Toplam Hamle: {stats['move_count']}")
    print(f"Toplam Dusunme Suresi: {stats['thinking_time']:.2f}s")
    print(f"Ortalama Hamle Suresi: {stats['avg_time_per_move']*1000:.1f}ms")
    
    # Grafik göster
    history = game.get_stats_history()
    if history['nodes']:
        show_graph = input("\nGrafikleri goster? (e/h): ").strip().lower()
        if show_graph == 'e':
            show_graphs(history, agent_name, board.score, board.get_state()['max_tile'], depth)


def main():
    """Oyunu başlat."""
    while True:
        print_menu()
        choice = input("\nSecim: ").strip().lower()
        
        if choice == 'q':
            print("Gorusuruz!")
            break
        
        elif choice == '1':
            # Manuel mod
            board = Board()
            mode = ClassicMode(board)
            game = GameManager(mode)
            print_controls()
            game.run()
            print(f"\nFinal Skor: {board.score}")
            print(f"En Yuksek Kutucuk: {board.get_state()['max_tile']}")
        
        elif choice == '2':
            # Alfa-Beta AI
            depth = ask_depth()
            agent = AlphaBetaAgent(depth=depth)
            run_ai_game(agent, "Alfa-Beta", depth)
        
        elif choice == '3':
            # Expectimax AI
            depth = ask_depth()
            agent = ExpectimaxAgent(depth=depth)
            run_ai_game(agent, "Expectimax", depth)
        
        else:
            print("Gecersiz secim!")


if __name__ == "__main__":
    main()
