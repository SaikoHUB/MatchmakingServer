import socket
import json
import threading
import sys
import time
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import os
from colorama import init, Fore, Back, Style
from src.common.chat import ChatMessage, ChatSystem, NotificationSystem, ChatManager

# Initialisation de colorama
init()

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
        
        # Système de chat
        self.chat_manager = ChatManager()
        
        # Thread pour recevoir les messages
        self.receive_thread = None
        
        # Nettoyer l'écran au démarrage
        self._clear_screen()
        
    def _clear_screen(self):
        """Nettoie l'écran de la console"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def _print_header(self, title: str):
        """Affiche un en-tête stylisé"""
        width = 60
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * width}")
        print(f"{title.center(width)}")
        print(f"{'=' * width}{Style.RESET_ALL}\n")
        
    def _print_success(self, message: str):
        """Affiche un message de succès"""
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        
    def _print_error(self, message: str):
        """Affiche un message d'erreur"""
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
        
    def _print_info(self, message: str):
        """Affiche un message d'information"""
        print(f"{Fore.BLUE}ℹ️ {message}{Style.RESET_ALL}")
        
    def _print_warning(self, message: str):
        """Affiche un message d'avertissement"""
        print(f"{Fore.YELLOW}⚠️ {message}{Style.RESET_ALL}")
        
    def _print_menu_item(self, number: str, text: str, icon: str = ""):
        """Affiche un élément du menu"""
        print(f"{Fore.CYAN}{number}.{Style.RESET_ALL} {icon} {text}")
        
    def _print_divider(self):
        """Affiche une ligne de séparation"""
        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
        
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
            
            self._print_success(f"✅ Connecté au serveur {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self._print_error(f"❌ Erreur de connexion: {e}")
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
        
        self._print_success("👋 Déconnecté du serveur")
    
    def _send_message(self, message: dict):
        """Envoie un message au serveur"""
        if not self.connected:
            self._print_error("❌ Pas connecté au serveur")
            return False
        
        try:
            message_json = json.dumps(message)
            self.socket.send(message_json.encode('utf-8'))
            return True
        except Exception as e:
            self._print_error(f"❌ Erreur envoi message: {e}")
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
                    self._print_error("❌ Message JSON invalide reçu")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self._print_error(f"❌ Erreur réception: {e}")
                break
        
        self.connected = False
    
    def _handle_server_message(self, message: dict):
        """Traite les messages reçus du serveur"""
        msg_type = message.get('type')
        
        if msg_type == 'register_success':
            self._print_success(message.get('message'))
            
        elif msg_type == 'register_error':
            self._print_error(f"❌ Erreur inscription: {message.get('message')}")
            
        elif msg_type == 'login_success':
            self.player_id = message.get('player_id')
            self.account_info = message.get('account_info')
            self.is_guest = False
            self._print_success(message.get('message'))
            self._print_info(f"   ID Joueur: {self.player_id}")
            
        elif msg_type == 'login_error':
            self._print_error(f"❌ Erreur connexion: {message.get('message')}")
            
        elif msg_type == 'guest_success':
            self.player_id = message.get('player_id')
            self.is_guest = True
            self._print_success(message.get('message'))
            self._print_info(f"   ID Joueur: {self.player_id}")
            
        elif msg_type == 'guest_error':
            self._print_error(f"❌ Erreur connexion invité: {message.get('message')}")
            
        elif msg_type == 'queue_joined':
            queue_pos = message.get('queue_position')
            game_name = message.get('game_name')
            ranked = message.get('ranked')
            mode = "classée" if ranked else "non classée"
            self._print_success(f"🎮 Ajouté à la file {mode} de {game_name}")
            self._print_info(f"   Position: {queue_pos} - En attente d'un adversaire...")
            
        elif msg_type == 'queue_error':
            self._print_error(f"❌ Erreur file d'attente: {message.get('message')}")
            
        elif msg_type == 'queue_left':
            self._print_success(f"🚪 {message.get('message')}")
            
        elif msg_type == 'match_found':
            self._handle_match_found(message)
            
        elif msg_type == 'games_list':
            self._display_games_list(message.get('games', []))
            
        elif msg_type == 'stats_result':
            self._display_stats(message.get('stats'))
            
        elif msg_type == 'game_history':
            self._display_game_history(message.get('history', []))
            
        elif msg_type == 'leaderboard':
            self._display_leaderboard(message.get('leaderboard', []))
            
        elif msg_type == 'chat_messages':
            self._display_chat_messages(message.get('messages', []))
            
        elif msg_type == 'notification':
            self.chat_manager.add_notification(message.get('content'))
            self._print_warning(f"🔔 {message.get('content')}")
            
        elif msg_type == 'private_message':
            self.chat_manager.add_message(
                ChatMessage(
                    sender_id=message.get('sender_id'),
                    sender_name=message.get('sender_name'),
                    content=message.get('content'),
                    timestamp=message.get('timestamp'),
                    message_type='private',
                    target=self.player_id
                )
            )
            self._print_info(f"🔒 Message privé de {message.get('sender_name')}: {message.get('content')}")
            
        elif msg_type == 'error':
            self._print_error(f"❌ Erreur: {message.get('message')}")
            
        elif msg_type == 'pong':
            self._print_success(f"🏓 Pong reçu: {message.get('timestamp')}")
            
        elif msg_type == 'make_move':
            self._handle_make_move(message)
            
        else:
            self._print_info(f"📨 Message reçu: {message}")
    
    def _handle_match_found(self, data: Dict):
        """Gère la notification de match trouvé"""
        self._print_header("🎮 Match trouvé! Vous jouez contre {data['opponent']['pseudo']}")
        self._print_info(f"Jeu: {data['game_display_name']}")
        if data['ranked']:
            self._print_info(f"Mode: Classé (ELO: {data['opponent']['elo_rating']})")
        else:
            self._print_info("Mode: Non classé")
        
        # Décodage du plateau
        board = json.loads(data['board']) if isinstance(data['board'], str) else data['board']
        self._display_board(board, data['game_name'])
        
        if data['your_turn']:
            self._print_info("\nC'est votre tour!")
        else:
            self._print_info("\nC'est au tour de votre adversaire")
    
    def _display_board(self, board: str, game_name: str):
        """Affiche le plateau de jeu"""
        if game_name == "Puissance 4":
            # Si board est déjà un dict/list, l'utiliser directement, sinon le décoder
            board_data = board if isinstance(board, (dict, list)) else json.loads(board)
            rows = len(board_data)
            cols = len(board_data[0])
            
            # Afficher les numéros de colonnes
            self._print_info("\n  " + " ".join(str(i) for i in range(cols)))
            
            # Afficher le plateau
            for row in board_data:
                self._print_info("| " + " ".join(str(cell) for cell in row) + " |")
            
            # Afficher la ligne du bas
            self._print_info("+" + "-" * (cols * 2 + 1) + "+")
        elif game_name.lower() == "morpion":
            self._print_info("  0 1 2")
            for i, row in enumerate(board):
                self._print_info(f"{i} {' '.join('⬜' if cell == 0 else ('❌' if cell == 1 else '⭕') for cell in row)}")
        else:
            self._print_info(f"Plateau: {board}")
    
    def _display_games_list(self, games):
        """Affiche la liste des jeux disponibles"""
        self._print_header("🎮 Jeux disponibles")
        self._print_divider()
        for i, game in enumerate(games, 1):
            self._print_menu_item(str(i), game['display_name'])
            self._print_info(f"   Nom: {game['name']}")
            self._print_info(f"   Description: {game['description']}")
            self._print_divider()
    
    def _display_stats(self, stats):
        """Affiche les statistiques"""
        if not stats:
            self._print_info("📊 Aucune statistique disponible (invité ou pas de parties jouées)")
            return
        
        self._print_header("📊 Statistiques")
        
        if isinstance(stats, list):
            for stat in stats:
                self._print_menu_item(str(i), stat['game'])
                self._print_info(f"   ELO: {Fore.YELLOW}{stat['elo_rating']:.0f}{Style.RESET_ALL}")
                self._print_info(f"   Parties: {Fore.CYAN}{stat['games_played']}{Style.RESET_ALL}")
                
                # Statistiques avec couleurs
                self._print_menu_item(str(i), f"Victoires: {Fore.GREEN}{stat['wins']}{Style.RESET_ALL}")
                self._print_menu_item(str(i), f"Défaites: {Fore.RED}{stat['losses']}{Style.RESET_ALL}")
                self._print_menu_item(str(i), f"Égalités: {Fore.YELLOW}{stat['draws']}{Style.RESET_ALL}")
                
                if stat['games_played'] > 0:
                    winrate = (stat['wins'] / stat['games_played']) * 100
                    winrate_color = Fore.GREEN if winrate >= 50 else Fore.RED
                    self._print_menu_item(str(i), f"Taux de victoire: {winrate_color}{winrate:.1f}%{Style.RESET_ALL}")
                
                self._print_divider()
        else:
            self._print_menu_item(str(i), f"🎮 {stats['game']}")
            self._print_info(f"   ELO: {Fore.YELLOW}{stats['elo_rating']:.0f}{Style.RESET_ALL}")
            self._print_info(f"   Parties: {Fore.CYAN}{stats['games_played']}{Style.RESET_ALL}")
            self._print_info(f"   Victoires: {Fore.GREEN}{stats['wins']}{Style.RESET_ALL}")
            self._print_info(f"   Défaites: {Fore.RED}{stats['losses']}{Style.RESET_ALL}")
            self._print_info(f"   Égalités: {Fore.YELLOW}{stats['draws']}{Style.RESET_ALL}")
            
            if stats['games_played'] > 0:
                winrate = (stats['wins'] / stats['games_played']) * 100
                winrate_color = Fore.GREEN if winrate >= 50 else Fore.RED
                self._print_menu_item(str(i), f"Taux de victoire: {winrate_color}{winrate:.1f}%{Style.RESET_ALL}")
    
    def _display_game_history(self, history: List[Dict[str, Any]]):
        """Affiche l'historique des parties"""
        if not history:
            self._print_info("📜 Aucune partie trouvée")
            return
        
        self._print_header("📜 Historique des parties")
        
        for game in history:
            self._print_menu_item(str(i), f"🎮 Partie #{game['game_id']}")
            self._print_info(f"   Jeu: {Fore.CYAN}{game['game_name']}{Style.RESET_ALL}")
            self._print_info(f"   Date: {Fore.CYAN}{game['date']}{Style.RESET_ALL}")
            
            # Affichage du résultat avec couleur
            result = game['result']
            if result == 'win':
                result_text = f"{Fore.GREEN}Victoire{Style.RESET_ALL}"
            elif result == 'loss':
                result_text = f"{Fore.RED}Défaite{Style.RESET_ALL}"
            else:
                result_text = f"{Fore.YELLOW}Égalité{Style.RESET_ALL}"
            self._print_menu_item(str(i), f"   Résultat: {result_text}")
            
            # Mode de jeu
            mode = "Classé" if game['ranked'] else "Non classé"
            mode_color = Fore.GREEN if game['ranked'] else Fore.BLUE
            self._print_menu_item(str(i), f"   Mode: {mode_color}{mode}{Style.RESET_ALL}")
            
            # Changement ELO
            if game['ranked']:
                elo_change = game['elo_change']
                elo_color = Fore.GREEN if elo_change > 0 else Fore.RED
                self._print_menu_item(str(i), f"   Changement ELO: {elo_color}{elo_change:+d}{Style.RESET_ALL}")
            
            self._print_divider()

    def _display_leaderboard(self, leaderboard: List[Dict[str, Any]]):
        """Affiche le classement"""
        if not leaderboard:
            self._print_info("🏆 Aucun classement disponible")
            return
        
        self._print_header("🏆 Classement")
        
        for i, player in enumerate(leaderboard, 1):
            # Couleur spéciale pour le top 3
            if i <= 3:
                rank_color = Fore.YELLOW if i == 1 else (Fore.LIGHTBLACK_EX if i == 2 else Fore.RED)
                rank_text = f"{rank_color}{i}.{Style.RESET_ALL}"
            else:
                rank_text = f"{Fore.CYAN}{i}.{Style.RESET_ALL}"
            
            self._print_menu_item(str(i), f"{Fore.GREEN}{player['display_name']}{Style.RESET_ALL}")
            self._print_info(f"   ELO: {Fore.YELLOW}{player['elo_rating']:.0f}{Style.RESET_ALL}")
            self._print_info(f"   Parties: {Fore.CYAN}{player['games_played']}{Style.RESET_ALL}")
            
            # Statistiques avec couleurs
            self._print_menu_item(str(i), f"Victoires: {Fore.GREEN}{player['wins']}{Style.RESET_ALL}")
            self._print_menu_item(str(i), f"Défaites: {Fore.RED}{player['losses']}{Style.RESET_ALL}")
            self._print_menu_item(str(i), f"Égalités: {Fore.YELLOW}{player['draws']}{Style.RESET_ALL}")
            
            if player['games_played'] > 0:
                winrate = (player['wins'] / player['games_played']) * 100
                winrate_color = Fore.GREEN if winrate >= 50 else Fore.RED
                self._print_menu_item(str(i), f"Taux de victoire: {winrate_color}{winrate:.1f}%{Style.RESET_ALL}")
            
            self._print_divider()

    def _display_chat_messages(self, messages: List[Dict[str, Any]]):
        """Affiche les messages du chat"""
        if not messages:
            self._print_info("💬 Aucun message")
            return
        
        self._print_header("💬 Messages récents")
        
        for msg in messages:
            # Couleur différente selon le type de message
            if msg['sender_id'] == 'system':
                sender_color = Fore.YELLOW
                content_color = Fore.YELLOW
                prefix = "🔔"
            elif msg.get('is_private', False):
                sender_color = Fore.MAGENTA
                content_color = Fore.MAGENTA
                prefix = "🔒"
            else:
                sender_color = Fore.GREEN
                content_color = Fore.WHITE
                prefix = "💬"
            
            # Afficher le message avec le bon format
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%H:%M:%S")
            self._print_menu_item(
                prefix,
                f"[{timestamp}] {sender_color}{msg['sender_name']}: {content_color}{msg['content']}{Style.RESET_ALL}"
            )
            self._print_divider()

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
            self._print_error("❌ Vous devez être connecté pour rejoindre une file")
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
            self._print_error("❌ Vous devez être connecté")
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
            self._print_error("❌ Vous devez être connecté")
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

    def get_game_history(self, game_name: str = None):
        """Récupère l'historique des parties"""
        if not self.player_id:
            self._print_error("❌ Vous devez être connecté")
            return False
        
        message = {
            'type': 'get_game_history',
            'player_id': self.player_id,
            'game_name': game_name
        }
        return self._send_message(message)

    def get_leaderboard(self, game_name: str = None):
        """Récupère le classement"""
        message = {
            'type': 'get_leaderboard',
            'game_name': game_name
        }
        return self._send_message(message)

    def get_chat_messages(self, count: int = 20):
        """Récupère les derniers messages du chat"""
        message = {
            'type': 'get_chat_messages',
            'count': count
        }
        return self._send_message(message)

    def send_chat_message(self, content: str):
        """Envoie un message dans le chat"""
        if not self.player_id:
            self._print_error("❌ Vous devez être connecté")
            return False
        
        message = {
            'type': 'chat_message',
            'player_id': self.player_id,
            'content': content
        }
        return self._send_message(message)

    def send_private_message(self, target_id: str, content: str):
        """Envoie un message privé"""
        if not self.player_id:
            self._print_error("❌ Vous devez être connecté")
            return False
        
        message = {
            'type': 'private_message',
            'player_id': self.player_id,
            'target_id': target_id,
            'content': content
        }
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
    client = MatchmakingClient()
    
    # Se connecter au serveur
    if not client.connect():
        client._print_error("Impossible de se connecter au serveur")
        return
    
    try:
        while client.connected:
            client._clear_screen()
            client._print_header("MENU PRINCIPAL")
            
            if not client.player_id:
                client._print_menu_item("1", "Se connecter", "🔑")
                client._print_menu_item("2", "Créer un compte", "📝")
                client._print_menu_item("3", "Jouer en invité", "🎭")
            else:
                pseudo = "Invité" if client.is_guest else client.account_info.get('display_name', 'Joueur')
                print(f"👤 Connecté en tant que: {pseudo}")
                print("4. 🎮 Voir les jeux disponibles")
                print("5. 🚀 Rejoindre une file d'attente")
                print("6. 🚪 Quitter une file d'attente")
                print("7. 📊 Voir mes statistiques")
                print("8. 📜 Voir mon historique de parties")
                print("9. 🏆 Voir le classement")
                print("10. 💬 Chat")
                print("11. 🏓 Ping serveur")
                print("12. 🔓 Se déconnecter")
            
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
                    if client.is_guest:
                        print("📜 Les invités n'ont pas d'historique")
                    else:
                        game_name = input("Jeu spécifique (optionnel): ") or None
                        client.get_game_history(game_name)
                        
                elif choice == "9" and client.player_id:
                    game_name = input("Jeu spécifique (optionnel): ") or None
                    client.get_leaderboard(game_name)
                    
                elif choice == "10" and client.player_id:
                    print("\n💬 Chat:")
                    print("1. Voir les messages récents")
                    print("2. Envoyer un message")
                    print("3. Messages privés")
                    chat_choice = input("Votre choix: ").strip()
                    
                    if chat_choice == "1":
                        client.get_chat_messages()
                    elif chat_choice == "2":
                        message = input("Message: ")
                        client.send_chat_message(message)
                    elif chat_choice == "3":
                        target = input("ID du destinataire: ")
                        message = input("Message: ")
                        client.send_private_message(target, message)
                    
                elif choice == "11" and client.player_id:
                    client.ping()
                    
                elif choice == "12" and client.player_id:
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