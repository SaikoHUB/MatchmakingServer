from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import os

@dataclass
class GameMove:
    player_id: str
    move: tuple
    timestamp: datetime
    move_number: int

@dataclass
class GameResult:
    winner_id: Optional[str]
    is_draw: bool
    end_reason: str  # 'win', 'draw', 'timeout', 'forfeit'
    final_board: List[List[int]]
    duration: float  # en secondes

@dataclass
class GameRecord:
    game_id: str
    game_name: str
    start_time: datetime
    end_time: datetime
    players: List[Dict[str, Any]]  # [{id, username, display_name, elo_before, elo_after}]
    moves: List[GameMove]
    result: GameResult
    ranked: bool
    game_config: Dict[str, Any]

class GameHistory:
    def __init__(self, save_dir: str = "game_history"):
        self.save_dir = save_dir
        self.games: Dict[str, GameRecord] = {}
        self._ensure_save_dir()
    
    def _ensure_save_dir(self) -> None:
        """Crée le répertoire de sauvegarde s'il n'existe pas"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    def add_game(self, game: GameRecord) -> None:
        """Ajoute une partie à l'historique"""
        self.games[game.game_id] = game
        self._save_game(game)
    
    def get_game(self, game_id: str) -> Optional[GameRecord]:
        """Récupère une partie par son ID"""
        if game_id in self.games:
            return self.games[game_id]
        return self._load_game(game_id)
    
    def get_player_games(self, player_id: str, limit: int = 10) -> List[GameRecord]:
        """Récupère les dernières parties d'un joueur"""
        player_games = [
            game for game in self.games.values()
            if any(p['id'] == player_id for p in game.players)
        ]
        return sorted(
            player_games,
            key=lambda g: g.end_time,
            reverse=True
        )[:limit]
    
    def get_recent_games(self, limit: int = 10) -> List[GameRecord]:
        """Récupère les parties les plus récentes"""
        return sorted(
            self.games.values(),
            key=lambda g: g.end_time,
            reverse=True
        )[:limit]
    
    def _save_game(self, game: GameRecord) -> None:
        """Sauvegarde une partie dans un fichier"""
        file_path = os.path.join(self.save_dir, f"{game.game_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self._game_to_dict(game), f, indent=4)
    
    def _load_game(self, game_id: str) -> Optional[GameRecord]:
        """Charge une partie depuis un fichier"""
        file_path = os.path.join(self.save_dir, f"{game_id}.json")
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            game = self._dict_to_game(data)
            self.games[game_id] = game
            return game
    
    def _game_to_dict(self, game: GameRecord) -> Dict[str, Any]:
        """Convertit une partie en dictionnaire"""
        return {
            'game_id': game.game_id,
            'game_name': game.game_name,
            'start_time': game.start_time.isoformat(),
            'end_time': game.end_time.isoformat(),
            'players': game.players,
            'moves': [
                {
                    'player_id': move.player_id,
                    'move': move.move,
                    'timestamp': move.timestamp.isoformat(),
                    'move_number': move.move_number
                }
                for move in game.moves
            ],
            'result': {
                'winner_id': game.result.winner_id,
                'is_draw': game.result.is_draw,
                'end_reason': game.result.end_reason,
                'final_board': game.result.final_board,
                'duration': game.result.duration
            },
            'ranked': game.ranked,
            'game_config': game.game_config
        }
    
    def _dict_to_game(self, data: Dict[str, Any]) -> GameRecord:
        """Crée une partie à partir d'un dictionnaire"""
        return GameRecord(
            game_id=data['game_id'],
            game_name=data['game_name'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            players=data['players'],
            moves=[
                GameMove(
                    player_id=move['player_id'],
                    move=tuple(move['move']),
                    timestamp=datetime.fromisoformat(move['timestamp']),
                    move_number=move['move_number']
                )
                for move in data['moves']
            ],
            result=GameResult(
                winner_id=data['result']['winner_id'],
                is_draw=data['result']['is_draw'],
                end_reason=data['result']['end_reason'],
                final_board=data['result']['final_board'],
                duration=data['result']['duration']
            ),
            ranked=data['ranked'],
            game_config=data['game_config']
        )
    
    def get_game_stats(self, game_id: str) -> Dict[str, Any]:
        """Récupère les statistiques d'une partie"""
        game = self.get_game(game_id)
        if not game:
            return {}
            
        return {
            'game_id': game.game_id,
            'game_name': game.game_name,
            'duration': game.result.duration,
            'moves_count': len(game.moves),
            'players': [
                {
                    'id': player['id'],
                    'username': player['username'],
                    'display_name': player['display_name'],
                    'elo_change': player['elo_after'] - player['elo_before']
                }
                for player in game.players
            ],
            'result': {
                'winner': game.result.winner_id,
                'is_draw': game.result.is_draw,
                'end_reason': game.result.end_reason
            },
            'ranked': game.ranked
        }
    
    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Récupère les statistiques d'un joueur"""
        player_games = self.get_player_games(player_id)
        if not player_games:
            return {}
            
        total_games = len(player_games)
        wins = sum(1 for g in player_games if g.result.winner_id == player_id)
        draws = sum(1 for g in player_games if g.result.is_draw)
        losses = total_games - wins - draws
        
        return {
            'total_games': total_games,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'win_rate': (wins / total_games) * 100 if total_games > 0 else 0,
            'recent_games': [
                {
                    'game_id': game.game_id,
                    'game_name': game.game_name,
                    'result': 'win' if game.result.winner_id == player_id else 
                             'draw' if game.result.is_draw else 'loss',
                    'date': game.end_time.isoformat()
                }
                for game in player_games[:5]
            ]
        } 