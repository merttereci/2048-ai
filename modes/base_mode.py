"""Soyut mod sınıfı - tüm oyun modları bundan türer."""

from abc import ABC, abstractmethod
from game.board import Board


class BaseMode(ABC):
    """Oyun modu için soyut temel sınıf."""
    
    name: str = "Base Mode"
    description: str = "Temel oyun modu"
    
    def __init__(self, board: Board):
        self.board = board
    
    @abstractmethod
    def handle_input(self, direction: str) -> bool:
        """
        Kullanıcı girdisini işle.
        Hareket yapıldıysa True döndür.
        """
        pass
    
    @abstractmethod
    def update(self) -> None:
        """Her frame çağrılır. Mod-spesifik güncellemeler için."""
        pass
    
    @abstractmethod
    def is_game_over(self) -> bool:
        """Oyun bitti mi kontrol et."""
        pass
    
    @abstractmethod
    def is_won(self) -> bool:
        """Oyun kazanıldı mı kontrol et."""
        pass
    
    def get_status_text(self) -> str:
        """Durum çubuğunda gösterilecek metin."""
        return f"{self.name} | Skor: {self.board.score}"
    
    def reset(self) -> None:
        """Modu sıfırla."""
        self.board.reset()
