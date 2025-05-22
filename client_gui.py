from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QStackedWidget, QHBoxLayout, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from src.client.console_client import MatchmakingClient
import sys

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connexion")
        self.setFixedSize(400, 200)
        self.client = MatchmakingClient()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.stacked_widget = QStackedWidget()
        self.init_welcome_page()
        self.init_guest_page()
        self.init_login_page()
        self.init_register_page()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def init_welcome_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        welcome_label = QLabel("Bienvenue ! Choisissez une option :")
        guest_button = QPushButton("Connexion en tant qu'invité")
        login_button = QPushButton("Connexion à un compte")
        register_button = QPushButton("Créer un compte")
        guest_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        login_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        register_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        layout.addWidget(welcome_label)
        layout.addWidget(guest_button)
        layout.addWidget(login_button)
        layout.addWidget(register_button)
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def init_guest_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.guest_label = QLabel("Connexion en tant qu'invité")
        self.guest_username = QLineEdit()
        self.guest_username.setPlaceholderText("Nom d'utilisateur")
        self.guest_login_button = QPushButton("Se connecter")
        self.guest_login_button.clicked.connect(self.handle_guest_login)
        back_button = QPushButton("Retour")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(self.guest_label)
        layout.addWidget(self.guest_username)
        layout.addWidget(self.guest_login_button)
        layout.addWidget(back_button)
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def init_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.login_label = QLabel("Connexion à un compte")
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Nom d'utilisateur")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Mot de passe")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_button = QPushButton("Se connecter")
        self.login_button.clicked.connect(self.handle_login)
        back_button = QPushButton("Retour")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(self.login_label)
        layout.addWidget(self.login_username)
        layout.addWidget(self.login_password)
        layout.addWidget(self.login_button)
        layout.addWidget(back_button)
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def init_register_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.register_label = QLabel("Créer un compte")
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Nom d'utilisateur")
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Mot de passe")
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_button = QPushButton("Créer")
        self.register_button.clicked.connect(self.handle_register)
        back_button = QPushButton("Retour")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(self.register_label)
        layout.addWidget(self.register_username)
        layout.addWidget(self.register_password)
        layout.addWidget(self.register_button)
        layout.addWidget(back_button)
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def handle_guest_login(self):
        username = self.guest_username.text().strip()
        if not username:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom d'utilisateur.")
            return
        try:
            self.client.connect()
            self.client.guest_login(username)
            self.hide()
            self.selection_window = GameSelectionWindow(self.client, username, self, is_guest=True)
            self.selection_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Erreur de connexion", str(e))

    def handle_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom d'utilisateur et un mot de passe.")
            return
        try:
            self.client.connect()
            # Ici, tu appelles la méthode de connexion à un compte (à implémenter dans ton client)
            # self.client.login(username, password)
            self.hide()
            self.selection_window = GameSelectionWindow(self.client, username, self, is_guest=False)
            self.selection_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Erreur de connexion", str(e))

    def handle_register(self):
        username = self.register_username.text().strip()
        password = self.register_password.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom d'utilisateur et un mot de passe.")
            return
        try:
            self.client.connect()
            # Ici, tu appelles la méthode de création de compte (à implémenter dans ton client)
            # self.client.register(username, password)
            self.hide()
            self.selection_window = GameSelectionWindow(self.client, username, self, is_guest=False)
            self.selection_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'inscription", str(e))

