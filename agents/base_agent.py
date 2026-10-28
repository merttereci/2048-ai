"""Soyut ajan sınıfı - tüm AI ajanları bundan türer."""

from abc import ABC, abstractmethod
from game.board import Board


class BaseAgent(ABC):
    """AI ajan için soyut temel sınıf."""
    
    name: str = "Base Agent"
    description: str = "Temel AI ajan"
    
    def __init__(self):
        self.move_count = 0
        self.thinking_time = 0.0
    
    @abstractmethod
    def get_move(self, board: Board) -> str | None:
        """
        Verilen board durumu için en iyi hamleyi hesapla.
        Geçerli hamle yoksa None döndür.
        
        Args:
            board: Mevcut oyun tahtası (kopyalanabilir)
        
        Returns:
            'up', 'down', 'left', 'right' veya None
        """
        pass
    
    def reset(self) -> None:
        """Ajan istatistiklerini sıfırla."""
        self.move_count = 0
        self.thinking_time = 0.0
    
    def get_stats(self) -> dict:
        """Ajan istatistiklerini döndür."""
        return {
            'name': self.name,
            'move_count': self.move_count,
            'thinking_time': self.thinking_time,
            'avg_time_per_move': (
                self.thinking_time / self.move_count 
                if self.move_count > 0 else 0
            ),
        }
