"""Klasik mod - standart 2048 oyunu."""

from modes.base_mode import BaseMode
from game.board import Board


class ClassicMode(BaseMode):
    """Standart 2048 oyun modu."""
    
    name = "Klasik"
    description = "Standart 2048 - 2048'e ulaş!"
    
    def __init__(self, board: Board):
        super().__init__(board)
    
    def handle_input(self, direction: str) -> bool:
        """Kullanıcı hareketini işle."""
        return self.board.move(direction)
    
    def update(self) -> None:
        """Klasik modda ekstra güncelleme yok."""
        pass
    
    def is_game_over(self) -> bool:
        """Oyun bitti mi?"""
        return self.board.game_over
    
    def is_won(self) -> bool:
        """2048'e ulaşıldı mı?"""
        return self.board.won
    
    def get_status_text(self) -> str:
        """Durum metni."""
        state = self.board.get_state()
        return f"Klasik | Skor: {state['score']} | En Yüksek: {state['max_tile']}"
