import socket
import json
import threading
import sys
import time
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict

class MatchmakingClient:
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = False
        
        # Données de session
        self.player_id = None
        self.account_info = None
        self.is_guest = False
        self.in_match = False
        self.current_match = None
        
        # Thread pour recevoir les messages
        self.receive_thread = None
        
    def connect(self):
        """Se connecte au serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True
            
            # Démarrer le thread de réception
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            print(f"✅ Connecté au serveur {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def disconnect(self):
        """Se déconnecte du serveur"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("👋 Déconnecté du serveur")
    
    def _send_message(self, message: dict):
        """Envoie un message au serveur"""
        if not self.connected:
            print("❌ Pas connecté au serveur")
            return False
        
        try:
            message_json = json.dumps(message)
            self.socket.send(message_json.encode('utf-8'))
            return True
        except Exception as e:
            print(f"❌ Erreur envoi message: {e}")
            return False
    
    def _receive_messages(self):
        """Thread pour recevoir les messages du serveur"""
        while self.running and self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    self._handle_server_message(message)
                except json.JSONDecodeError:
                    print("❌ Message JSON invalide reçu")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"❌ Erreur réception: {e}")
                break
        
        self.connected = False
    
    def _handle_server_message(self, message: dict):
        """Traite les messages reçus du serveur"""
        msg_type = message.get('type')
        
        if msg_type == 'register_success':
            print(f"✅ {message.get('message')}")
            
        elif msg_type == 'register_error':
            print(f"❌ Erreur inscription: {message.get('message')}")
            
        elif msg_type == 'login_success':
            self.player_id = message.get('player_id')
            self.account_info = message.get('account_info')
            self.is_guest = False
            print(f"✅ {message.get('message')}")
            print(f"   ID Joueur: {self.player_id}")
            
        elif msg_type == 'login_error':
            print(f"❌ Erreur connexion: {message.get('message')}")
            
        elif msg_type == 'guest_success':
            self.player_id = message.get('player_id')
            self.is_guest = True
            print(f"✅ {message.get('message')}")
            print(f"   ID Joueur: {self.player_id}")
            
        elif msg_type == 'guest_error':
            print(f"❌ Erreur connexion invité: {message.get('message')}")
            
        elif msg_type == 'queue_joined':
            queue_pos = message.get('queue_position')
            game_name = message.get('game_name')
            ranked = message.get('ranked')
            mode = "classée" if ranked else "non classée"
            print(f"🎮 Ajouté à la file {mode} de {game_name}")
            print(f"   Position: {queue_pos} - En attente d'un adversaire...")
            
        elif msg_type == 'queue_error':
            print(f"❌ Erreur file d'attente: {message.get('message')}")
            
        elif msg_type == 'queue_left':
            print(f"🚪 {message.get('message')}")
            
        elif msg_type == 'match_found':
            self._handle_match_found(message)
            
        elif msg_type == 'games_list':
            self._display_games_list(message.get('games', []))
            
        elif msg_type == 'stats_result':
            self._display_stats(message.get('stats'))
            
        elif msg_type == 'error':
            print(f"❌ Erreur: {message.get('message')}")
            
        elif msg_type == 'pong':
            print(f"🏓 Pong reçu: {message.get('timestamp')}")
            
        elif msg_type == 'make_move':
            self._handle_make_move(message)
            
        else:
            print(f"📨 Message reçu: {message}")
    
    def _handle_match_found(self, data: Dict):
        """Gère la notification de match trouvé"""
        print(f"\n🎮 Match trouvé! Vous jouez contre {data['opponent']['pseudo']}")
        print(f"Jeu: {data['game_display_name']}")
        if data['ranked']:
            print(f"Mode: Classé (ELO: {data['opponent']['elo_rating']})")
        else:
            print("Mode: Non classé")
        
        # Décodage du plateau
        board = json.loads(data['board']) if isinstance(data['board'], str) else data['board']
        self._display_board(board, data['game_name'])
        
        if data['your_turn']:
            print("\nC'est votre tour!")
        else:
            print("\nC'est au tour de votre adversaire")
    
    def _display_board(self, board: str, game_name: str):
        """Affiche le plateau de jeu"""
        if game_name == "Puissance 4":
            # Si board est déjà un dict/list, l'utiliser directement, sinon le décoder
            board_data = board if isinstance(board, (dict, list)) else json.loads(board)
            rows = len(board_data)
            cols = len(board_data[0])
            
            # Afficher les numéros de colonnes
            print("\n  " + " ".join(str(i) for i in range(cols)))
            
            # Afficher le plateau
            for row in board_data:
                print("| " + " ".join(str(cell) for cell in row) + " |")
            
            # Afficher la ligne du bas
            print("+" + "-" * (cols * 2 + 1) + "+")
        elif game_name.lower() == "morpion":
            print("  0 1 2")
            for i, row in enumerate(board):
                print(f"{i} {' '.join('⬜' if cell == 0 else ('❌' if cell == 1 else '⭕') for cell in row)}")
        else:
            print(f"Plateau: {board}")
    
    def _display_games_list(self, games):
        """Affiche la liste des jeux disponibles"""
        print("\n🎮 Jeux disponibles:")
        print("-" * 40)
        for i, game in enumerate(games, 1):
            print(f"{i}. {game['display_name']}")
            print(f"   Nom: {game['name']}")
            print(f"   Description: {game['description']}")
            print()
    
    def _display_stats(self, stats):
        """Affiche les statistiques"""
        if not stats:
            print("📊 Aucune statistique disponible (invité ou pas de parties jouées)")
            return
        
        if isinstance(stats, list):
            print("\n📊 Statistiques par jeu:")
            print("-" * 40)
            for stat in stats:
                print(f"🎮 {stat['game']}")
                print(f"   ELO: {stat['elo_rating']}")
                print(f"   Parties: {stat['games_played']}")
                print(f"   Victoires: {stat['wins']}")
                print(f"   Défaites: {stat['losses']}")
                print(f"   Égalités: {stat['draws']}")
                if stat['games_played'] > 0:
                    winrate = (stat['wins'] / stat['games_played']) * 100
                    print(f"   Taux de victoire: {winrate:.1f}%")
                print()
        else:
            print(f"\n📊 Statistiques - {stats['game']}:")
            print(f"   ELO: {stats['elo_rating']}")
            print(f"   Parties: {stats['games_played']}")
            print(f"   Victoires: {stats['wins']}")
            print(f"   Défaites: {stats['losses']}")
            print(f"   Égalités: {stats['draws']}")
    
    # =================== ACTIONS UTILISATEUR ===================
    
    def register(self, username: str, password: str, display_name: str, email: str = None):
        """Inscription d'un nouveau compte"""
        message = {
            'type': 'register',
            'username': username,
            'password': password,
            'display_name': display_name,
            'email': email
        }
        return self._send_message(message)
    
    def login(self, username: str, password: str):
        """Connexion avec un compte"""
        message = {
            'type': 'login',
            'username': username,
            'password': password
        }
        return self._send_message(message)
    
    def guest_login(self, pseudo: str = None):
        """Connexion en tant qu'invité"""
        message = {
            'type': 'guest_login',
            'pseudo': pseudo
        }
        return self._send_message(message)
    
    def join_queue(self, game_name: str, ranked: bool = True):
        """Rejoindre la file d'attente"""
        if not self.player_id:
            print("❌ Vous devez être connecté pour rejoindre une file")
            return False
        
        message = {
            'type': 'join_queue',
            'player_id': self.player_id,
            'game_name': game_name,
            'ranked': ranked
        }
        return self._send_message(message)
    
    def leave_queue(self, game_name: str):
        """Quitter la file d'attente"""
        if not self.player_id:
            print("❌ Vous devez être connecté")
            return False
        
        message = {
            'type': 'leave_queue',
            'player_id': self.player_id,
            'game_name': game_name
        }
        return self._send_message(message)
    
    def get_games(self):
        """Récupérer la liste des jeux"""
        message = {'type': 'get_games'}
        return self._send_message(message)
    
    def get_stats(self, game_name: str = None):
        """Récupérer les statistiques"""
        if not self.player_id:
            print("❌ Vous devez être connecté")
            return False
        
        message = {
            'type': 'get_stats',
            'player_id': self.player_id,
            'game_name': game_name
        }
        return self._send_message(message)
    
    def ping(self):
        """Envoyer un ping au serveur"""
        message = {'type': 'ping'}
        return self._send_message(message)

    def _handle_make_move(self, message: Dict):
        match_id = message.get('match_id')
        player_id = message.get('player_id')
        move = message.get('move_data')
        # 1. Récupérer l'état du match et du plateau
        # 2. Charger la classe de jeu correspondante
        # 3. Valider et appliquer le coup
        # 4. Mettre à jour la DB, vérifier victoire/nul
        # 5. Notifier les deux joueurs


