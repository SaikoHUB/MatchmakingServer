import subprocess
import sys
import os

def install_requirements():
    print("Installation des dépendances...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dépendances installées avec succès!")

def create_shortcut():
    print("Création du raccourci...")
    if sys.platform == "win32":
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Matchmaking Client.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = os.path.abspath("src/client/gui_client.py")
        shortcut.WorkingDirectory = os.path.abspath(".")
        shortcut.save()
        print("✅ Raccourci créé sur le bureau!")
    else:
        print("ℹ️ Création de raccourci non supportée sur ce système d'exploitation")

def main():
    print("=== Installation du Client Matchmaking ===")
    install_requirements()
    create_shortcut()
    print("\n✅ Installation terminée!")
    print("\nPour lancer le client:")
    print("1. Double-cliquez sur le raccourci 'Matchmaking Client' sur votre bureau")
    print("2. Ou exécutez: python src/client/gui_client.py")
    print("\nAssurez-vous que le serveur est en cours d'exécution avant de lancer le client!")

if __name__ == "__main__":
    main() 