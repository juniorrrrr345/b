#!/bin/bash

echo "🔄 Mise à jour du bot Telegram sur le VPS..."

# Arrêter le bot
echo "⏹️ Arrêt du bot..."
pm2 stop telegram-bot

# Aller dans le répertoire du bot
cd /opt/telegram-bot

# Sauvegarder les fichiers de données
echo "💾 Sauvegarde des données..."
cp data.json data.json.backup
cp users.json users.json.backup
cp admins.json admins.json.backup

# Mettre à jour depuis GitHub
echo "📥 Mise à jour depuis GitHub..."
git fetch origin
git reset --hard origin/main

# Restaurer les fichiers de données
echo "🔄 Restauration des données..."
cp data.json.backup data.json
cp users.json.backup users.json
cp admins.json.backup admins.json

# Redémarrer le bot
echo "▶️ Redémarrage du bot..."
pm2 start telegram_bot.py --name telegram-bot --interpreter python3

# Vérifier le statut
echo "📊 Statut du bot:"
pm2 status

echo "✅ Mise à jour terminée !"
echo "📋 Pour voir les logs: pm2 logs telegram-bot"