#!/bin/bash

# Script de déploiement pour la boutique e-commerce
# Usage: ./deploy.sh

set -e

echo "🛒 Déploiement de la boutique e-commerce..."

# Variables
BOUTIQUE_DIR="/opt/boutique"
SERVICE_NAME="boutique"
USER="ubuntu"
NGINX_SITE="boutique"

# Vérifier si on est root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Ne pas exécuter en tant que root. Utilisez sudo si nécessaire."
    exit 1
fi

# Créer le répertoire de la boutique
echo "📁 Création du répertoire de la boutique..."
sudo mkdir -p $BOUTIQUE_DIR
sudo chown $USER:$USER $BOUTIQUE_DIR

# Copier les fichiers
echo "📋 Copie des fichiers..."
cp -r . $BOUTIQUE_DIR/
cd $BOUTIQUE_DIR

# Créer l'environnement virtuel
echo "🐍 Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Créer le fichier .env s'il n'existe pas
if [ ! -f ".env" ]; then
    echo "⚙️  Création du fichier de configuration..."
    cp .env.example .env
    echo "📝 Veuillez éditer le fichier $BOUTIQUE_DIR/.env pour configurer votre application"
fi

# Créer le répertoire pour les logs
mkdir -p logs

# Configurer le service systemd
echo "⚙️  Configuration du service systemd..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Boutique E-commerce Flask Application
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$BOUTIQUE_DIR
Environment=PATH=$BOUTIQUE_DIR/venv/bin
ExecStart=$BOUTIQUE_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 3 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Configurer Nginx
echo "🌐 Configuration de Nginx..."
sudo tee /etc/nginx/sites-available/$NGINX_SITE > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $BOUTIQUE_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /favicon.ico {
        alias $BOUTIQUE_DIR/static/favicon.ico;
    }
}
EOF

# Activer le site Nginx
sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Donner les permissions
sudo chown -R $USER:$USER $BOUTIQUE_DIR
chmod +x $BOUTIQUE_DIR/app.py

# Initialiser la base de données
echo "🗄️  Initialisation de la base de données..."
source venv/bin/activate
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Base de données initialisée')
"

echo "✅ Déploiement terminé !"
echo ""
echo "📝 Prochaines étapes :"
echo "1. Éditez le fichier $BOUTIQUE_DIR/.env pour configurer votre application"
echo "2. Redémarrez le service : sudo systemctl restart $SERVICE_NAME"
echo "3. Vérifiez le statut : sudo systemctl status $SERVICE_NAME"
echo "4. Consultez les logs : sudo journalctl -u $SERVICE_NAME -f"
echo "5. Votre boutique sera accessible sur http://votre-ip"
echo ""
echo "🔐 Comptes par défaut :"
echo "   Admin: admin / admin123"
echo "   Client: client / client123"