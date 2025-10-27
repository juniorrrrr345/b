#!/bin/bash

echo "🔧 Diagnostic et correction du bot Telegram sur le VPS..."

# Vérifier le statut actuel
echo "📊 Statut actuel du bot:"
pm2 status

# Arrêter le bot
echo "⏹️ Arrêt du bot..."
pm2 stop telegram-bot

# Aller dans le répertoire du bot
cd /opt/telegram-bot

# Vérifier la version actuelle
echo "📋 Version actuelle du code:"
git log --oneline -5

# Sauvegarder les données importantes
echo "💾 Sauvegarde des données..."
cp data.json data.json.backup 2>/dev/null || echo "data.json non trouvé"
cp users.json users.json.backup 2>/dev/null || echo "users.json non trouvé"
cp admins.json admins.json.backup 2>/dev/null || echo "admins.json non trouvé"

# Nettoyer le cache git
echo "🧹 Nettoyage du cache git..."
git clean -fd
git reset --hard HEAD

# Récupérer la dernière version
echo "📥 Récupération de la dernière version..."
git fetch origin
git reset --hard origin/main

# Vérifier que la commande "repondre" est correcte
echo "🔍 Vérification de la commande repondre:"
grep -n "CommandHandler.*repondre" telegram_bot.py

# Restaurer les données
echo "🔄 Restauration des données..."
[ -f data.json.backup ] && cp data.json.backup data.json
[ -f users.json.backup ] && cp users.json.backup users.json
[ -f admins.json.backup ] && cp admins.json.backup admins.json

# Redémarrer le bot
echo "▶️ Redémarrage du bot..."
pm2 start telegram_bot.py --name telegram-bot --interpreter python3

# Attendre un peu
sleep 3

# Vérifier les logs
echo "📋 Vérification des logs (dernières 10 lignes):"
pm2 logs telegram-bot --lines 10

echo "✅ Correction terminée !"
echo "📋 Pour surveiller les logs: pm2 logs telegram-bot --follow"