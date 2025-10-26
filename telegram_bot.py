import json
import os
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# Configuration depuis les variables d'environnement
TOKEN = os.getenv("TELEGRAM_TOKEN", "TON_TOKEN_ICI")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")
DATA_FILE = os.getenv("DATA_FILE", "data.json")
USERS_FILE = os.getenv("USERS_FILE", "users.json")


# --- Charger les données depuis le fichier JSON ---
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        data = {
            "contact": "📞 Contactez-nous : contact@monentreprise.com\nTéléphone : +33 6 12 34 56 78",
            "services": "💼 Nos Services :\n1️⃣ Développement Web\n2️⃣ Design\n3️⃣ Marketing Digital",
            "welcome_text": "👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :",
            "welcome_photo": None,
        }
        save_data(data)
        return data


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Gestion des utilisateurs ---
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": [], "messages": []}

def save_users(users_data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

def add_user(user_id, username, first_name, last_name):
    users_data = load_users()
    user_info = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name
    }
    
    # Vérifier si l'utilisateur existe déjà
    for user in users_data["users"]:
        if user["user_id"] == user_id:
            return
    
    users_data["users"].append(user_info)
    save_users(users_data)

def add_message(user_id, username, first_name, last_name, message_text, timestamp):
    users_data = load_users()
    message_info = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "message": message_text,
        "timestamp": timestamp
    }
    users_data["messages"].append(message_info)
    save_users(users_data)

async def clear_all_bot_messages(context):
    """Supprime tous les messages du bot avec tous les utilisateurs"""
    users_data = load_users()
    users = users_data["users"]
    deleted_count = 0
    
    for user in users:
        try:
            chat_id = user["user_id"]
            
            # Essayer de supprimer les messages récents
            # Note: L'API Telegram limite la suppression aux messages des 48 dernières heures
            try:
                # Récupérer les messages récents (limité à 100 pour éviter les timeouts)
                message_ids = []
                async for message in context.bot.iter_history(chat_id, limit=100):
                    if message.from_user and message.from_user.id == context.bot.id:
                        message_ids.append(message.message_id)
                
                # Supprimer les messages par lots pour éviter les limites de rate
                for message_id in message_ids:
                    try:
                        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                        deleted_count += 1
                        # Petite pause pour éviter les limites de rate
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        # Ignorer les erreurs de suppression (message trop ancien, etc.)
                        continue
                        
            except Exception as e:
                # Si on ne peut pas accéder à l'historique, continuer
                continue
                    
        except Exception as e:
            print(f"Erreur lors de la suppression des messages pour {user['user_id']}: {e}")
            continue
    
    return deleted_count


data = load_data()
admins = set()  # liste des ID admins connectés


