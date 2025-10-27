#!/bin/bash

echo "🚀 Mise à jour rapide du bot Telegram..."

# Arrêter le bot
pm2 stop telegram-bot

# Aller dans le répertoire
cd /opt/telegram-bot

# Sauvegarder les données
cp data.json data.json.bak 2>/dev/null
cp users.json users.json.bak 2>/dev/null
cp admins.json admins.json.bak 2>/dev/null

# Forcer la mise à jour
git fetch origin
git reset --hard origin/main

# Restaurer les données
cp data.json.bak data.json 2>/dev/null
cp users.json.bak users.json 2>/dev/null
cp admins.json.bak admins.json 2>/dev/null

# Redémarrer
pm2 start telegram_bot.py --name telegram-bot --interpreter python3

echo "✅ Mise à jour terminée !"
pm2 logs telegram-bot --lines 5