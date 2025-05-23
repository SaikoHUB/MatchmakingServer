from typing import List, Tuple, Dict, Any
from datetime import datetime
from .base_game import BaseGame

class TicTacToe(BaseGame):
    def _create_empty_board(self) -> List[List[int]]:
        """Crée un plateau vide de Morpion"""
        return [[0 for _ in range(self.board_size[1])] for _ in range(self.board_size[0])]

    def is_valid_move(self, move: Tuple[int, int]) -> bool:
        """Vérifie si un coup est valide dans le Morpion"""
        row, col = move
        # Vérifie si la position est dans les limites
        if not (0 <= row < self.board_size[0] and 0 <= col < self.board_size[1]):
            return False
        # Vérifie si la case est vide
        return self.state.board[row][col] == 0

    def apply_move(self, move: Tuple[int, int]) -> bool:
        """Applique un coup dans le Morpion"""
        if not self.is_valid_move(move):
            return False

        row, col = move
        self.state.board[row][col] = self.state.current_player
        self.state.last_move = (row, col)
        self.state.last_move_time = datetime.now()
        
        # Enregistre le coup dans l'historique
        self.state.moves_history.append({
            'player': self.state.current_player,
            'move': (row, col),
            'time': self.state.last_move_time.isoformat()
        })
        
        # Vérifie la victoire
        if self.check_win():
            self.state.game_over = True
            self.state.winner = self.state.current_player
        # Vérifie le match nul
        elif self.check_draw():
            self.state.game_over = True
            self.state.is_draw = True
        else:
            # Change de joueur
            self.state.current_player = 3 - self.state.current_player
        
        return True

    def check_win(self) -> bool:
        """Vérifie si le joueur actuel a gagné"""
        if not self.state.last_move:
            return False
            
        row, col = self.state.last_move
        player = self.state.current_player
        
        # Vérifie la ligne
        if all(self.state.board[row][c] == player for c in range(self.board_size[1])):
            return True
            
        # Vérifie la colonne
        if all(self.state.board[r][col] == player for r in range(self.board_size[0])):
            return True
            
        # Vérifie la diagonale principale
        if row == col and all(self.state.board[i][i] == player for i in range(self.board_size[0])):
            return True
            
        # Vérifie la diagonale secondaire
        if row + col == self.board_size[0] - 1 and all(
            self.state.board[i][self.board_size[0] - 1 - i] == player 
            for i in range(self.board_size[0])
        ):
            return True
            
        return False

    def check_draw(self) -> bool:
        """Vérifie si la partie est nulle"""
        # Dans le Morpion, c'est un match nul si toutes les cases sont remplies
        return all(
            self.state.board[r][c] != 0 
            for r in range(self.board_size[0]) 
            for c in range(self.board_size[1])
        )

    def get_empty_cells(self) -> List[Tuple[int, int]]:
        """Retourne la liste des cases vides"""
        return [
            (r, c) 
            for r in range(self.board_size[0]) 
            for c in range(self.board_size[1]) 
            if self.state.board[r][c] == 0
        ]

    def get_winning_moves(self) -> List[Tuple[int, int]]:
        """Retourne la liste des coups gagnants possibles"""
        winning_moves = []
        empty_cells = self.get_empty_cells()
        
        for row, col in empty_cells:
            # Simule le coup
            self.state.board[row][col] = self.state.current_player
            if self.check_win():
                winning_moves.append((row, col))
            # Annule le coup
            self.state.board[row][col] = 0
            
        return winning_moves 