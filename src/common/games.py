from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

@dataclass
class GameState:
    """État d'une partie"""
    board: List[List[int]]
    current_player: int
    last_move: Optional[tuple] = None
    start_time: datetime = datetime.now()
    last_move_time: datetime = datetime.now()
    moves_history: List[Dict] = None
    game_over: bool = False
    winner: Optional[int] = None
    is_draw: bool = False

    def __post_init__(self):
        if self.moves_history is None:
            self.moves_history = []

class BaseGame(ABC):
    """Classe de base pour tous les jeux"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.state = None
        self.reset()

    def reset(self):
        """Réinitialise la partie"""
        self.state = GameState(
            board=self._create_empty_board(),
            current_player=1
        )

    @abstractmethod
    def _create_empty_board(self) -> List[List[int]]:
        """Crée un plateau vide"""
        pass

    @abstractmethod
    def is_valid_move(self, move: Any) -> bool:
        """Vérifie si un coup est valide"""
        pass

    @abstractmethod
    def apply_move(self, move: Any) -> bool:
        """Applique un coup"""
        pass

    @abstractmethod
    def check_win(self) -> bool:
        """Vérifie s'il y a un gagnant"""
        pass

    @abstractmethod
    def check_draw(self) -> bool:
        """Vérifie s'il y a match nul"""
        pass

    def get_valid_moves(self) -> List[Any]:
        """Retourne la liste des coups valides"""
        return [move for move in self._get_all_possible_moves() if self.is_valid_move(move)]

    @abstractmethod
    def _get_all_possible_moves(self) -> List[Any]:
        """Retourne tous les coups possibles"""
        pass

    def get_state(self) -> GameState:
        """Retourne l'état actuel de la partie"""
        return self.state

    def save_state(self, filename: str):
        """Sauvegarde l'état de la partie"""
        state_dict = {
            'board': self.state.board,
            'current_player': self.state.current_player,
            'last_move': self.state.last_move,
            'start_time': self.state.start_time.isoformat(),
            'last_move_time': self.state.last_move_time.isoformat(),
            'moves_history': self.state.moves_history,
            'game_over': self.state.game_over,
            'winner': self.state.winner,
            'is_draw': self.state.is_draw
        }
        with open(filename, 'w') as f:
            json.dump(state_dict, f)

    def load_state(self, filename: str):
        """Charge l'état d'une partie"""
        with open(filename, 'r') as f:
            state_dict = json.load(f)
        self.state = GameState(
            board=state_dict['board'],
            current_player=state_dict['current_player'],
            last_move=tuple(state_dict['last_move']) if state_dict['last_move'] else None,
            start_time=datetime.fromisoformat(state_dict['start_time']),
            last_move_time=datetime.fromisoformat(state_dict['last_move_time']),
            moves_history=state_dict['moves_history'],
            game_over=state_dict['game_over'],
            winner=state_dict['winner'],
            is_draw=state_dict['is_draw']
        )

class Connect4(BaseGame):
    """Jeu du Puissance 4"""
    def _create_empty_board(self) -> List[List[int]]:
        return [[0 for _ in range(7)] for _ in range(6)]

    def is_valid_move(self, column: int) -> bool:
        if not 0 <= column < 7:
            return False
        return self.state.board[0][column] == 0

    def apply_move(self, column: int) -> bool:
        if not self.is_valid_move(column):
            return False

        # Trouver la première case vide dans la colonne
        for row in range(5, -1, -1):
            if self.state.board[row][column] == 0:
                self.state.board[row][column] = self.state.current_player
                self.state.last_move = (row, column)
                self.state.last_move_time = datetime.now()
                self.state.moves_history.append({
                    'player': self.state.current_player,
                    'move': column,
                    'time': self.state.last_move_time.isoformat()
                })

                if self.check_win():
                    self.state.game_over = True
                    self.state.winner = self.state.current_player
                elif self.check_draw():
                    self.state.game_over = True
                    self.state.is_draw = True
                else:
                    self.state.current_player = 3 - self.state.current_player
                return True
        return False

    def check_win(self) -> bool:
        if not self.state.last_move:
            return False
        row, col = self.state.last_move
        player = self.state.board[row][col]

        # Vérifier horizontalement
        for c in range(max(0, col-3), min(4, col+1)):
            if all(self.state.board[row][c+i] == player for i in range(4)):
                return True

        # Vérifier verticalement
        for r in range(max(0, row-3), min(3, row+1)):
            if all(self.state.board[r+i][col] == player for i in range(4)):
                return True

        # Vérifier diagonales
        for r in range(max(0, row-3), min(3, row+1)):
            for c in range(max(0, col-3), min(4, col+1)):
                if all(self.state.board[r+i][c+i] == player for i in range(4)):
                    return True
                if all(self.state.board[r+i][c+3-i] == player for i in range(4)):
                    return True
        return False

    def check_draw(self) -> bool:
        return all(self.state.board[0][col] != 0 for col in range(7))

    def _get_all_possible_moves(self) -> List[int]:
        return list(range(7))

    def get_column_height(self, column: int) -> int:
        """Retourne la hauteur d'une colonne"""
        for row in range(6):
            if self.state.board[row][column] != 0:
                return 6 - row
        return 0

class TicTacToe(BaseGame):
    """Jeu du Morpion"""
    def _create_empty_board(self) -> List[List[int]]:
        return [[0 for _ in range(3)] for _ in range(3)]

    def is_valid_move(self, move: tuple) -> bool:
        row, col = move
        if not (0 <= row < 3 and 0 <= col < 3):
            return False
        return self.state.board[row][col] == 0

    def apply_move(self, move: tuple) -> bool:
        if not self.is_valid_move(move):
            return False

        row, col = move
        self.state.board[row][col] = self.state.current_player
        self.state.last_move = move
        self.state.last_move_time = datetime.now()
        self.state.moves_history.append({
            'player': self.state.current_player,
            'move': move,
            'time': self.state.last_move_time.isoformat()
        })

        if self.check_win():
            self.state.game_over = True
            self.state.winner = self.state.current_player
        elif self.check_draw():
            self.state.game_over = True
            self.state.is_draw = True
        else:
            self.state.current_player = 3 - self.state.current_player
        return True

    def check_win(self) -> bool:
        if not self.state.last_move:
            return False
        row, col = self.state.last_move
        player = self.state.board[row][col]

        # Vérifier la ligne
        if all(self.state.board[row][c] == player for c in range(3)):
            return True

        # Vérifier la colonne
        if all(self.state.board[r][col] == player for r in range(3)):
            return True

        # Vérifier les diagonales
        if row == col and all(self.state.board[i][i] == player for i in range(3)):
            return True
        if row + col == 2 and all(self.state.board[i][2-i] == player for i in range(3)):
            return True

        return False

    def check_draw(self) -> bool:
        return all(self.state.board[r][c] != 0 for r in range(3) for c in range(3))

    def _get_all_possible_moves(self) -> List[tuple]:
        return [(r, c) for r in range(3) for c in range(3)]

    def get_empty_cells(self) -> List[tuple]:
        """Retourne la liste des cases vides"""
        return [(r, c) for r in range(3) for c in range(3) if self.state.board[r][c] == 0]

    def get_winning_moves(self) -> List[tuple]:
        """Retourne la liste des coups gagnants possibles"""
        winning_moves = []
        for move in self.get_empty_cells():
            row, col = move
            self.state.board[row][col] = self.state.current_player
            if self.check_win():
                winning_moves.append(move)
            self.state.board[row][col] = 0
        return winning_moves 