def main():
    """Interface utilisateur console"""
    print("🎮 Client de test - Serveur de Matchmaking")
    print("=" * 45)
    
    client = MatchmakingClient()
    
    # Se connecter au serveur
    if not client.connect():
        print("❌ Impossible de se connecter au serveur")
        return
    
    try:
        while client.connected:
            print("\n" + "=" * 30)
            print("MENU PRINCIPAL")
            print("=" * 30)
            
            if not client.player_id:
                print("1. 🔑 Se connecter")
                print("2. 📝 Créer un compte")
                print("3. 🎭 Jouer en invité")
            else:
                pseudo = "Invité" if client.is_guest else client.account_info.get('display_name', 'Joueur')
                print(f"👤 Connecté en tant que: {pseudo}")
                print("4. 🎮 Voir les jeux disponibles")
                print("5. 🚀 Rejoindre une file d'attente")
                print("6. 🚪 Quitter une file d'attente")
                print("7. 📊 Voir mes statistiques")
                print("8. 🏓 Ping serveur")
                print("9. 🔓 Se déconnecter")
            
            print("0. ❌ Quitter")
            
            try:
                choice = input("\n👉 Votre choix: ").strip()
                
                if choice == "0":
                    break
                elif choice == "1" and not client.player_id:
                    username = input("Nom d'utilisateur: ")
                    password = input("Mot de passe: ")
                    client.login(username, password)
                    
                elif choice == "2" and not client.player_id:
                    print("\n📝 Création de compte:")
                    username = input("Nom d'utilisateur: ")
                    password = input("Mot de passe: ")
                    display_name = input("Nom d'affichage: ")
                    email = input("Email (optionnel): ") or None
                    client.register(username, password, display_name, email)
                    
                elif choice == "3" and not client.player_id:
                    pseudo = input("Pseudo (optionnel): ") or None
                    client.guest_login(pseudo)
                    
                elif choice == "4" and client.player_id:
                    client.get_games()
                    
                elif choice == "5" and client.player_id:
                    print("\n🎮 Jeux disponibles: connect4, tictactoe")
                    game_name = input("Nom du jeu: ")
                    if not client.is_guest:
                        ranked_input = input("Partie classée ? (o/N): ").lower()
                        ranked = ranked_input in ['o', 'oui', 'y', 'yes']
                    else:
                        ranked = False
                        print("ℹ️ Les invités ne peuvent jouer qu'en partie non classée")
                    client.join_queue(game_name, ranked)
                    
                elif choice == "6" and client.player_id:
                    game_name = input("Nom du jeu: ")
                    client.leave_queue(game_name)
                    
                elif choice == "7" and client.player_id:
                    if client.is_guest:
                        print("📊 Les invités n'ont pas de statistiques")
                    else:
                        game_name = input("Jeu spécifique (optionnel): ") or None
                        client.get_stats(game_name)
                    
                elif choice == "8" and client.player_id:
                    client.ping()
                    
                elif choice == "9" and client.player_id:
                    client.player_id = None
                    client.account_info = None
                    client.is_guest = False
                    print("🔓 Déconnecté de la session")
                    
                else:
                    print("❌ Choix invalide")
                
                # Petite pause pour lire les messages
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()

class BaseGame(ABC):
    @abstractmethod
    def is_valid_move(self, board, move, player):
        pass

    @abstractmethod
    def apply_move(self, board, move, player):
        pass

    @abstractmethod
    def check_win(self, board, player):
        pass

    @abstractmethod
    def is_draw(self, board):
        pass