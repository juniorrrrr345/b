# 🛒 Boutique E-commerce

Une boutique en ligne moderne et complète développée avec Flask, prête pour le déploiement sur VPS.

## ✨ Fonctionnalités

### 🛍️ Frontend
- **Design moderne et responsive** avec Bootstrap 5
- **Interface utilisateur intuitive** avec animations CSS
- **Recherche et filtres** par catégorie
- **Panier d'achat** avec gestion des quantités
- **Processus de commande** complet
- **Système d'authentification** (inscription/connexion)

### 🔧 Backend
- **API REST** avec Flask
- **Base de données SQLite** avec SQLAlchemy
- **Gestion des utilisateurs** avec authentification sécurisée
- **Système de commandes** complet
- **Panneau d'administration** pour gérer les produits
- **Gestion des stocks** en temps réel

### 🚀 Déploiement
- **Script de déploiement automatique** pour VPS
- **Configuration Nginx** comme reverse proxy
- **Service systemd** pour la gestion des processus
- **Configuration PM2** (optionnel)
- **Logs centralisés** et monitoring

## 📋 Prérequis

- **VPS Ubuntu/Debian** avec accès root/sudo
- **Python 3.8+** installé
- **Nginx** installé
- **Git** installé

## 🚀 Installation et déploiement

### 1. Cloner le projet sur votre VPS

```bash
git clone <votre-repo> /opt/boutique
cd /opt/boutique
```

### 2. Exécuter le script de déploiement

```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. Configurer l'application

Éditez le fichier de configuration :

```bash
nano /opt/boutique/.env
```

Modifiez les valeurs suivantes :
```env
SECRET_KEY=votre-cle-secrete-tres-longue-et-complexe
DATABASE_URL=sqlite:///boutique.db
FLASK_ENV=production
```

### 4. Démarrer les services

```bash
# Démarrer la boutique
sudo systemctl start boutique

# Vérifier le statut
sudo systemctl status boutique

# Démarrer Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 5. Accéder à la boutique

Votre boutique sera accessible sur `http://votre-ip-vps`

## 👤 Comptes par défaut

### Administrateur
- **Nom d'utilisateur :** `admin`
- **Mot de passe :** `admin123`

### Client de test
- **Nom d'utilisateur :** `client`
- **Mot de passe :** `client123`

## 🛠️ Gestion de la boutique

### Commandes utiles

```bash
# Redémarrer la boutique
sudo systemctl restart boutique

# Voir les logs
sudo journalctl -u boutique -f

# Vérifier le statut
sudo systemctl status boutique

# Redémarrer Nginx
sudo systemctl restart nginx
```

### Gestion des produits

1. Connectez-vous avec le compte administrateur
2. Accédez au panneau d'administration
3. Ajoutez, modifiez ou supprimez des produits
4. Gérez les stocks et catégories

## 📁 Structure du projet

```
boutique/
├── app.py                 # Application Flask principale
├── requirements.txt       # Dépendances Python
├── deploy.sh             # Script de déploiement
├── ecosystem.config.js   # Configuration PM2
├── nginx.conf           # Configuration Nginx
├── .env.example         # Variables d'environnement
├── templates/           # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── products.html
│   ├── product_detail.html
│   ├── cart.html
│   ├── checkout.html
│   ├── login.html
│   ├── register.html
│   └── admin.html
├── static/              # Fichiers statiques
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── README.md
```

## 🔧 Configuration avancée

### SSL/HTTPS

Pour activer HTTPS, modifiez le fichier Nginx :

```bash
sudo nano /etc/nginx/sites-available/boutique
```

Décommentez et configurez la section HTTPS avec vos certificats SSL.

### Base de données

La boutique utilise SQLite par défaut. Pour utiliser PostgreSQL ou MySQL :

1. Installez le driver approprié
2. Modifiez `DATABASE_URL` dans `.env`
3. Redémarrez l'application

### Monitoring

Utilisez PM2 pour un monitoring avancé :

```bash
# Installer PM2
npm install -g pm2

# Démarrer avec PM2
pm2 start ecosystem.config.js

# Monitoring
pm2 monit
```

## 🛡️ Sécurité

- Changez le `SECRET_KEY` en production
- Utilisez HTTPS en production
- Configurez un pare-feu
- Mettez à jour régulièrement les dépendances
- Surveillez les logs

## 📞 Support

Pour toute question ou problème :

1. Vérifiez les logs : `sudo journalctl -u boutique -f`
2. Vérifiez la configuration Nginx : `sudo nginx -t`
3. Consultez la documentation Flask

## 🎯 Fonctionnalités à venir

- [ ] Système de paiement (Stripe, PayPal)
- [ ] Notifications email
- [ ] Gestion des avis clients
- [ ] Codes promo et réductions
- [ ] Multi-langues
- [ ] API mobile
- [ ] Dashboard analytics

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

---

**Développé avec ❤️ pour votre VPS**