# Bot Telegram avec Panneau d'Administration

Un bot Telegram simple avec un panneau d'administration pour modifier les textes dynamiquement.

## Fonctionnalités

- **Menu principal** : Boutons pour Contact et Services
- **Panneau d'administration** : Modification des textes en temps réel
- **Sécurité** : Authentification par mot de passe pour l'admin
- **Persistance** : Sauvegarde des données dans un fichier JSON
- **Déploiement VPS** : Scripts de déploiement automatique
- **Docker** : Support pour le déploiement en conteneur

## Installation Locale

1. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurer le bot** :
   - Obtenez un token depuis [@BotFather](https://t.me/botfather) sur Telegram
   - Copiez `.env.example` vers `.env` et configurez vos valeurs
   - Modifiez le mot de passe admin si nécessaire

3. **Lancer le bot** :
   ```bash
   python telegram_bot.py
   ```

## Déploiement sur VPS

### Méthode 1 : Script de déploiement automatique

1. **Préparer le VPS** :
   ```bash
   # Sur votre VPS Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git
   ```

2. **Cloner et déployer** :
   ```bash
   git clone <votre-repo>
   cd telegram-bot
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Configurer le bot** :
   ```bash
   sudo nano /opt/telegram-bot/.env
   # Ajoutez votre token Telegram
   ```

4. **Démarrer le service** :
   ```bash
   sudo systemctl start telegram-bot
   sudo systemctl status telegram-bot
   ```

### Méthode 2 : Docker

1. **Installer Docker** :
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Configurer et lancer** :
   ```bash
   cp .env.example .env
   # Éditez .env avec vos valeurs
   docker-compose up -d
   ```

### Gestion du service

```bash
# Démarrer le bot
sudo systemctl start telegram-bot

# Arrêter le bot
sudo systemctl stop telegram-bot

# Redémarrer le bot
sudo systemctl restart telegram-bot

# Voir les logs
sudo journalctl -u telegram-bot -f

# Statut du service
sudo systemctl status telegram-bot
```

## Utilisation

### Pour les utilisateurs
- `/start` : Affiche le menu principal avec les boutons Contact et Services

### Pour l'administrateur
- `/admin` : Accède au panneau d'administration (nécessite le mot de passe)
- **Modifier Contact** : Change le texte affiché pour la section Contact
- **Modifier Services** : Change le texte affiché pour la section Services
- **Quitter admin** : Se déconnecte du mode administrateur

## Structure des fichiers

```
/workspace/
├── telegram_bot.py      # Code principal du bot
├── requirements.txt     # Dépendances Python
├── data.json           # Fichier de données (créé automatiquement)
└── README.md           # Ce fichier
```

## Configuration

- **TOKEN** : Token de votre bot Telegram
- **ADMIN_PASSWORD** : Mot de passe pour accéder au panneau admin (défaut: "1234")
- **DATA_FILE** : Fichier de sauvegarde des données (défaut: "data.json")

## Sécurité

- Changez le mot de passe admin par défaut
- Le bot ne stocke que les ID des administrateurs connectés
- Les données sont sauvegardées localement dans un fichier JSON

## Développement

Pour ajouter de nouvelles sections :
1. Ajoutez la clé dans `load_data()` avec une valeur par défaut
2. Créez un bouton dans le menu principal
3. Ajoutez une option dans le panneau admin
4. Gérez la logique dans `admin_actions()`