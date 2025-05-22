from src.client.console_client import MatchmakingClient
import time
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton

def main():
    # Créer deux clients
    client1 = MatchmakingClient()
    client2 = MatchmakingClient()
    
    # Connecter les clients
    print("\n=== Client 1 ===")
    client1.connect()
    client1.guest_login("Joueur1")
    
    print("\n=== Client 2 ===")
    client2.connect()
    client2.guest_login("Joueur2")
    
    # Attendre un peu pour la connexion
    time.sleep(1)
    
    # Rejoindre la file d'attente
    print("\n=== Client 1 rejoint la file ===")
    client1.join_queue("connect4", ranked=False)
    
    print("\n=== Client 2 rejoint la file ===")
    client2.join_queue("connect4", ranked=False)
    
    # Garder le script en vie
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt des clients...")
        client1.disconnect()
        client2.disconnect()

if __name__ == "__main__":
    main() 