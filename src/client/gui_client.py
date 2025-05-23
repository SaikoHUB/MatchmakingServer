import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QStackedWidget, QMessageBox, QGridLayout, QComboBox, QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon
import json
import socket
import threading
import time
from datetime import datetime

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.common.chat import ChatMessage, ChatSystem, NotificationSystem, ChatManager
from src.common.games.connect4 import Connect4
from src.common.games.tictactoe import TicTacToe

class MatchmakingThread(QThread):
    message_received = pyqtSignal(dict)
    
    def __init__(self, client):
        super().__init__()
        self.client = client
        
    def run(self):
        while self.client.running and self.client.connected:
            try:
                data = self.client.socket.recv(4096)
                if not data:
                    break
                message = json.loads(data.decode('utf-8'))
                self.message_received.emit(message)
            except:
                break

class MatchmakingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = MatchmakingClient()
        self.matchmaking_thread = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Matchmaking Client')
        self.setMinimumSize(800, 600)
        
        # Widget principal
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        # Pages
        self.login_page = self.create_login_page()
        self.main_page = self.create_main_page()
        self.game_page = self.create_game_page()
        
        # Ajouter les pages
        self.central_widget.addWidget(self.login_page)
        self.central_widget.addWidget(self.main_page)
        self.central_widget.addWidget(self.game_page)
        
        # Afficher la page de connexion
        self.central_widget.setCurrentWidget(self.login_page)
        
    def create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel('Matchmaking Client')
        title.setFont(QFont('Arial', 24))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Formulaire de connexion
        form_layout = QVBoxLayout()
        
        # Connexion invité
        guest_btn = QPushButton('Jouer en invité')
        guest_btn.clicked.connect(self.guest_login)
        form_layout.addWidget(guest_btn)
        
        # Ou
        or_label = QLabel('OU')
        or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(or_label)
        
        # Champs de connexion
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Nom d\'utilisateur')
        form_layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Mot de passe')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.password_input)
        
        # Bouton de connexion
        login_btn = QPushButton('Se connecter')
        login_btn.clicked.connect(self.login)
        form_layout.addWidget(login_btn)
        
        layout.addLayout(form_layout)
        page.setLayout(layout)
        return page
        
    def create_main_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        # En-tête
        header = QHBoxLayout()
        self.user_label = QLabel()
        header.addWidget(self.user_label)
        
        logout_btn = QPushButton('Se déconnecter')
        logout_btn.clicked.connect(self.logout)
        header.addWidget(logout_btn)
        layout.addLayout(header)
        
        # Liste des jeux
        games_label = QLabel('Jeux disponibles')
        games_label.setFont(QFont('Arial', 16))
        layout.addWidget(games_label)
        
        # Grille de jeux
        games_grid = QGridLayout()
        
        # Puissance 4
        connect4_btn = QPushButton('Puissance 4')
        connect4_btn.clicked.connect(lambda: self.join_queue('connect4'))
        games_grid.addWidget(connect4_btn, 0, 0)
        
        # Morpion
        tictactoe_btn = QPushButton('Morpion')
        tictactoe_btn.clicked.connect(lambda: self.join_queue('tictactoe'))
        games_grid.addWidget(tictactoe_btn, 0, 1)
        
        layout.addLayout(games_grid)
        page.setLayout(layout)
        return page
        
    def create_game_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        # En-tête du jeu
        self.game_header = QLabel()
        self.game_header.setFont(QFont('Arial', 16))
        layout.addWidget(self.game_header)
        
        # Plateau de jeu
        self.board_widget = QWidget()
        self.board_layout = QGridLayout()
        self.board_widget.setLayout(self.board_layout)
        layout.addWidget(self.board_widget)
        
        # Bouton pour quitter la partie
        quit_btn = QPushButton('Quitter la partie')
        quit_btn.clicked.connect(self.leave_game)
        layout.addWidget(quit_btn)
        
        page.setLayout(layout)
        return page
        
    def connect_to_server(self):
        if self.client.connect():
            self.matchmaking_thread = MatchmakingThread(self.client)
            self.matchmaking_thread.message_received.connect(self.handle_message)
            self.matchmaking_thread.start()
            return True
        return False
        
    def guest_login(self):
        if not self.connect_to_server():
            QMessageBox.critical(self, 'Erreur', 'Impossible de se connecter au serveur')
            return
            
        self.client.guest_login()
        
    def login(self):
        if not self.connect_to_server():
            QMessageBox.critical(self, 'Erreur', 'Impossible de se connecter au serveur')
            return
            
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, 'Erreur', 'Veuillez remplir tous les champs')
            return
            
        self.client.login(username, password)
        
    def join_queue(self, game_name):
        self.client.join_queue(game_name, ranked=False)
        self.game_header.setText(f'En attente d\'un adversaire pour {game_name}...')
        self.central_widget.setCurrentWidget(self.game_page)
        
    def leave_game(self):
        if self.client.current_match:
            self.client.leave_queue(self.client.current_match['game_name'])
        self.central_widget.setCurrentWidget(self.main_page)
        
    def logout(self):
        self.client.disconnect()
        self.central_widget.setCurrentWidget(self.login_page)
        
    def handle_message(self, message):
        msg_type = message.get('type')
        
        if msg_type == 'login_success':
            self.client.player_id = message.get('player_id')
            self.client.account_info = message.get('account_info')
            self.client.is_guest = False
            self.user_label.setText(f'Connecté en tant que: {message["account_info"]["display_name"]}')
            self.central_widget.setCurrentWidget(self.main_page)
            
        elif msg_type == 'guest_success':
            self.client.player_id = message.get('player_id')
            self.client.is_guest = True
            self.user_label.setText(f'Connecté en tant que: {message["pseudo"]}')
            self.central_widget.setCurrentWidget(self.main_page)
            
        elif msg_type == 'match_found':
            self.client.current_match = message
            self.game_header.setText(f'Partie contre {message["opponent"]["pseudo"]}')
            self.update_board(message['board'], message['game_name'])
            
        elif msg_type == 'error':
            QMessageBox.warning(self, 'Erreur', message.get('message'))
            
    def update_board(self, board_data, game_name):
        # Nettoyer le plateau
        for i in reversed(range(self.board_layout.count())): 
            self.board_layout.itemAt(i).widget().setParent(None)
            
        if game_name == 'connect4':
            board = json.loads(board_data) if isinstance(board_data, str) else board_data
            rows = len(board)
            cols = len(board[0])
            
            for row in range(rows):
                for col in range(cols):
                    cell = QLabel()
                    cell.setFixedSize(50, 50)
                    cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    if board[row][col] == 0:
                        cell.setText('⚪')
                    elif board[row][col] == 1:
                        cell.setText('🔴')
                    else:
                        cell.setText('🟡')
                        
                    self.board_layout.addWidget(cell, row, col)

def main():
    app = QApplication(sys.argv)
    window = MatchmakingGUI()
    window.show()
    sys.exit(app.exec()) 