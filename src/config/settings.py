import os
from dataclasses import dataclass
from typing import Dict, Any
import json

@dataclass
class GameConfig:
    name: str
    display_name: str
    description: str
    min_players: int
    max_players: int
    board_size: tuple
    rules: Dict[str, Any]

@dataclass
class ServerConfig:
    host: str
    port: int
    max_connections: int
    timeout: int
    debug: bool

@dataclass
class DatabaseConfig:
    path: str
    backup_path: str
    auto_backup: bool

@dataclass
class ClientConfig:
    host: str
    port: int
    reconnect_attempts: int
    reconnect_delay: int
    chat_history_size: int

class Config:
    def __init__(self):
        self.server = ServerConfig(
            host="localhost",
            port=8080,
            max_connections=100,
            timeout=30,
            debug=True
        )
        
        self.database = DatabaseConfig(
            path="matchmaking.db",
            backup_path="backups/",
            auto_backup=True
        )
        
        self.client = ClientConfig(
            host="localhost",
            port=8080,
            reconnect_attempts=3,
            reconnect_delay=5,
            chat_history_size=100
        )
        
        self.games = {
            "connect4": GameConfig(
                name="connect4",
                display_name="Puissance 4",
                description="Jeu de Puissance 4 classique",
                min_players=2,
                max_players=2,
                board_size=(6, 7),
                rules={
                    "win_length": 4,
                    "time_per_turn": 30
                }
            ),
            "tictactoe": GameConfig(
                name="tictactoe",
                display_name="Morpion",
                description="Jeu de Morpion classique",
                min_players=2,
                max_players=2,
                board_size=(3, 3),
                rules={
                    "win_length": 3,
                    "time_per_turn": 30
                }
            )
        }
    
    def save(self, path: str = "config.json"):
        """Sauvegarde la configuration dans un fichier JSON"""
        config_dict = {
            "server": self.server.__dict__,
            "database": self.database.__dict__,
            "client": self.client.__dict__,
            "games": {name: game.__dict__ for name, game in self.games.items()}
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=4)
    
    @classmethod
    def load(cls, path: str = "config.json") -> 'Config':
        """Charge la configuration depuis un fichier JSON"""
        if not os.path.exists(path):
            return cls()
            
        with open(path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
            
        config = cls()
        config.server = ServerConfig(**config_dict["server"])
        config.database = DatabaseConfig(**config_dict["database"])
        config.client = ClientConfig(**config_dict["client"])
        config.games = {
            name: GameConfig(**game_config)
            for name, game_config in config_dict["games"].items()
        }
        
        return config

# Instance globale de configuration
config = Config() 