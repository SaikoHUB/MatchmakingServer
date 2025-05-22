# Système de Matchmaking et Jeux

Ce projet implémente un système de matchmaking client-serveur simple avec une interface graphique pour jouer au TicTacToe.

## Structure du Projet

```
.
├── client_gui.py         # Client avec interface graphique PyQt6
├── matchmaking.db        # Base de données SQLite pour le matchmaking et les comptes
├── requirements.txt      # Dépendances Python nécessaires
├── install_client.py     # Script pour installer les dépendances du client
├── src/
│   ├── client/
│   │   └── console_client.py # Client console (utilisé par le client GUI)
│   ├── database/
│   │   └── database.py     # Logique d'accès à la base de données
│   └── server/
│       ├── matchmaking_server.py # Logique principale du serveur
│       ├── game_manager.py     # (Potentiel) Logique de gestion des jeux
│       └── socket_handler.py   # (Potentiel) Gestion des connexions sockets
├── tests/                # Dossier pour les tests unitaires (actuellement vide ou non pertinent pour l'exécution principale)
├── .venv/                # Ancien environnement virtuel (peut être supprimé si .venv_new est utilisé)
└── .venv_new/            # Nouvel environnement virtuel (recommandé)
```

## Configuration et Installation

Il est recommandé d'utiliser un environnement virtuel pour isoler les dépendances du projet.

1.  **Créer un environnement virtuel** (si ce n'est pas déjà fait, idéalement `.venv_new`):

    ```bash
    python -m venv .venv_new
    ```

2.  **Activer l'environnement virtuel**:

    *   Windows (Command Prompt):
        ```bash
        .venv_new\Scripts\activate.bat
        ```
    *   Windows (PowerShell):
        ```powershell
        .venv_new\Scripts\Activate.ps1
        ```
    *   macOS/Linux (Bash/Zsh):
        ```bash
        source .venv_new/bin/activate
        ```

3.  **Installer les dépendances**:

    Vous pouvez installer les dépendances en exécutant `pip` directement:

    ```bash
    pip install -r requirements.txt
    ```

    Alternativement, vous pouvez exécuter le script `install_client.py` *après avoir activé l'environnement virtuel*. Ce script installera les dépendances et créera également un raccourci sur le bureau (principalement sous Windows) pour lancer le client graphique.

    ```bash
    python install_client.py
    ```

4.  **Supprimer l'ancien environnement virtuel (optionnel)**:

    Si vous avez confirmé utiliser `.venv_new`, vous pouvez supprimer `.venv`:

    *   Windows:
        ```powershell
        Remove-Item -Recurse -Force .venv
        ```
    *   macOS/Linux:
        ```bash
        rm -rf .venv
        ```

## Utilisation

Pour utiliser le système, vous devez d'abord lancer le serveur, puis le ou les clients graphiques dans des terminaux séparés.

1.  **Lancer le Serveur**:

    Ouvrez un terminal, activez votre environnement virtuel (`.venv_new`), puis exécutez le script du serveur. Le serveur utilise par défaut `localhost:8080` et le fichier `matchmaking.db`.

    ```bash
    python src/server/matchmaking_server.py
    ```

    Laissez ce terminal ouvert et le serveur en cours d'exécution.

2.  **Lancer le Client Graphique**:

    Ouvrez un *autre* terminal, activez également votre environnement virtuel (`.venv_new`), puis exécutez le script client GUI.

    ```bash
    python client_gui.py
    ```

    Le client vous présentera une fenêtre de connexion/inscription. Vous pouvez lancer plusieurs instances du client graphique pour simuler plusieurs joueurs.

## Fonctionnalités Implémentées

- Connexion en tant qu'invité
- Connexion / Création de compte (logique côté client commentée, à implémenter côté serveur et client)
- Sélection de jeu (TicTacToe, Connect4)
- Matchmaking simple (trouve un adversaire si disponible dans la file d'attente pour le même jeu et mode)
- Partie de TicTacToe avec interface graphique
- Affichage du plateau et gestion des tours
- Détection de fin de partie (victoire, nul)
- Bouton pour revenir à l'écran de sélection de jeu après une partie

## Fonctionnalités à Implémenter (TODO)

- Logique complète d'inscription et de connexion (vérification mot de passe, hachage, etc.)
- Gestion complète du jeu Connect4
- Parties classées (gestion ELO/statistiques)
- Gestion des déconnexions en cours de partie
- Amélioration de la gestion des erreurs et des messages réseau 