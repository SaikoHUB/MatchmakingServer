# Système de Matchmaking et Jeux

Un système de matchmaking client-serveur avec interface graphique pour jouer au TicTacToe et au Puissance 4.

## Installation Rapide

1. **Installer le client** :
   - Double-cliquez sur `install_client.py`
   - Un raccourci sera créé sur votre bureau
   - Les dépendances seront installées automatiquement

2. **Lancer le serveur** (si vous hébergez) :
   ```bash
   python src/server/matchmaking_server.py
   ```

## Utilisation

1. **Pour jouer** :
   - Double-cliquez sur le raccourci "Matchmaking Client" sur votre bureau
   - Connectez-vous ou créez un compte
   - Choisissez un jeu et commencez à jouer !

2. **Pour héberger** :
   - Lancez le serveur avec la commande ci-dessus
   - Les joueurs pourront se connecter à votre adresse IP

## Fonctionnalités

- 🎮 Jeux disponibles : TicTacToe et Puissance 4
- 👥 Système de comptes et invités
- 🏆 Parties classées et non classées
- 📊 Statistiques et classement
- 📜 Historique des parties

## Structure du Projet

```
.
├── src/
│   ├── client/          # Interface graphique et client console
│   ├── server/          # Serveur de matchmaking
│   ├── common/          # Code partagé (jeux, etc.)
│   ├── config/          # Configuration
│   └── database/        # Gestion de la base de données
├── matchmaking.db       # Base de données
├── requirements.txt     # Dépendances
└── install_client.py    # Installation automatique
```

## Support

Pour toute question ou problème, n'hésitez pas à ouvrir une issue sur le dépôt. 