# --- Commande /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Enregistrer l'utilisateur
    user = update.effective_user
    add_user(
        user.id,
        user.username,
        user.first_name,
        user.last_name
    )
    
    # Supprimer l'ancien message s'il existe
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
        except:
            pass
    
    keyboard = [
        [
            InlineKeyboardButton("📞 Contact", callback_data="contact"),
            InlineKeyboardButton("💼 Nos Services", callback_data="services"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = data.get("welcome_text", "👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :")
    welcome_photo = data.get("welcome_photo")
    
    if welcome_photo:
        await update.message.reply_photo(
            photo=welcome_photo,
            caption=welcome_text,
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
        )


# --- Boutons ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Gestion des callbacks admin
    if query.data.startswith("admin_"):
        await handle_admin_callback(query, context)
        return
    
    # Gestion des callbacks normaux
    if query.data == "back_to_main":
        keyboard = [
            [
                InlineKeyboardButton("📞 Contact", callback_data="contact"),
                InlineKeyboardButton("💼 Nos Services", callback_data="services"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = data.get("welcome_text", "👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :")
        welcome_photo = data.get("welcome_photo")
        
        if welcome_photo:
            # Si on a une photo d'accueil, on doit d'abord supprimer l'ancien message et en créer un nouveau
            try:
                await query.edit_message_media(
                    media=InputMediaPhoto(media=welcome_photo, caption=welcome_text),
                    reply_markup=reply_markup
                )
            except:
                # Si ça ne marche pas, on utilise edit_message_text
                await query.edit_message_text(
                    f"{welcome_text}\n\n🖼️ *Photo d'accueil disponible*",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
        else:
            await query.edit_message_text(
                welcome_text,
                reply_markup=reply_markup,
            )
    else:
        content = data.get(query.data, "Texte non défini.")
        keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Toujours utiliser edit_message_text pour les callbacks normaux
        await query.edit_message_text(text=content, reply_markup=reply_markup)


# --- Commande /admin ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Supprimer l'ancien message s'il existe
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
        except:
            pass
    
    await update.message.reply_text("🔐 Entrez le mot de passe admin :")
    context.user_data["awaiting_password"] = True


# --- Gestion du mot de passe ---
async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_password"):
        if update.message.text == ADMIN_PASSWORD:
            admins.add(update.message.from_user.id)
            context.user_data["awaiting_password"] = False
            # Créer le panneau admin avec des boutons callback
            keyboard = [
                [
                    InlineKeyboardButton("✏️ Modifier Contact", callback_data="admin_edit_contact"),
                    InlineKeyboardButton("✏️ Modifier Services", callback_data="admin_edit_services")
                ],
                [InlineKeyboardButton("🖼️ Panel Admin Photo", callback_data="admin_photo_panel")],
                [InlineKeyboardButton("📢 Message", callback_data="admin_message_panel")],
                [InlineKeyboardButton("🚪 Quitter admin", callback_data="admin_quit")]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("⚙️ Panneau Admin :", reply_markup=markup)
        else:
            await update.message.reply_text("❌ Mot de passe incorrect.")
        return True
    return False


# --- Gestion des callbacks admin ---
async def handle_admin_callback(query, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    if user_id not in admins:
        await query.edit_message_text("❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
        return
    
    if query.data == "admin_edit_contact":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "✏️ **Modification du Contact**\n\n"
            "Envoie le nouveau texte pour *Contact* :\n\n"
            f"*Texte actuel :*\n{data.get('contact', 'Aucun texte défini')}",
            parse_mode="Markdown",
            reply_markup=markup
        )
        context.user_data["editing"] = "contact"
    elif query.data == "admin_edit_services":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "✏️ **Modification des Services**\n\n"
            "Envoie le nouveau texte pour *Services* :\n\n"
            f"*Texte actuel :*\n{data.get('services', 'Aucun texte défini')}",
            parse_mode="Markdown",
            reply_markup=markup
        )
        context.user_data["editing"] = "services"
    elif query.data == "admin_photo_panel":
        keyboard = [
            [InlineKeyboardButton("✏️ Modifier Texte d'accueil", callback_data="admin_edit_welcome_text")],
            [InlineKeyboardButton("🖼️ Modifier Photo d'accueil", callback_data="admin_edit_welcome_photo")],
            [InlineKeyboardButton("🗑️ Supprimer Photo d'accueil", callback_data="admin_delete_welcome_photo")],
            [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        current_photo = data.get("welcome_photo")
        photo_status = "✅ Photo définie" if current_photo else "❌ Aucune photo"
        await query.edit_message_text(
            f"🖼️ **Panel Admin Photo**\n\n"
            f"*Texte d'accueil actuel :*\n{data.get('welcome_text', 'Aucun texte défini')}\n\n"
            f"*Photo d'accueil :* {photo_status}",
            parse_mode="Markdown",
            reply_markup=markup
        )
    elif query.data == "admin_edit_welcome_text":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panel photo", callback_data="admin_photo_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "✏️ **Modification du Texte d'accueil**\n\n"
            "Envoie le nouveau texte pour l'accueil :\n\n"
            f"*Texte actuel :*\n{data.get('welcome_text', 'Aucun texte défini')}",
            parse_mode="Markdown",
            reply_markup=markup
        )
        context.user_data["editing"] = "welcome_text"
    elif query.data == "admin_edit_welcome_photo":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panel photo", callback_data="admin_photo_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🖼️ **Modification de la Photo d'accueil**\n\n"
            "Envoie la nouvelle photo pour l'accueil :\n\n"
            "*Note :* Envoie une image en tant que photo (pas en tant que fichier)",
            parse_mode="Markdown",
            reply_markup=markup
        )
        context.user_data["editing"] = "welcome_photo"
    elif query.data == "admin_delete_welcome_photo":
        data["welcome_photo"] = None
        save_data(data)
        keyboard = [
            [InlineKeyboardButton("✏️ Modifier Texte d'accueil", callback_data="admin_edit_welcome_text")],
            [InlineKeyboardButton("🖼️ Modifier Photo d'accueil", callback_data="admin_edit_welcome_photo")],
            [InlineKeyboardButton("🗑️ Supprimer Photo d'accueil", callback_data="admin_delete_welcome_photo")],
            [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "✅ **Photo d'accueil supprimée !**\n\n"
            f"*Texte d'accueil actuel :*\n{data.get('welcome_text', 'Aucun texte défini')}\n\n"
            f"*Photo d'accueil :* ❌ Aucune photo",
            parse_mode="Markdown",
            reply_markup=markup
        )
    elif query.data == "admin_message_panel":
        users_data = load_users()
        total_users = len(users_data["users"])
        total_messages = len(users_data["messages"])
        
        keyboard = [
            [InlineKeyboardButton("📤 Envoyer Message à tous", callback_data="admin_broadcast_message")],
            [InlineKeyboardButton("🗑️ Supprimer tous les messages", callback_data="admin_clear_messages")],
            [InlineKeyboardButton("📊 Voir les messages reçus", callback_data="admin_view_messages")],
            [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📢 **Panel Message**\n\n"
            f"*Utilisateurs enregistrés :* {total_users}\n"
            f"*Messages reçus :* {total_messages}\n\n"
            "Choisissez une action :",
            parse_mode="Markdown",
            reply_markup=markup
        )
    elif query.data == "admin_broadcast_message":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panel message", callback_data="admin_message_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📤 **Envoi de message à tous les utilisateurs**\n\n"
            "Envoie le message que tu veux diffuser à tous les utilisateurs :",
            parse_mode="Markdown",
            reply_markup=markup
        )
        context.user_data["editing"] = "broadcast_message"
    elif query.data == "admin_clear_messages":
        # Afficher un message de traitement
        await query.edit_message_text(
            "🗑️ **Suppression en cours...**\n\n"
            "Suppression de tous les messages du bot avec les utilisateurs...\n"
            "Cela peut prendre quelques instants.",
            parse_mode="Markdown"
        )
        
        # Supprimer les messages stockés
        users_data = load_users()
        users_data["messages"] = []
        save_users(users_data)
        
        # Supprimer les messages du bot avec les utilisateurs
        deleted_count = await clear_all_bot_messages(context)
        
        keyboard = [
            [InlineKeyboardButton("📤 Envoyer Message à tous", callback_data="admin_broadcast_message")],
            [InlineKeyboardButton("🗑️ Supprimer tous les messages", callback_data="admin_clear_messages")],
            [InlineKeyboardButton("📊 Voir les messages reçus", callback_data="admin_view_messages")],
            [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"✅ **Suppression terminée !**\n\n"
            f"*Messages supprimés :* {deleted_count}\n"
            f"*Messages stockés supprimés :* Tous\n\n"
            "📢 **Panel Message**\n\n"
            f"*Utilisateurs enregistrés :* {len(users_data['users'])}\n"
            f"*Messages reçus :* 0\n\n"
            "Choisissez une action :",
            parse_mode="Markdown",
            reply_markup=markup
        )
    elif query.data == "admin_view_messages":
        users_data = load_users()
        messages = users_data["messages"]
        
        if not messages:
            keyboard = [[InlineKeyboardButton("🔙 Retour au panel message", callback_data="admin_message_panel")]]
            markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📊 **Messages reçus**\n\n"
                "Aucun message reçu pour le moment.",
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            # Afficher les 10 derniers messages
            recent_messages = messages[-10:]
            message_text = "📊 **Messages reçus** (10 derniers)\n\n"
            
            for i, msg in enumerate(recent_messages, 1):
                username = f"@{msg['username']}" if msg['username'] else "Sans username"
                name = f"{msg['first_name']} {msg['last_name']}".strip()
                message_text += f"**{i}.** {name} ({username})\n"
                message_text += f"ID: `{msg['user_id']}`\n"
                message_text += f"Message: {msg['message'][:100]}{'...' if len(msg['message']) > 100 else ''}\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Retour au panel message", callback_data="admin_message_panel")]]
            markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                message_text,
                parse_mode="Markdown",
                reply_markup=markup
            )
    elif query.data == "admin_panel":
        keyboard = [
            [
                InlineKeyboardButton("✏️ Modifier Contact", callback_data="admin_edit_contact"),
                InlineKeyboardButton("✏️ Modifier Services", callback_data="admin_edit_services")
            ],
            [InlineKeyboardButton("🖼️ Panel Admin Photo", callback_data="admin_photo_panel")],
            [InlineKeyboardButton("📢 Message", callback_data="admin_message_panel")],
            [InlineKeyboardButton("🚪 Quitter admin", callback_data="admin_quit")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚙️ Panneau Admin :", reply_markup=markup)
    elif query.data == "admin_quit":
        admins.discard(user_id)
        context.user_data.clear()
        keyboard = [
            [
                InlineKeyboardButton("📞 Contact", callback_data="contact"),
                InlineKeyboardButton("💼 Nos Services", callback_data="services"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "✅ Déconnecté du mode admin.\n\n👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :",
            reply_markup=reply_markup,
        )


# --- Gestion des actions admin (texte) ---
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in admins:
        return

    # Enregistrement d'une modification
    section = context.user_data.get("editing")
    if section:
        if section == "welcome_photo":
            # Gestion de la photo d'accueil
            if update.message.photo:
                # Prendre la photo de plus haute qualité
                photo = update.message.photo[-1]
                data["welcome_photo"] = photo.file_id
                save_data(data)
                context.user_data["editing"] = None
                
                # Retour au panel photo
                keyboard = [
                    [InlineKeyboardButton("✏️ Modifier Texte d'accueil", callback_data="admin_edit_welcome_text")],
                    [InlineKeyboardButton("🖼️ Modifier Photo d'accueil", callback_data="admin_edit_welcome_photo")],
                    [InlineKeyboardButton("🗑️ Supprimer Photo d'accueil", callback_data="admin_delete_welcome_photo")],
                    [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
                ]
                markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "✅ Photo d'accueil mise à jour !\n\n🖼️ Panel Admin Photo :",
                    reply_markup=markup
                )
            else:
                await update.message.reply_text("❌ Veuillez envoyer une photo (pas un fichier).")
        elif section == "broadcast_message":
            # Envoi du message à tous les utilisateurs
            users_data = load_users()
            users = users_data["users"]
            message_text = update.message.text
            context.user_data["editing"] = None
            
            sent_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    await context.bot.send_message(
                        chat_id=user["user_id"],
                        text=message_text
                    )
                    sent_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"Erreur envoi à {user['user_id']}: {e}")
            
            # Retour au panel message
            keyboard = [
                [InlineKeyboardButton("📤 Envoyer Message à tous", callback_data="admin_broadcast_message")],
                [InlineKeyboardButton("🗑️ Supprimer tous les messages", callback_data="admin_clear_messages")],
                [InlineKeyboardButton("📊 Voir les messages reçus", callback_data="admin_view_messages")],
                [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"✅ **Message diffusé !**\n\n"
                f"*Envoyé à :* {sent_count} utilisateurs\n"
                f"*Échecs :* {failed_count} utilisateurs\n\n"
                "📢 **Panel Message**",
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            # Gestion du texte (contact, services, welcome_text)
            data[section] = update.message.text
            save_data(data)
            context.user_data["editing"] = None
            
            if section == "welcome_text":
                # Retour au panel photo
                keyboard = [
                    [InlineKeyboardButton("✏️ Modifier Texte d'accueil", callback_data="admin_edit_welcome_text")],
                    [InlineKeyboardButton("🖼️ Modifier Photo d'accueil", callback_data="admin_edit_welcome_photo")],
                    [InlineKeyboardButton("🗑️ Supprimer Photo d'accueil", callback_data="admin_delete_welcome_photo")],
                    [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
                ]
                markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ Texte d'accueil mis à jour !\n\n🖼️ Panel Admin Photo :",
                    reply_markup=markup
                )
            else:
                # Retour au menu admin principal
                keyboard = [
                    [
                        InlineKeyboardButton("✏️ Modifier Contact", callback_data="admin_edit_contact"),
                        InlineKeyboardButton("✏️ Modifier Services", callback_data="admin_edit_services")
                    ],
                    [InlineKeyboardButton("🖼️ Panel Admin Photo", callback_data="admin_photo_panel")],
                    [InlineKeyboardButton("📢 Message", callback_data="admin_message_panel")],
                    [InlineKeyboardButton("🚪 Quitter admin", callback_data="admin_quit")]
                ]
                markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ Texte '{section}' mis à jour !\n\n⚙️ Panneau Admin :",
                    reply_markup=markup
                )
    else:
        await update.message.reply_text("Commande non reconnue.")


# --- Gestion du texte et des photos (mot de passe ou actions admin) ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_password(update, context):
        return
    
    # Si c'est un admin, gérer les actions admin
    if update.message.from_user.id in admins:
        await admin_actions(update, context)
        return
    
    # Si c'est un utilisateur normal, enregistrer son message
    user = update.effective_user
    add_message(
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        update.message.text,
        str(update.effective_message.date)
    )
    
    # Envoyer confirmation à l'utilisateur
    await update.message.reply_text(
        "✅ Votre message a été envoyé ! Nous vous répondrons bientôt."
    )

# --- Gestion des photos ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in admins:
        return
    
    section = context.user_data.get("editing")
    if section == "welcome_photo":
        # Prendre la photo de plus haute qualité
        photo = update.message.photo[-1]
        data["welcome_photo"] = photo.file_id
        save_data(data)
        context.user_data["editing"] = None
        
        # Retour au panel photo
        keyboard = [
            [InlineKeyboardButton("✏️ Modifier Texte d'accueil", callback_data="admin_edit_welcome_text")],
            [InlineKeyboardButton("🖼️ Modifier Photo d'accueil", callback_data="admin_edit_welcome_photo")],
            [InlineKeyboardButton("🗑️ Supprimer Photo d'accueil", callback_data="admin_delete_welcome_photo")],
            [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "✅ Photo d'accueil mise à jour !\n\n🖼️ Panel Admin Photo :",
            reply_markup=markup
        )


# --- Fonction principale ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot en marche...")
    app.run_polling()


if __name__ == "__main__":
    main()