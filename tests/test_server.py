print("Test Python OK!")

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.database.database import MatchmakingDatabase
    print("Import database OK!")
except Exception as e:
    print(f"Erreur import database: {e}")

try:
    import socket, threading, json
    print("Imports standard OK!")
except Exception as e:
    print(f"Erreur imports standard: {e}")