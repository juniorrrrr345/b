#!/bin/bash

echo "🔧 Configuration du bot Telegram..."

# Vérifier si le token est déjà configuré
if grep -q "TON_TOKEN_ICI" /workspace/.env; then
    echo "⚠️  Token non configuré. Veuillez éditer le fichier .env :"
    echo "   nano /workspace/.env"
    echo ""
    echo "   Remplacez 'TON_TOKEN_ICI' par votre vrai token du bot"
    echo "   Exemple: TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    echo ""
    read -p "Appuyez sur Entrée quand vous avez configuré le token..."
fi

# Charger les variables d'environnement
export $(cat /workspace/.env | xargs)

# Vérifier que le token est configuré
if [ "$TELEGRAM_TOKEN" = "TON_TOKEN_ICI" ]; then
    echo "❌ Token non configuré. Veuillez éditer /workspace/.env"
    exit 1
fi

echo "✅ Token configuré: ${TELEGRAM_TOKEN:0:10}..."

# Démarrer le bot
echo "🚀 Démarrage du bot..."
cd /workspace
python3 telegram_bot.py