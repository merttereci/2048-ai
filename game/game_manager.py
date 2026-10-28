"""GameManager - oyun akışı ve mod yönetimi."""

import pygame
from game.board import Board
from modes.base_mode import BaseMode
from agents.base_agent import BaseAgent
from renderer.pygame_renderer import PygameRenderer
from constants import FPS


class GameManager:
    """Oyun akışını ve modları yöneten sınıf."""
    
    # Tuş eşlemeleri
    KEY_MAP = {
        pygame.K_UP: 'up',
        pygame.K_DOWN: 'down',
        pygame.K_LEFT: 'left',
        pygame.K_RIGHT: 'right',
        pygame.K_w: 'up',
        pygame.K_s: 'down',
        pygame.K_a: 'left',
        pygame.K_d: 'right',
    }
    
    def __init__(self, mode: BaseMode, agent: BaseAgent | None = None):
        """
        Args:
            mode: Oyun modu
            agent: Opsiyonel AI ajan (auto-play için)
        """
        self.mode = mode
        self.agent = agent
        self.renderer = PygameRenderer()
        self.clock = pygame.time.Clock()
        self.running = False
        self.auto_play = False
        
        # İstatistik geçmişi (oyun sonu grafiği için)
        self.stats_history = {
            'nodes': [],
            'times': [],
            'scores': [],
        }
        self.last_thinking_time = 0
    
    def _handle_events(self) -> None:
        """Pygame eventlerini işle."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
    
    def _handle_key(self, key: int) -> None:
        """Tuş basımını işle."""
        # Çıkış
        if key == pygame.K_q or key == pygame.K_ESCAPE:
            self.running = False
            return
        
        # Yeniden başla
        if key == pygame.K_r:
            self.mode.reset()
            self._reset_stats()
            if self.agent:
                self.agent.reset()
            return
        
        # Auto-play toggle (ajan varsa)
        if key == pygame.K_SPACE and self.agent:
            self.auto_play = not self.auto_play
            return
        
        # Oyun bittiyse hareket kabul etme
        if self.mode.is_game_over():
            return
        
        # Hareket tuşları
        if key in self.KEY_MAP:
            direction = self.KEY_MAP[key]
            self.mode.handle_input(direction)
    
    def _reset_stats(self) -> None:
        """İstatistikleri sıfırla."""
        self.stats_history = {
            'nodes': [],
            'times': [],
            'scores': [],
        }
        self.last_thinking_time = 0
    
    def _record_stats(self) -> None:
        """Her hamle sonrası istatistik kaydet."""
        if not self.agent:
            return
        
        stats = self.agent.get_stats()
        
        # Bu hamlenin süresi
        current_thinking = stats.get('thinking_time', 0)
        move_time = (current_thinking - self.last_thinking_time) * 1000  # ms
        self.last_thinking_time = current_thinking
        
        self.stats_history['nodes'].append(stats.get('nodes_explored', 0))
        self.stats_history['times'].append(move_time)
        self.stats_history['scores'].append(self.mode.board.score)
    
    def _agent_move(self) -> None:
        """Ajan hamlesi yap."""
        if not self.agent or not self.auto_play:
            return
        
        if self.mode.is_game_over():
            self.auto_play = False
            return
        
        move = self.agent.get_move(self.mode.board)
        if move:
            self.mode.handle_input(move)
            self._record_stats()
    
    def _get_status_text(self) -> str:
        """Durum çubuğu metnini oluştur."""
        text = self.mode.get_status_text()
        
        if self.agent:
            if self.auto_play:
                text += " | [AUTO]"
            else:
                text += " | Space: Baslat"
        
        return text
    
    def get_stats_history(self) -> dict:
        """İstatistik geçmişini döndür."""
        return self.stats_history
    
    def run(self) -> None:
        """Ana oyun döngüsü."""
        self.running = True
        
        while self.running:
            self._handle_events()
            
            # Ajan hamlesi (delay yok)
            if self.auto_play:
                self._agent_move()
            
            # Mod güncelleme
            self.mode.update()
            
            # Render
            self.renderer.render(
                grid=self.mode.board.grid,
                status_text=self._get_status_text(),
                game_over=self.mode.is_game_over(),
            )
            
            self.clock.tick(FPS)
        
        self.renderer.quit()
