FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY telegram_bot.py .
COPY .env.example .env

# Créer le fichier de données par défaut
RUN echo '{"contact": "📞 Contactez-nous : contact@monentreprise.com\\nTéléphone : +33 6 12 34 56 78", "services": "💼 Nos Services :\\n1️⃣ Développement Web\\n2️⃣ Design\\n3️⃣ Marketing Digital"}' > data.json

# Exposer le port (optionnel, pour monitoring)
EXPOSE 8000

# Commande par défaut
CMD ["python", "telegram_bot.py"]