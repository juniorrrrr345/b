# Bot Telegram avec Panneau d'Administration

Un bot Telegram simple avec un panneau d'administration pour modifier les textes dynamiquement.

## Fonctionnalités

- **Menu principal** : Boutons pour Contact et Services
- **Panneau d'administration** : Modification des textes en temps réel
- **Sécurité** : Authentification par mot de passe pour l'admin
- **Persistance** : Sauvegarde des données dans un fichier JSON

## Installation

1. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurer le bot** :
   - Obtenez un token depuis [@BotFather](https://t.me/botfather) sur Telegram
   - Remplacez `TON_TOKEN_ICI` dans `telegram_bot.py` par votre token
   - Modifiez le mot de passe admin `ADMIN_PASSWORD` si nécessaire

3. **Lancer le bot** :
   ```bash
   python telegram_bot.py
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