class GameSelectionWindow(QWidget):
    def __init__(self, client, username, login_window, is_guest=False):
        super().__init__()
        self.setWindowTitle(f"Bienvenue {username}")
        self.setFixedSize(300, 200)
        self.client = client
        self.is_guest = is_guest
        self.username = username
        self.login_window = login_window # Stocker la référence à la fenêtre de connexion
        layout = QVBoxLayout()
        self.label = QLabel("Choisissez un jeu :")
        self.combo = QComboBox()
        self.combo.addItems(["tictactoe", "connect4"])  # Ajout de tictactoe
        self.ranked_button = QPushButton("Rejoindre (Ranked)")
        self.casual_button = QPushButton("Rejoindre (Classique)")
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
        layout.addWidget(self.ranked_button)
        layout.addWidget(self.casual_button)
        self.setLayout(layout)
        self.ranked_button.clicked.connect(lambda: self.join_queue(True))
        self.casual_button.clicked.connect(lambda: self.join_queue(False))
        if is_guest:
            self.ranked_button.setEnabled(False)
            self.ranked_button.setToolTip("Les invités n'ont pas accès aux parties classées.")

    def join_queue(self, ranked):
        game = self.combo.currentText()
        try:
            self.client.join_queue(game, ranked=ranked)
            QMessageBox.information(self, "File d'attente", f"En attente d'un adversaire pour {game} ({'Ranked' if ranked else 'Classique'})...")
            # Attendre le début de la partie
            self.wait_for_game_start(game)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def wait_for_game_start(self, game):
        # Ici, tu devras implémenter la logique pour attendre le début de la partie
        # Pour l'instant, on simule le début d'une partie
        # Cette fonction sera idéalement déclenchée par un message serveur confirmant le match
        # Par exemple, le serveur envoie 'match_start' après 'match_found'

        # TODO: Remplacer cette simulation par l'attente d'un message serveur spécifique

        if game == "tictactoe":
            # Assurez-vous que le client est bien connecté avant de créer la fenêtre de jeu
            if self.client.connected:
                 self.game_window = TicTacToeWindow(self.client, self.username)
                 # Connecter le signal de retour au menu principal
                 self.game_window.game_finished_and_return_to_menu.connect(self.handle_game_finished_and_return)
                 self.game_window.show()
                 self.hide() # Cacher la fenêtre de sélection une fois le jeu lancé
            else:
                 QMessageBox.critical(self, "Erreur", "Client non connecté. Impossible de lancer le jeu.")

    def handle_game_finished_and_return(self):
        # Gérer le signal de la fenêtre de jeu pour revenir à la fenêtre de sélection de jeu
        print("Signal reçu: Fin de partie et retour au menu.")
        self.show() # Réafficher la fenêtre de sélection
        # Supprimer la logique pour réafficher la fenêtre de connexion et fermer la fenêtre de sélection
        # if self.login_window:
        #      self.login_window.show()
        # self.close()

