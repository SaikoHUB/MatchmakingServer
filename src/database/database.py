import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

class MatchmakingDatabase:
    def __init__(self, db_path: str = "matchmaking.db"):
        self.db_path = db_path
        self._init_db()
        self._add_default_games()
    
    def _init_db(self):
        """Initialise la base de données avec les tables nécessaires"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table des comptes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des sessions joueurs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    session_pseudo TEXT,
                    ip_address TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    is_guest BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                )
            """)
            
            # Table des jeux
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    initial_board_config TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des files d'attente
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    game_id INTEGER NOT NULL,
                    ranked BOOLEAN DEFAULT 1,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES player_sessions(id),
                    FOREIGN KEY (game_id) REFERENCES games(id)
                )
            """)
            
            # Table des matchs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    player1_id INTEGER NOT NULL,
                    player2_id INTEGER NOT NULL,
                    ranked BOOLEAN DEFAULT 1,
                    status TEXT DEFAULT 'active',
                    winner_id INTEGER,
                    board_state TEXT,
                    current_turn_player_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES games(id),
                    FOREIGN KEY (player1_id) REFERENCES player_sessions(id),
                    FOREIGN KEY (player2_id) REFERENCES player_sessions(id),
                    FOREIGN KEY (winner_id) REFERENCES player_sessions(id)
                )
            """)
            
            conn.commit()
    
    def _add_default_games(self):
        """Ajoute les jeux par défaut s'ils n'existent pas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Vérifier si des jeux existent déjà
            cursor.execute("SELECT COUNT(*) FROM games")
            if cursor.fetchone()[0] > 0:
                return
            
            # Configuration du Puissance 4
            connect4_config = {
                'board': [[0]*7 for _ in range(6)],  # 6 lignes, 7 colonnes
                'players': 2,
                'win_length': 4
            }
            
            # Configuration du Morpion
            tictactoe_config = {
                'board': [[0]*3 for _ in range(3)],  # 3x3
                'players': 2,
                'win_length': 3
            }
            
            # Ajouter les jeux
            games = [
                ('connect4', 'Puissance 4', 'Alignez 4 jetons', json.dumps(connect4_config)),
                ('tictactoe', 'Morpion', 'Alignez 3 symboles', json.dumps(tictactoe_config))
            ]
            
            cursor.executemany("""
                INSERT INTO games (name, display_name, description, initial_board_config)
                VALUES (?, ?, ?, ?)
            """, games)
            
            conn.commit()
    
    def register_account(self, username: str, password: str, display_name: str, email: Optional[str] = None) -> Optional[int]:
        """Enregistre un nouveau compte"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO accounts (username, password, display_name, email)
                    VALUES (?, ?, ?, ?)
                """, (username, password, display_name, email))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def login_account(self, username: str, password: str) -> Optional[Dict]:
        """Vérifie les identifiants et retourne les informations du compte"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, email
                FROM accounts
                WHERE username = ? AND password = ?
            """, (username, password))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'display_name': row[2],
                    'email': row[3]
                }
            return None
    
    def create_player_session(self, ip_address: str, port: int, account_id: Optional[int] = None, 
                            session_pseudo: Optional[str] = None) -> int:
        """Crée une nouvelle session joueur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO player_sessions (account_id, session_pseudo, ip_address, port)
                VALUES (?, ?, ?, ?)
            """, (account_id, session_pseudo, ip_address, port))
            return cursor.lastrowid
    
    def get_player_info(self, player_id: int) -> Optional[Dict]:
        """Récupère les informations d'un joueur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ps.id, ps.session_pseudo, a.display_name as account_display_name,
                       a.id as account_id, ps.account_id IS NULL as is_guest
                FROM player_sessions ps
                LEFT JOIN accounts a ON ps.account_id = a.id
                WHERE ps.id = ?
            """, (player_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'session_pseudo': row[1],
                    'account_display_name': row[2],
                    'account_id': row[3],
                    'is_guest': bool(row[4])
                }
            return None
    
    def add_to_queue(self, player_id: int, game_name: str, ranked: bool) -> int:
        """Ajoute un joueur à la file d'attente"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Vérifier si le joueur est déjà en file
            cursor.execute("""
                SELECT q.id FROM queues q
                JOIN games g ON q.game_id = g.id
                WHERE q.player_id = ? AND g.name = ?
            """, (player_id, game_name))
            
            if cursor.fetchone():
                return 0
            
            # Récupérer l'ID du jeu
            cursor.execute("SELECT id FROM games WHERE name = ?", (game_name,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Jeu '{game_name}' introuvable dans la base de données")
            game_id = row[0]
            
            # Ajouter à la file
            cursor.execute("""
                INSERT INTO queues (player_id, game_id, ranked)
                VALUES (?, ?, ?)
            """, (player_id, game_id, ranked))
            
            return cursor.lastrowid
    
    def remove_from_queue(self, player_id: int, game_id: int):
        """Retire un joueur de la file d'attente"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM queues
                WHERE player_id = ? AND game_id = ?
            """, (player_id, game_id))
    
    def get_queue_for_game(self, game_name: str, ranked: bool) -> List[Dict]:
        """Récupère la file d'attente pour un jeu"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.id, q.player_id, ps.session_pseudo, a.display_name, q.joined_at
                FROM queues q
                JOIN games g ON q.game_id = g.id
                JOIN player_sessions ps ON q.player_id = ps.id
                LEFT JOIN accounts a ON ps.account_id = a.id
                WHERE g.name = ? AND q.ranked = ?
                ORDER BY q.joined_at ASC
            """, (game_name, ranked))
            
            return [{
                'queue_id': row[0],
                'player_id': row[1],
                'pseudo': row[3] or row[2],
                'joined_at': row[4]
            } for row in cursor.fetchall()]
    
    def find_match_in_queue(self, game_name: str, ranked: bool) -> Optional[Tuple[Dict, Dict]]:
        """Trouve une paire de joueurs dans la file d'attente"""
        queue = self.get_queue_for_game(game_name, ranked)
        if len(queue) >= 2:
            return queue[0], queue[1]
        return None
    
    def create_match(self, game_name: str, player1: Dict, player2: Dict, ranked: bool) -> int:
        """Crée un nouveau match dans la base de données"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            game_info = self.get_game_by_name(game_name)
            if not game_info:
                raise ValueError(f"Jeu '{game_name}' introuvable")

            # Le initial_board_config est déjà un dictionnaire Python (décodé par get_game_by_name)
            # Il faut l'encoder en JSON pour le stocker dans la base de données des matchs
            initial_board_config_dict = game_info['initial_board_config']
            initial_board_config_json = json.dumps(initial_board_config_dict)
            
            cursor.execute("""
                INSERT INTO matches (game_id, player1_id, player2_id, ranked, status, board_state, current_turn_player_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                game_info['id'],
                player1['player_id'],
                player2['player_id'],
                ranked,
                'active',
                initial_board_config_json, # Utiliser la chaîne JSON
                player1['player_id'] # Player 1 commence
            ))
            
            return cursor.lastrowid
    
    def get_player_current_match(self, player_id: int, game_name: str) -> Optional[Dict]:
        """Récupère le match actif d'un joueur pour un jeu donné"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.game_id, m.player1_id, m.player2_id, m.ranked, m.status,
                       m.board_state, m.current_turn_player_id, m.winner_id, g.name as game_name
                FROM matches m
                JOIN games g ON m.game_id = g.id
                WHERE (m.player1_id = ? OR m.player2_id = ?)
                  AND g.name = ?
                  AND m.status = 'active'
            """, (player_id, player_id, game_name))
            
            row = cursor.fetchone()
            
            if row:
                # Décoder le board_state de JSON en dictionnaire Python lors de la lecture
                board_state_dict = json.loads(row[6])
                return {
                    'id': row[0],
                    'game_id': row[1],
                    'player1_id': row[2],
                    'player2_id': row[3],
                    'ranked': bool(row[4]),
                    'status': row[5],
                    'board_state': board_state_dict, # Retourner le dictionnaire
                    'current_turn_player_id': row[7],
                    'winner_id': row[8],
                    'game_name': row[9]
                }
            return None
    
    def update_match_state(self, match_id: int, board_state: List[int], current_turn_player_id: Optional[int], 
                           winner_id: Optional[int] = None, is_draw: bool = False):
        """Met à jour l'état d'un match"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            status = 'active'
            ended_at = None
            
            if winner_id is not None or is_draw:
                status = 'completed'
                ended_at = datetime.now().isoformat()

            # Encoder le board_state (liste ou dictionnaire Python) en JSON
            board_state_json = json.dumps(board_state)
            
            cursor.execute("""
                UPDATE matches
                SET board_state = ?, current_turn_player_id = ?, winner_id = ?, status = ?, ended_at = ?
                WHERE id = ?
            """, (board_state_json, current_turn_player_id, winner_id, status, ended_at, match_id))
            
            conn.commit()
    
    def get_all_games(self) -> List[Dict]:
        """Retourne la liste de tous les jeux disponibles"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, display_name, description, initial_board_config FROM games")
            games = []
            for row in cursor.fetchall():
                games.append({
                    'id': row[0],
                    'name': row[1],
                    'display_name': row[2],
                    'description': row[3],
                    'initial_board_config': json.loads(row[4])
                })
            return games
    
    def get_game_by_name(self, name: str) -> Optional[Dict]:
        """Retourne les informations d'un jeu par son nom"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, display_name, description, initial_board_config 
                FROM games WHERE name = ?
            """, (name,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'display_name': row[2],
                    'description': row[3],
                    'initial_board_config': json.loads(row[4])
                }
            return None
    
    def get_player_stats(self, pseudo: str, game_name: str) -> Dict:
        """Récupère les statistiques d'un joueur pour un jeu"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # TODO: Implémenter la logique des statistiques
            return {
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'elo_rating': 1000
            }


# =================== TESTS ===================
if __name__ == "__main__":
    print("=== Test système d'authentification et matchmaking ===")
    
    db = MatchmakingDatabase("test_auth_matchmaking.db")
    
    # Test création de comptes
    print("\n1. Test création de comptes:")
    alice_account = db.register_account("alice123", "motdepasse", "Alice")
    bob_account = db.register_account("bob456", "password", "Bob")
    
    # Test login
    print("\n2. Test login:")
    alice_login = db.login_account("alice123", "motdepasse")
    wrong_login = db.login_account("alice123", "mauvais_mot_de_passe")
    
    if alice_login:
        print(f"Alice connectée: {alice_login['display_name']}")
    if not wrong_login:
        print("Mauvais mot de passe rejeté ✓")
    
    # Test sessions
    print("\n3. Test sessions:")
    # Session compte connecté
    alice_session = db.create_player_session("192.168.1.100", 5000, alice_account)
    bob_session = db.create_player_session("192.168.1.101", 5001, bob_account)
    
    # Session invité
    guest_session = db.create_player_session("192.168.1.102", 5002, session_pseudo="InvitéTest")
    
    # Test files d'attente mixtes
    print("\n4. Test files d'attente (classées/non classées):")
    db.add_to_queue(alice_session, "connect4", ranked=True)  # Alice en classé
    db.add_to_queue(bob_session, "connect4", ranked=True)    # Bob en classé
    db.add_to_queue(guest_session, "connect4", ranked=False) # Invité en non classé (forcé)
    
    # Afficher les files
    ranked_queue = db.get_queue_for_game("connect4", ranked=True)
    unranked_queue = db.get_queue_for_game("connect4", ranked=False)
    
    print(f"File classée: {len(ranked_queue)} joueurs")
    for player in ranked_queue:
        print(f"  - {player['pseudo']} (ELO: {player['elo_rating']})")
    
    print(f"File non classée: {len(unranked_queue)} joueurs")
    for player in unranked_queue:
        guest_indicator = " [INVITÉ]" if player['is_guest'] else ""
        print(f"  - {player['pseudo']}{guest_indicator}")
    
    # Test matchmaking classé
    print("\n5. Test match classé:")
    ranked_match = db.find_match_in_queue("connect4", ranked=True)
    if ranked_match:
        player1, player2 = ranked_match
        match_id = db.create_match("connect4", player1, player2, ranked=True)
        print(f"Match classé créé: {player1['pseudo']} vs {player2['pseudo']}")
        
        # Simuler fin de match (Alice gagne)
        db.finish_match(match_id, 1)
    
    print("\n=== Tests terminés ===")