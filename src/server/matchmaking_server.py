import socket
import threading
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import traceback

# Ajouter le chemin pour importer la database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.database.database import MatchmakingDatabase

class MatchmakingServer:
    def __init__(self, host: str = "localhost", port: int = 8080, db_path: str = "matchmaking.db"):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
        # Base de données
        self.db = MatchmakingDatabase(db_path)
        
        # Gestion des clients connectés
        self.clients: Dict[int, Dict] = {}  # player_id -> {socket, thread, info}
        self.clients_lock = threading.Lock()
        
        # Gestionnaire de matchmaking automatique
        self.matchmaking_thread = None
        self.matchmaking_interval = 2  # Vérification toutes les 2 secondes
        
        print(f"Serveur de matchmaking initialisé sur {host}:{port}")
    
    def start(self):
        """Démarre le serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)  # Max 10 connexions en attente
            
            self.running = True
            print(f"🚀 Serveur démarré et en écoute sur {self.host}:{self.port}")
            
            # Démarrer le thread de matchmaking automatique
            self.matchmaking_thread = threading.Thread(target=self._auto_matchmaking, daemon=True)
            self.matchmaking_thread.start()
            
            # Boucle principale d'acceptation des connexions
            while self.running:
                try:
                    client_socket, client_address = self.socket.accept()
                    print(f"🔗 Nouvelle connexion de {client_address}")
                    
                    # Créer un thread pour gérer ce client
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        print(f"❌ Erreur socket: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Erreur lors du démarrage du serveur: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Arrête le serveur"""
        print("🛑 Arrêt du serveur...")
        self.running = False
        
        # Fermer toutes les connexions clients
        with self.clients_lock:
            for player_id, client_data in self.clients.items():
                try:
                    client_data['socket'].close()
                except:
                    pass
            self.clients.clear()
        
        # Fermer le socket principal
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("✅ Serveur arrêté")
    
    def _handle_client(self, client_socket: socket.socket, client_address: tuple):
        """Gère un client connecté"""
        player_id = None
        
        try:
            while self.running:
                # Recevoir le message
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    
                    # Traitement spécifique pour 'make_move' avec traceback complète
                    if message.get('type') == 'make_move':
                        try:
                            response = self._process_message(message, client_socket, client_address)
                        except Exception as e:
                            print(f"❌ Erreur lors du traitement de make_move pour {client_address}:")
                            traceback.print_exc()
                            response = {
                                'type': 'error',
                                'message': f'Erreur serveur lors du coup: {str(e)}'
                            }
                    else:
                        # Traitement standard pour les autres messages
                        response = self._process_message(message, client_socket, client_address)
                    
                    # Si c'est une connexion réussie, enregistrer le client
                    if response.get('type') in ['login_success', 'guest_success'] and response.get('player_id'):
                        player_id = response['player_id']
                        with self.clients_lock:
                            self.clients[player_id] = {
                                'socket': client_socket,
                                'thread': threading.current_thread(),
                                'address': client_address,
                                'last_seen': datetime.now()
                            }
                    
                    # Envoyer la réponse (si elle existe et n'a pas déjà été envoyée par un handler spécifique)
                    if response:
                        try:
                            response_json = json.dumps(response)
                            client_socket.send(response_json.encode('utf-8'))
                        except Exception as e:
                             print(f"❌ Erreur lors de l'envoi de la réponse au client {client_address}: {e}")
                        
                except json.JSONDecodeError:
                    error_response = {
                        'type': 'error',
                        'message': 'Format JSON invalide'
                    }
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                except Exception as e: # Gestion générique pour les erreurs non liées à 'make_move'
                    print(f"❌ Erreur lors du traitement du message (générique) pour {client_address}: {e}")
                    error_response = {
                        'type': 'error',
                        'message': 'Erreur serveur générique'
                    }
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
        
        except ConnectionResetError:
            print(f"🔌 Connexion fermée par le client {client_address}")
        except Exception as e:
            print(f"❌ Erreur avec le client {client_address}: {e}")
        finally:
            # Nettoyer lors de la déconnexion
            if player_id:
                self._handle_client_disconnect(player_id)
            
            try:
                client_socket.close()
            except:
                pass
            
            print(f"👋 Client {client_address} déconnecté")
    
    def _process_message(self, message: Dict, client_socket: socket.socket, client_address: tuple) -> Dict:
        """Traite un message reçu d'un client"""
        msg_type = message.get('type')
        
        if msg_type == 'register':
            return self._handle_register(message)
        elif msg_type == 'login':
            return self._handle_login(message, client_address)
        elif msg_type == 'guest_login':
            return self._handle_guest_login(message, client_address)
        elif msg_type == 'join_queue':
            return self._handle_join_queue(message)
        elif msg_type == 'leave_queue':
            return self._handle_leave_queue(message)
        elif msg_type == 'get_games':
            return self._handle_get_games()
        elif msg_type == 'make_move':
            return self._handle_make_move(message)
        elif msg_type == 'get_stats':
            return self._handle_get_stats(message)
        elif msg_type == 'ping':
            return {'type': 'pong', 'timestamp': datetime.now().isoformat()}
        else:
            return {
                'type': 'error',
                'message': f'Type de message inconnu: {msg_type}'
            }
    
    def _handle_register(self, message: Dict) -> Dict:
        """Gère l'inscription d'un nouveau compte"""
        try:
            username = message.get('username')
            password = message.get('password')
            display_name = message.get('display_name')
            email = message.get('email')
            
            if not all([username, password, display_name]):
                return {
                    'type': 'register_error',
                    'message': 'Nom d\'utilisateur, mot de passe et nom d\'affichage requis'
                }
            
            account_id = self.db.register_account(username, password, display_name, email)
            
            if account_id:
                return {
                    'type': 'register_success',
                    'account_id': account_id,
                    'message': f'Compte créé avec succès pour {username}'
                }
            else:
                return {
                    'type': 'register_error',
                    'message': 'Nom d\'utilisateur déjà utilisé'
                }
                
        except Exception as e:
            return {
                'type': 'register_error',
                'message': f'Erreur lors de l\'inscription: {str(e)}'
            }
    
    def _handle_login(self, message: Dict, client_address: tuple) -> Dict:
        """Gère la connexion d'un compte"""
        try:
            username = message.get('username')
            password = message.get('password')
            
            if not all([username, password]):
                return {
                    'type': 'login_error',
                    'message': 'Nom d\'utilisateur et mot de passe requis'
                }
            
            account_info = self.db.login_account(username, password)
            
            if account_info:
                # Créer une session de joueur
                player_id = self.db.create_player_session(
                    ip_address=client_address[0],
                    port=client_address[1],
                    account_id=account_info['id']
                )
                
                return {
                    'type': 'login_success',
                    'player_id': player_id,
                    'account_info': account_info,
                    'message': f'Connexion réussie, bienvenue {account_info["display_name"]}!'
                }
            else:
                return {
                    'type': 'login_error',
                    'message': 'Nom d\'utilisateur ou mot de passe incorrect'
                }
                
        except Exception as e:
            return {
                'type': 'login_error',
                'message': f'Erreur lors de la connexion: {str(e)}'
            }
    
    def _handle_guest_login(self, message: Dict, client_address: tuple) -> Dict:
        """Gère la connexion en tant qu'invité"""
        try:
            pseudo = message.get('pseudo', f"Invité{datetime.now().strftime('%H%M%S')}")
            
            # Créer une session invité
            player_id = self.db.create_player_session(
                ip_address=client_address[0],
                port=client_address[1],
                account_id=None,
                session_pseudo=pseudo
            )
            
            return {
                'type': 'guest_success',
                'player_id': player_id,
                'pseudo': pseudo,
                'message': f'Connexion invité réussie, bienvenue {pseudo}!'
            }
            
        except Exception as e:
            return {
                'type': 'guest_error',
                'message': f'Erreur lors de la connexion invité: {str(e)}'
            }
    
    def _handle_join_queue(self, message: Dict) -> Dict:
        """Gère l'ajout à la file d'attente"""
        try:
            player_id = message.get('player_id')
            game_name = message.get('game_name')
            ranked = message.get('ranked', True)
            
            if not all([player_id, game_name]):
                return {
                    'type': 'queue_error',
                    'message': 'ID joueur et nom du jeu requis'
                }
            
            queue_id = self.db.add_to_queue(player_id, game_name, ranked)
            
            if queue_id > 0:
                queue_count = len(self.db.get_queue_for_game(game_name, ranked))
                mode = "classée" if ranked else "non classée"
                
                return {
                    'type': 'queue_joined',
                    'queue_id': queue_id,
                    'game_name': game_name,
                    'ranked': ranked,
                    'queue_position': queue_count,
                    'message': f'Ajouté à la file {mode} de {game_name}. Position: {queue_count}'
                }
            else:
                return {
                    'type': 'queue_error',
                    'message': 'Déjà en file d\'attente pour ce jeu'
                }
                
        except Exception as e:
            return {
                'type': 'queue_error',
                'message': f'Erreur lors de l\'ajout à la file: {str(e)}'
            }
    
    def _handle_leave_queue(self, message: Dict) -> Dict:
        """Gère la sortie de la file d'attente"""
        try:
            player_id = message.get('player_id')
            game_name = message.get('game_name')
            
            if not all([player_id, game_name]):
                return {
                    'type': 'error',
                    'message': 'ID joueur et nom du jeu requis'
                }
            
            game = self.db.get_game_by_name(game_name)
            if game:
                self.db.remove_from_queue(player_id, game['id'])
                return {
                    'type': 'queue_left',
                    'message': f'Retiré de la file d\'attente de {game_name}'
                }
            else:
                return {
                    'type': 'error',
                    'message': 'Jeu non trouvé'
                }
                
        except Exception as e:
            return {
                'type': 'error',
                'message': f'Erreur lors de la sortie de file: {str(e)}'
            }
    
    def _handle_get_games(self) -> Dict:
        """Retourne la liste des jeux disponibles"""
        try:
            games = self.db.get_all_games()
            return {
                'type': 'games_list',
                'games': games
            }
        except Exception as e:
            return {
                'type': 'error',
                'message': f'Erreur lors de la récupération des jeux: {str(e)}'
            }
    
    def _handle_make_move(self, message: Dict) -> Optional[Dict]:
        """Gère un coup joué par un joueur"""
        player_id = message.get('player_id')
        game_name = message.get('game_name')
        move_index = message.get('move')

        if not all([player_id, game_name, isinstance(move_index, int) and 0 <= move_index < 9]):
            return {
                'type': 'error',
                'message': 'Données de coup invalides'
            }

        # 1. Récupérer l'état du match
        match = self.db.get_player_current_match(player_id, game_name)

        if not match:
            return {
                'type': 'error',
                'message': 'Aucune partie en cours pour ce joueur'
            }

        match_id = match['id']
        # match['board_state'] contient le dictionnaire complet du plateau (e.g. {'board': [[...]], ...})
        board_config = match['board_state'] # Récupère le dictionnaire complet
        board_data = board_config.get('board') # Extraire la liste de listes du plateau
        current_turn_player_id = match['current_turn_player_id']
        player1_id = match['player1_id']
        player2_id = match['player2_id']

        # Vérifier si c'est bien le tour du joueur
        if player_id != current_turn_player_id:
            return {
                'type': 'error',
                'message': "Ce n'est pas votre tour"
            }

        # Vérifier si board_data a le bon format pour TicTacToe (liste de listes)
        if not isinstance(board_data, list) or len(board_data) != 3 or any(not isinstance(row, list) or len(row) != 3 for row in board_data):
             return {
                'type': 'error',
                'message': 'Format de plateau invalide reçu du serveur'
            }

        # Déterminer le symbole du joueur (X ou O)
        player_symbol_value = 1 if player_id == player1_id else 2 # 1 pour X, 2 pour O

        # Convertir l'index 0-8 en (ligne, colonne)
        row = move_index // 3
        col = move_index % 3

        # 2. Valider le coup
        if board_data[row][col] != 0: # 0 signifie case vide
            return {
                'type': 'error',
                'message': "Cette case est déjà occupée"
            }

        # 3. Appliquer le coup et mettre à jour l'état
        board_data[row][col] = player_symbol_value

        # 4. Vérifier la fin de partie (Victoire ou Nul) - Logique TicTacToe
        winner_id = None
        is_draw = False

        # Vérifier les lignes
        for r in range(3):
            if board_data[r][0] == player_symbol_value and board_data[r][1] == player_symbol_value and board_data[r][2] == player_symbol_value:
                winner_id = player_id
                break

        # Vérifier les colonnes
        if winner_id is None:
            for c in range(3):
                if board_data[0][c] == player_symbol_value and board_data[1][c] == player_symbol_value and board_data[2][c] == player_symbol_value:
                    winner_id = player_id
                    break

        # Vérifier les diagonales
        if winner_id is None:
            # Diagonale principale
            if board_data[0][0] == player_symbol_value and board_data[1][1] == player_symbol_value and board_data[2][2] == player_symbol_value:
                winner_id = player_id
            # Diagonale secondaire
            elif board_data[0][2] == player_symbol_value and board_data[1][1] == player_symbol_value and board_data[2][0] == player_symbol_value:
                 winner_id = player_id

        # Vérifier match nul
        if winner_id is None and all(cell != 0 for row in board_data for cell in row):
            is_draw = True

        # Déterminer le prochain joueur ou terminer la partie
        next_turn_player_id = None
        if winner_id is None and not is_draw:
            next_turn_player_id = player2_id if player_id == player1_id else player1_id

        # 5. Mettre à jour la DB
        # Mettre à jour le dictionnaire complet board_config avec l'état modifié du plateau
        board_config['board'] = board_data
        self.db.update_match_state(
            match_id,
            board_config, # Passer le dictionnaire complet mis à jour
            next_turn_player_id,
            winner_id,
            is_draw
        )

        # 6. Notifier les deux joueurs
        opponent_id = player2_id if player_id == player1_id else player1_id
        
        if winner_id is not None or is_draw:
            # Envoyer message game_over
            winner_symbol = "X" if winner_id == player1_id else ("O" if winner_id == player2_id else None)
            game_over_message = {
                'type': 'game_over',
                'match_id': match_id,
                'winner_id': winner_id,
                'winner_symbol': winner_symbol,
                'board': board_data # Envoyer uniquement les données du plateau dans game_over
            }
            self._send_to_player(player_id, game_over_message)
            self._send_to_player(opponent_id, game_over_message)
            
            # TODO: Gérer la fin de partie dans la DB (stats, etc.)
            
        else:
            # Envoyer message game_update
            game_update_message = {
                'type': 'game_update',
                'match_id': match_id,
                'board': board_data, # Envoyer uniquement les données du plateau
                'current_turn_player_id': next_turn_player_id
            }
            self._send_to_player(player_id, game_update_message)
            self._send_to_player(opponent_id, game_update_message)

        # Retourner une réponse vide ou simple confirmation au joueur qui a joué
        return {
            'type': 'move_received',
            'message': 'Coup traité par le serveur'
        }
    
    def _handle_get_stats(self, message: Dict) -> Dict:
        """Retourne les statistiques d'un joueur"""
        try:
            player_id = message.get('player_id')
            game_name = message.get('game_name')
            
            if not player_id:
                return {
                    'type': 'error',
                    'message': 'ID joueur requis'
                }
            
            player_info = self.db.get_player_info(player_id)
            if not player_info or player_info['is_guest']:
                return {
                    'type': 'stats_result',
                    'message': 'Pas de statistiques pour les invités'
                }
            
            # Récupérer les stats via le pseudo du compte
            pseudo = player_info['account_display_name'] or player_info['session_pseudo']
            stats = self.db.get_player_stats(pseudo, game_name)
            
            return {
                'type': 'stats_result',
                'stats': stats
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': f'Erreur lors de la récupération des stats: {str(e)}'
            }
    
    def _auto_matchmaking(self):
        """Thread de matchmaking automatique"""
        print("🤖 Matchmaking automatique démarré")
        
        while self.running:
            try:
                # Récupérer tous les jeux
                games = self.db.get_all_games()
                
                for game in games:
                    # Vérifier les files classées et non classées
                    for ranked in [True, False]:
                        match_found = self.db.find_match_in_queue(game['name'], ranked)
                        
                        if match_found:
                            player1, player2 = match_found
                            
                            # Créer le match
                            match_id = self.db.create_match(game['name'], player1, player2, ranked)
                            
                            # Retirer les joueurs de la file
                            game_info = self.db.get_game_by_name(game['name'])
                            self.db.remove_from_queue(player1['player_id'], game_info['id'])
                            self.db.remove_from_queue(player2['player_id'], game_info['id'])
                            
                            # Notifier les joueurs
                            self._notify_match_found(match_id, player1, player2, game, ranked)
                
                # Attendre avant la prochaine vérification
                threading.Event().wait(self.matchmaking_interval)
                
            except Exception as e:
                print(f"❌ Erreur dans le matchmaking automatique: {e}")
                threading.Event().wait(self.matchmaking_interval)
    
    def _notify_match_found(self, match_id: int, player1: Dict, player2: Dict, game: Dict, ranked: bool):
        """Notifie les joueurs qu'un match a été trouvé"""
        match_notification = {
            'type': 'match_found',
            'match_id': match_id,
            'game_name': game['name'],
            'game_display_name': game['display_name'],
            'ranked': ranked,
            'opponent': {
                'pseudo': player2['pseudo'],
                'elo_rating': player2['elo_rating'] if ranked else None
            },
            'your_turn': True,  # Joueur 1 commence
            'board': json.dumps(game['initial_board_config'])
        }
        
        # Notification pour joueur 1
        self._send_to_player(player1['player_id'], match_notification)
        
        # Notification pour joueur 2 (avec your_turn à False)
        match_notification['opponent']['pseudo'] = player1['pseudo']
        match_notification['opponent']['elo_rating'] = player1['elo_rating'] if ranked else None
        match_notification['your_turn'] = False
        self._send_to_player(player2['player_id'], match_notification)
        
        # Envoyer le premier game_update au joueur dont c'est le tour
        initial_game_update = {
            'type': 'game_update',
            'match_id': match_id,
            'board': game['initial_board_config']['board'], # Envoyer le plateau extrait
            'current_turn_player_id': player1['player_id'] # C'est le tour du joueur 1
        }
        self._send_to_player(player1['player_id'], initial_game_update)

        mode = "classé" if ranked else "non classé"
        print(f"🎮 Match {mode} créé: {player1['pseudo']} vs {player2['pseudo']} ({game['display_name']})")
    
    def _send_to_player(self, player_id: int, message: Dict):
        """Envoie un message à un joueur spécifique"""
        with self.clients_lock:
            if player_id in self.clients:
                try:
                    client_socket = self.clients[player_id]['socket']
                    message_json = json.dumps(message)
                    client_socket.send(message_json.encode('utf-8'))
                except Exception as e:
                    print(f"❌ Erreur envoi message au joueur {player_id}: {e}")
    
    def _handle_client_disconnect(self, player_id: int):
        """Gère la déconnexion d'un client"""
        with self.clients_lock:
            if player_id in self.clients:
                del self.clients[player_id]
        
        # Retirer de toutes les files d'attente
        try:
            games = self.db.get_all_games()
            for game in games:
                self.db.remove_from_queue(player_id, game['id'])
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage pour le joueur {player_id}: {e}")
        
        print(f"🧹 Joueur {player_id} nettoyé des files d'attente")
    
    def get_server_stats(self) -> Dict:
        """Retourne les statistiques du serveur"""
        with self.clients_lock:
            connected_players = len(self.clients)
        
        # Compter les files d'attente
        total_in_queue = 0
        games = self.db.get_all_games()
        for game in games:
            for ranked in [True, False]:
                total_in_queue += len(self.db.get_queue_for_game(game['name'], ranked))
        
        return {
            'connected_players': connected_players,
            'players_in_queue': total_in_queue,
            'available_games': len(games),
            'server_uptime': 'TODO',  # À implémenter
        }


def main():
    """Point d'entrée principal du serveur"""
    import signal
    
    # Configuration
    HOST = "localhost"  # Modifier pour "0.0.0.0" pour accepter connexions externes
    PORT = 8080
    DB_PATH = "matchmaking.db"
    
    server = MatchmakingServer(HOST, PORT, DB_PATH)
    
    # Gestion propre de l'arrêt avec Ctrl+C
    def signal_handler(sig, frame):
        print("\n🛑 Arrêt demandé...")
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt par l'utilisateur")
        server.stop()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        server.stop()


if __name__ == "__main__":
    main()