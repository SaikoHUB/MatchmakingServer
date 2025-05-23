from typing import List, Tuple, Dict, Any
from .base_game import BaseGame

class Connect4(BaseGame):
    def _create_empty_board(self) -> List[List[int]]:
        """Crée un plateau vide de Puissance 4"""
        return [[0 for _ in range(self.board_size[1])] for _ in range(self.board_size[0])]

    def is_valid_move(self, move: Tuple[int, int]) -> bool:
        """Vérifie si un coup est valide dans le Puissance 4"""
        col = move[1]
        # Vérifie si la colonne est valide
        if not (0 <= col < self.board_size[1]):
            return False
        # Vérifie si la colonne n'est pas pleine
        return self.state.board[0][col] == 0

    def apply_move(self, move: Tuple[int, int]) -> bool:
        """Applique un coup dans le Puissance 4"""
        if not self.is_valid_move(move):
            return False

        col = move[1]
        # Trouve la première ligne vide dans la colonne
        for row in range(self.board_size[0] - 1, -1, -1):
            if self.state.board[row][col] == 0:
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
        return False

    def check_win(self) -> bool:
        """Vérifie si le joueur actuel a gagné"""
        if not self.state.last_move:
            return False
            
        row, col = self.state.last_move
        player = self.state.current_player
        
        # Directions à vérifier (horizontal, vertical, diagonales)
        directions = [
            [(0, 1), (0, -1)],  # horizontal
            [(1, 0), (-1, 0)],  # vertical
            [(1, 1), (-1, -1)], # diagonale /
            [(1, -1), (-1, 1)]  # diagonale \
        ]
        
        for dir_pair in directions:
            count = 1  # Le coup actuel compte pour 1
            
            # Vérifie dans chaque direction
            for dx, dy in dir_pair:
                x, y = row + dx, col + dy
                while (0 <= x < self.board_size[0] and 
                       0 <= y < self.board_size[1] and 
                       self.state.board[x][y] == player):
                    count += 1
                    x += dx
                    y += dy
                    
            if count >= self.win_length:
                return True
                
        return False

    def check_draw(self) -> bool:
        """Vérifie si la partie est nulle"""
        # Dans le Puissance 4, c'est un match nul si toutes les colonnes sont pleines
        return all(self.state.board[0][col] != 0 for col in range(self.board_size[1]))

    def get_valid_columns(self) -> List[int]:
        """Retourne la liste des colonnes valides"""
        return [col for col in range(self.board_size[1]) 
                if self.state.board[0][col] == 0]

    def get_column_height(self, col: int) -> int:
        """Retourne la hauteur de la colonne (nombre de jetons)"""
        height = 0
        for row in range(self.board_size[0]):
            if self.state.board[row][col] != 0:
                height += 1
        return height 