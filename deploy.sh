#!/bin/bash

# Script de déploiement pour le bot Telegram
# Usage: ./deploy.sh

set -e

echo "🚀 Déploiement du bot Telegram..."

# Variables
BOT_DIR="/opt/telegram-bot"
SERVICE_NAME="telegram-bot"
USER="ubuntu"

# Vérifier si on est root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Ne pas exécuter en tant que root. Utilisez sudo si nécessaire."
    exit 1
fi

# Créer le répertoire du bot
echo "📁 Création du répertoire du bot..."
sudo mkdir -p $BOT_DIR
sudo chown $USER:$USER $BOT_DIR

# Copier les fichiers
echo "📋 Copie des fichiers..."
cp telegram_bot.py $BOT_DIR/
cp requirements.txt $BOT_DIR/
cp .env.example $BOT_DIR/.env 2>/dev/null || echo "⚠️  Fichier .env.example non trouvé"

# Créer l'environnement virtuel
echo "🐍 Création de l'environnement virtuel..."
cd $BOT_DIR
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurer le service systemd
echo "⚙️  Configuration du service systemd..."
sudo cp telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Créer le fichier de données s'il n'existe pas
if [ ! -f "$BOT_DIR/data.json" ]; then
    echo "📄 Création du fichier de données..."
    cat > $BOT_DIR/data.json << EOF
{
    "contact": "📞 Contactez-nous : contact@monentreprise.com\\nTéléphone : +33 6 12 34 56 78",
    "services": "💼 Nos Services :\\n1️⃣ Développement Web\\n2️⃣ Design\\n3️⃣ Marketing Digital"
}
EOF
fi

# Donner les permissions
sudo chown -R $USER:$USER $BOT_DIR
chmod +x $BOT_DIR/telegram_bot.py

echo "✅ Déploiement terminé !"
echo ""
echo "📝 Prochaines étapes :"
echo "1. Éditez le fichier $BOT_DIR/.env pour configurer votre token"
echo "2. Redémarrez le service : sudo systemctl restart $SERVICE_NAME"
echo "3. Vérifiez le statut : sudo systemctl status $SERVICE_NAME"
echo "4. Consultez les logs : sudo journalctl -u $SERVICE_NAME -f"