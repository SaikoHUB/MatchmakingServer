from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import math

@dataclass
class PlayerStats:
    player_id: str
    username: str
    display_name: str
    elo_rating: float
    games_played: int
    wins: int
    losses: int
    draws: int
    win_streak: int
    best_win_streak: int
    last_game: Optional[datetime]
    rank: Optional[int] = None

class RankingSystem:
    def __init__(self, k_factor: float = 32, initial_elo: float = 1000):
        self.k_factor = k_factor
        self.initial_elo = initial_elo
        self.players: Dict[str, PlayerStats] = {}
        
    def add_player(self, player_id: str, username: str, display_name: str) -> PlayerStats:
        """Ajoute un nouveau joueur au système de classement"""
        if player_id not in self.players:
            self.players[player_id] = PlayerStats(
                player_id=player_id,
                username=username,
                display_name=display_name,
                elo_rating=self.initial_elo,
                games_played=0,
                wins=0,
                losses=0,
                draws=0,
                win_streak=0,
                best_win_streak=0,
                last_game=None
            )
        return self.players[player_id]
    
    def update_ratings(self, winner_id: str, loser_id: str, is_draw: bool = False) -> None:
        """Met à jour les classements après une partie"""
        if winner_id not in self.players or loser_id not in self.players:
            return
            
        winner = self.players[winner_id]
        loser = self.players[loser_id]
        
        # Calcule les probabilités de victoire
        winner_expected = 1 / (1 + math.pow(10, (loser.elo_rating - winner.elo_rating) / 400))
        loser_expected = 1 - winner_expected
        
        if is_draw:
            # Match nul
            winner.elo_rating += self.k_factor * (0.5 - winner_expected)
            loser.elo_rating += self.k_factor * (0.5 - loser_expected)
            winner.draws += 1
            loser.draws += 1
            winner.win_streak = 0
            loser.win_streak = 0
        else:
            # Victoire/Défaite
            winner.elo_rating += self.k_factor * (1 - winner_expected)
            loser.elo_rating += self.k_factor * (0 - loser_expected)
            winner.wins += 1
            loser.losses += 1
            winner.win_streak += 1
            loser.win_streak = 0
            winner.best_win_streak = max(winner.best_win_streak, winner.win_streak)
        
        winner.games_played += 1
        loser.games_played += 1
        winner.last_game = datetime.now()
        loser.last_game = datetime.now()
        
        # Met à jour les rangs
        self._update_ranks()
    
    def _update_ranks(self) -> None:
        """Met à jour les rangs de tous les joueurs"""
        # Trie les joueurs par ELO
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: (-p.elo_rating, -p.wins, p.games_played)
        )
        
        # Attribue les rangs
        for i, player in enumerate(sorted_players, 1):
            player.rank = i
    
    def get_leaderboard(self, limit: int = 10) -> List[PlayerStats]:
        """Récupère le classement des meilleurs joueurs"""
        return sorted(
            self.players.values(),
            key=lambda p: (-p.elo_rating, -p.wins, p.games_played)
        )[:limit]
    
    def get_player_stats(self, player_id: str) -> Optional[PlayerStats]:
        """Récupère les statistiques d'un joueur"""
        return self.players.get(player_id)
    
    def get_player_rank(self, player_id: str) -> Optional[int]:
        """Récupère le rang d'un joueur"""
        player = self.players.get(player_id)
        return player.rank if player else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le système de classement en dictionnaire"""
        return {
            'k_factor': self.k_factor,
            'initial_elo': self.initial_elo,
            'players': {
                player_id: {
                    'player_id': stats.player_id,
                    'username': stats.username,
                    'display_name': stats.display_name,
                    'elo_rating': stats.elo_rating,
                    'games_played': stats.games_played,
                    'wins': stats.wins,
                    'losses': stats.losses,
                    'draws': stats.draws,
                    'win_streak': stats.win_streak,
                    'best_win_streak': stats.best_win_streak,
                    'last_game': stats.last_game.isoformat() if stats.last_game else None,
                    'rank': stats.rank
                }
                for player_id, stats in self.players.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RankingSystem':
        """Crée un système de classement à partir d'un dictionnaire"""
        system = cls(
            k_factor=data.get('k_factor', 32),
            initial_elo=data.get('initial_elo', 1000)
        )
        
        for player_id, stats_data in data.get('players', {}).items():
            system.players[player_id] = PlayerStats(
                player_id=stats_data['player_id'],
                username=stats_data['username'],
                display_name=stats_data['display_name'],
                elo_rating=stats_data['elo_rating'],
                games_played=stats_data['games_played'],
                wins=stats_data['wins'],
                losses=stats_data['losses'],
                draws=stats_data['draws'],
                win_streak=stats_data['win_streak'],
                best_win_streak=stats_data['best_win_streak'],
                last_game=datetime.fromisoformat(stats_data['last_game']) if stats_data['last_game'] else None,
                rank=stats_data['rank']
            )
        
        return system 