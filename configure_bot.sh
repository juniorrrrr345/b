#!/bin/bash

echo "🤖 Configuration du bot Telegram sur le VPS"
echo "============================================="

# Vérifier si le token est déjà configuré
if grep -q "TON_TOKEN_ICI" /workspace/.env; then
    echo ""
    echo "⚠️  Le token n'est pas configuré !"
    echo ""
    echo "📝 Pour configurer le token :"
    echo "   1. Ouvrez le fichier de configuration :"
    echo "      nano /workspace/.env"
    echo ""
    echo "   2. Remplacez 'TON_TOKEN_ICI' par votre vrai token du bot"
    echo "      Exemple: TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    echo ""
    echo "   3. Sauvegardez avec Ctrl+X, puis Y, puis Entrée"
    echo ""
    echo "🔑 Pour obtenir un token :"
    echo "   - Allez sur Telegram et cherchez @BotFather"
    echo "   - Tapez /newbot"
    echo "   - Suivez les instructions"
    echo ""
    read -p "Appuyez sur Entrée quand vous avez configuré le token..."
fi

# Vérifier que le token est configuré
if grep -q "TON_TOKEN_ICI" /workspace/.env; then
    echo "❌ Token non configuré. Veuillez éditer /workspace/.env"
    exit 1
fi

echo "✅ Token configuré !"
echo ""

# Charger les variables d'environnement
export $(cat /workspace/.env | xargs)

echo "🚀 Démarrage du bot..."
echo "📱 Le bot sera accessible via Telegram"
echo "🛑 Pour arrêter le bot, utilisez Ctrl+C"
echo ""

cd /workspace
python3 telegram_bot.py