class TicTacToeWindow(QWidget):
    # Ajouter un signal pour indiquer que la partie est finie et qu'on veut revenir au menu
    game_finished_and_return_to_menu = pyqtSignal()

    def __init__(self, client, username):
        super().__init__()
        self.client = client
        self.username = username
        self.current_player = None  # Sera défini par le serveur (votre tour ou non)
        self.my_symbol = None  # X ou O, déterminé par le serveur
        self.opponent_name = None
        self.opponent_symbol = None # Assurez-vous que cet attribut existe dès le début
        self.init_ui()
        self.setup_network_handlers()

        # Désactiver les boutons au début en attendant le match_found puis le premier game_update
        self.disable_buttons()

    def setup_network_handlers(self):
        # Remplacer complètement le handler original du client par notre handler spécifique au jeu
        # Nous stockons l'ancien handler pour le restaurer plus tard si nécessaire (par exemple, en quittant la fenêtre de jeu)
        if not hasattr(self.client, '_original_handle_server_message'):
             self.client._original_handle_server_message = self.client._handle_server_message

        def game_window_handler(message):
            msg_type = message.get('type')

            # Gérer les messages spécifiques au jeu TicTacToe
            if msg_type == 'match_found':
                 self.handle_match_found(message)
            elif msg_type == 'game_update':
                 self.handle_game_update(message)
            elif msg_type == 'game_over':
                 self.handle_game_over(message)
            # Pour les autres types de messages, nous ne faisons rien ici pour l'instant
            # pour éviter les interférences. L'ancien handler n'est plus actif quand cette fenêtre est ouverte.

        # Assigner le nouveau handler à la place de l'ancien
        self.client._handle_server_message = game_window_handler

    # Ajout d'une méthode pour restaurer le handler original (utile en quittant la fenêtre de jeu)
    def restore_original_handler(self):
        if hasattr(self.client, '_original_handle_server_message'):
            self.client._handle_server_message = self.client._original_handle_server_message
            del self.client._original_handle_server_message

    def handle_match_found(self, message):
        # Déterminer si on est X ou O
        self.my_symbol = "X" if message.get('your_turn') else "O"
        self.opponent_symbol = "O" if self.my_symbol == "X" else "X"
        # Le nom de l'adversaire est nécessaire pour l'affichage
        opponent_data = message.get('opponent')
        if opponent_data and isinstance(opponent_data, dict):
             self.opponent_name = opponent_data.get('pseudo', 'Adversaire inconnu')
        else:
             self.opponent_name = 'Adversaire inconnu'

        # Mettre à jour l'interface avec les informations du joueur et de l'adversaire
        self.player_info.setText(f"Vous jouez {self.my_symbol} | {self.opponent_name} joue {self.opponent_symbol}")

        # Afficher un message indiquant que la partie a commencé et en attente du premier coup/update
        self.status_label.setText("Partie trouvée. En attente du premier coup...")
        # Le plateau visuel sera mis à jour par le premier message 'game_update'
        # handle_game_update gère la mise à jour du plateau et l'activation/désactivation des boutons.

    def make_move(self, row, col):
        index = row * 3 + col
        # On vérifie si c'est notre tour (les boutons sont activés/désactivés par handle_game_update)
        # On vérifie aussi si la case sur l'interface est vide
        if self.buttons[index].text() == "" and self.current_player == self.my_symbol:
            # Envoyer le coup au serveur
            self.client._send_message({
                'type': 'make_move',
                'game_name': 'tictactoe',
                'move': index,
                'player_id': self.client.player_id
            })

            # On désactive les boutons après l'envoi du coup en attendant la réponse du serveur (game_update)
            self.disable_buttons()
        else:
            print("Coup invalide (case non vide ou pas votre tour).")


    def handle_game_update(self, message):
        # Recevoir l'état complet du plateau et le joueur actuel du serveur
        board_data = message.get('board') # Devrait être une liste de listes
        current_turn_player_id = message.get('current_turn_player_id')

        # Vérification plus stricte du format du plateau
        if not isinstance(board_data, list):
            # print("❌ Erreur: board_data n'est pas une liste") # Remplacé par QMessageBox
            QMessageBox.critical(self, "Erreur plateau", "Erreur serveur: Format de plateau invalide (pas une liste).")
            return
            
        if len(board_data) != 3:
            # print("❌ Erreur: board_data n'a pas 3 lignes") # Remplacé par QMessageBox
            QMessageBox.critical(self, "Erreur plateau", f"Erreur serveur: Format de plateau invalide (nombre de lignes incorrect : {len(board_data)}).")
            return
            
        for i, row in enumerate(board_data):
            if not isinstance(row, list) or len(row) != 3:
                # print("❌ Erreur: Une ligne du plateau n'est pas valide") # Remplacé par QMessageBox
                QMessageBox.critical(self, "Erreur plateau", f"Erreur serveur: Format de plateau invalide (ligne {i} non valide).")
                return

        # Mettre à jour le plateau visuel
        for i in range(9):
            row = i // 3
            col = i % 3

            try:
                symbol_value = board_data[row][col]
                symbol = "X" if symbol_value == 1 else ("O" if symbol_value == 2 else "")

                self.buttons[i].setText(symbol)
                self.buttons[i].setStyleSheet(f"""
                    QPushButton {{
                        background-color: white;
                        border: 2px solid #8f8f91;
                        border-radius: 6px;
                        color: {{'#ff4444' if symbol == 'X' else '#4444ff'}};
                    }}
                """)
            except IndexError:
                print(f"❌ Erreur d'index pour la position ({row}, {col})")
                continue

        # Mettre à jour le statut et l'état des boutons
        if current_turn_player_id is not None:
            if current_turn_player_id == self.client.player_id:
                self.current_player = self.my_symbol
                self.status_label.setText("C'est votre tour !")
                self.enable_buttons()
            else:
                self.current_player = self.opponent_symbol
                opponent_name = self.opponent_name if self.opponent_name is not None else 'Adversaire'
                self.status_label.setText(f"C'est au tour de {opponent_name}")
                self.disable_buttons()
        else:
            self.status_label.setText("En attente d'instructions du serveur...")
            self.disable_buttons()

    def handle_game_over(self, message):
        winner_id = message.get('winner_id')
        board_data = message.get('board')

        # Vérification plus stricte du format du plateau
        if not isinstance(board_data, list):
            # print("❌ Erreur: board_data n'est pas une liste") # Remplacé par QMessageBox
            QMessageBox.critical(self, "Erreur plateau", "Erreur serveur: Format de plateau invalide en fin de partie (pas une liste).")
            return
            
        if len(board_data) != 3:
            # print("❌ Erreur: board_data n'a pas 3 lignes") # Remplacé par QMessageBox
            QMessageBox.critical(self, "Erreur plateau", f"Erreur serveur: Format de plateau invalide en fin de partie (nombre de lignes incorrect : {len(board_data)}).")
            return
            
        for i, row in enumerate(board_data):
            if not isinstance(row, list) or len(row) != 3:
                # print("❌ Erreur: Une ligne du plateau n'est pas valide") # Remplacé par QMessageBox
                QMessageBox.critical(self, "Erreur plateau", f"Erreur serveur: Format de plateau invalide en fin de partie (ligne {i} non valide).")
                return

        # Mettre à jour le plateau final
        for i in range(9):
            row = i // 3
            col = i % 3

            try:
                symbol_value = board_data[row][col]
                symbol = "X" if symbol_value == 1 else ("O" if symbol_value == 2 else "")

                self.buttons[i].setText(symbol)
                self.buttons[i].setStyleSheet(f"""
                    QPushButton {{
                        background-color: white;
                        border: 2px solid #8f8f91;
                        border-radius: 6px;
                        color: {{'#ff4444' if symbol == 'X' else '#4444ff'}};
                    }}
                """)
            except IndexError:
                print(f"❌ Erreur d'index pour la position ({row}, {col})")
                continue

        if winner_id == self.client.player_id:
            self.status_label.setText("Vous avez gagné ! 🎉")
        elif winner_id is not None: # L'adversaire a gagné
             # Utiliser le nom de l'adversaire pour le message final
             self.status_label.setText(f"Le joueur {self.opponent_name} a gagné ! 😢")
        else:
            self.status_label.setText("Match nul ! 🤝")

        for button in self.buttons:
            button.setEnabled(False)

        # Rendre les boutons de fin de partie visibles
        if hasattr(self, 'return_button'):
             self.return_button.setVisible(True)

    def enable_buttons(self):
        # Activer les boutons uniquement si la case est vide
        for i in range(9):
            if self.buttons[i].text() == "": # Vérifier le texte affiché sur le bouton
                self.buttons[i].setEnabled(True)
            else:
                self.buttons[i].setEnabled(False) # Désactiver si la case est déjà prise

    def disable_buttons(self):
        for button in self.buttons:
            button.setEnabled(False)

    def quit_game(self):
        # self.client._send_message({
        #     'type': 'leave_game',
        #     'game_name': 'tictactoe',
        #     'player_id': self.client.player_id
        # }) # Désactivé pour l'instant, la fermeture de la fenêtre suffit peut-être
        self.restore_original_handler()
        self.close()

    def request_return_to_menu(self):
        # Émettre le signal pour indiquer qu'on veut revenir au menu principal
        print("Émission du signal: game_finished_and_return_to_menu")
        self.game_finished_and_return_to_menu.emit()
        # Fermer la fenêtre de jeu actuelle
        self.close()

    def init_ui(self):
        self.setWindowTitle(f"TicTacToe - {self.username}")
        self.setFixedSize(400, 500)

        # Layout principal
        layout = QVBoxLayout()

        # Label pour le statut
        self.status_label = QLabel("En attente de l'adversaire...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont('Arial', 14))
        layout.addWidget(self.status_label)

        # Grille de jeu
        self.grid = QGridLayout()
        self.buttons = []
        for i in range(3):
            for j in range(3):
                button = QPushButton()
                button.setFixedSize(100, 100)
                button.setFont(QFont('Arial', 40))
                button.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: 2px solid #8f8f91;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                    }
                """)
                button.clicked.connect(lambda checked, row=i, col=j: self.make_move(row, col))
                self.grid.addWidget(button, i, j)
                self.buttons.append(button)

        layout.addLayout(self.grid)

        # Informations sur les joueurs
        self.player_info = QLabel("En attente de l'adversaire...")
        self.player_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_info.setFont(QFont('Arial', 12))
        layout.addWidget(self.player_info)

        # Bouton pour quitter
        quit_button = QPushButton("Quitter la partie")
        quit_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """)
        quit_button.clicked.connect(self.quit_game)
        layout.addWidget(quit_button)

        self.return_button = QPushButton("Retour au menu principal")
        self.return_button.clicked.connect(self.request_return_to_menu)
        self.return_button.setVisible(False) # Cacher initialement
        layout.addWidget(self.return_button)

        self.setLayout(layout)

    # Assurez-vous que la fenêtre de jeu restaure le handler si elle est fermée manuellement
    def closeEvent(self, event):
        print("Fermeture de la fenêtre TicTacToe. Restauration du handler original.")
        self.restore_original_handler()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())