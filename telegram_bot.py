import json
import os
import asyncio
from datetime import datetime
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

async def notify_admin_contact(context, user, message_text):
    """Notifie l'admin d'un nouveau message de contact"""
    try:
        # Récupérer l'ID de l'admin (premier admin connecté)
        admin_id = list(admins)[0] if admins else None
        
        if admin_id:
            # Créer le message de notification
            username = f"@{user.username}" if user.username else "Pas de @username"
            name = f"{user.first_name} {user.last_name}".strip()
            
            notification_text = (
                f"🔔 **Nouveau message de contact !**\n\n"
                f"**👤 De :** {name}\n"
                f"**📱 @username :** {username}\n"
                f"**🆔 ID :** `{user.id}`\n\n"
                f"**💬 Message :**\n{message_text}"
            )
            
            # Envoyer la notification à l'admin
            await context.bot.send_message(
                chat_id=admin_id,
                text=notification_text,
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Erreur lors de la notification admin: {e}")

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
                # Récupérer les messages récents (limité à 200 pour supprimer plus de messages)
                message_ids = []
                async for message in context.bot.iter_history(chat_id, limit=200):
                    if message.from_user and message.from_user.id == context.bot.id:
                        # Supprimer TOUS les messages du bot
                        message_ids.append(message.message_id)
                
                # Supprimer les messages par lots pour éviter les limites de rate
                # Supprimer du plus récent au plus ancien pour éviter les conflits
                for message_id in reversed(message_ids):
                    try:
                        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                        deleted_count += 1
                        # Petite pause pour éviter les limites de rate
                        await asyncio.sleep(0.02)
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

# --- Système de rôles ---
ROLES = {
    "CHEF": 3,      # Niveau le plus haut - peut tout faire
    "ADMIN": 2,      # Peut gérer le bot mais pas supprimer d'autres admins
    "STAFF": 1       # Niveau basique
}

def load_admins():
    """Charger la liste des administrateurs depuis le fichier"""
    try:
        with open("admins.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_admins(admins_data):
    """Sauvegarder la liste des administrateurs"""
    with open("admins.json", "w", encoding="utf-8") as f:
        json.dump(admins_data, f, ensure_ascii=False, indent=2)

def get_user_role(user_id):
    """Obtenir le rôle d'un utilisateur"""
    admins_data = load_admins()
    return admins_data.get(str(user_id), {}).get("role", "STAFF")

def has_permission(user_id, required_role):
    """Vérifier si un utilisateur a la permission requise"""
    user_role = get_user_role(user_id)
    return ROLES.get(user_role, 0) >= ROLES.get(required_role, 0)

def is_chef(user_id):
    """Vérifier si l'utilisateur est chef"""
    return has_permission(user_id, "CHEF")

def is_admin_or_higher(user_id):
    """Vérifier si l'utilisateur est admin ou plus"""
    return has_permission(user_id, "ADMIN")

async def update_message_display(query, context):
    """Mettre à jour l'affichage des messages avec les sélections"""
    users_data = load_users()
    messages = users_data.get("messages", [])
    recent_messages = messages[-10:]
    selected_messages = context.user_data.get("selected_messages", [])
    
    if recent_messages:
        message_text = "📊 **Messages reçus (10 derniers)**\n\n"
        for i, msg in enumerate(recent_messages, 1):
            name = f"{msg['first_name']} {msg['last_name']}".strip()
            username = f"@{msg['username']}" if msg['username'] else "Sans @username"
            
            # Indicateur de sélection
            selection_indicator = "✅" if (i-1) in selected_messages else "☐"
            
            message_text += f"{selection_indicator} **{i}.** Message envoyé par {name} [{msg['user_id']}]\n"
            message_text += f"#{msg['user_id']}\n"
            message_text += f"• {username}\n"
            message_text += f"Message: {msg['message'][:100]}{'...' if len(msg['message']) > 100 else ''}\n\n"
        
        # Créer des boutons pour chaque message
        keyboard = []
        for i, msg in enumerate(recent_messages, 1):
            name = f"{msg['first_name']} {msg['last_name']}".strip()
            # Bouton de sélection + bouton profil
            selection_text = "❌ Désélectionner" if (i-1) in selected_messages else f"☑️ Sélectionner {i}"
            keyboard.append([
                InlineKeyboardButton(selection_text, callback_data=f"select_msg_{i}"),
                InlineKeyboardButton(f"👤 Profil {name}", url=f"tg://user?id={msg['user_id']}")
            ])
        
        # Boutons d'action
        action_buttons = []
        if selected_messages:
            action_buttons.append(InlineKeyboardButton(f"🗑️ Supprimer ({len(selected_messages)})", callback_data="delete_selected_messages"))
        
        if len(selected_messages) < len(recent_messages):
            action_buttons.append(InlineKeyboardButton("✅ Tout sélectionner", callback_data="select_all_messages"))
        
        if action_buttons:
            keyboard.append(action_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 Retour au panel message", callback_data="admin_message_panel")])
        markup = InlineKeyboardMarkup(keyboard)
        
        await safe_edit_message(
            query,
            message_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        # Aucun message
        keyboard = [[InlineKeyboardButton("🔙 Retour au panel message", callback_data="admin_message_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "📊 **Messages reçus**\n\nAucun message reçu pour le moment.",
            reply_markup=markup,
            parse_mode="Markdown"
        )

# --- Fonction pour forcer la suppression de tous les messages du bot ---
async def force_delete_all_bot_messages(context, chat_id):
    """Force la suppression de tous les messages du bot dans un chat"""
    try:
        # Première passe : supprimer les messages récents
        message_ids = []
        async for message in context.bot.iter_history(chat_id, limit=200):
            if message.from_user and message.from_user.id == context.bot.id:
                message_ids.append(message.message_id)
        
        # Supprimer du plus récent au plus ancien
        for message_id in reversed(message_ids):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                await asyncio.sleep(0.01)
            except:
                continue
                
        # Deuxième passe : essayer de supprimer plus de messages
        await asyncio.sleep(0.5)
        message_ids = []
        async for message in context.bot.iter_history(chat_id, limit=500):
            if message.from_user and message.from_user.id == context.bot.id:
                message_ids.append(message.message_id)
        
        for message_id in reversed(message_ids):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                await asyncio.sleep(0.005)
            except:
                continue
                
        # Troisième passe : dernière tentative
        await asyncio.sleep(0.5)
        message_ids = []
        async for message in context.bot.iter_history(chat_id, limit=1000):
            if message.from_user and message.from_user.id == context.bot.id:
                message_ids.append(message.message_id)
        
        for message_id in reversed(message_ids):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                await asyncio.sleep(0.002)
            except:
                continue
    except:
        pass

# --- Fonction pour notifier l'admin des messages de contact ---
async def notify_admin_contact(context, user, message_text):
    """Notifie l'admin d'un nouveau message de contact"""
    try:
        # Récupérer l'ID admin (premier admin connecté)
        admin_id = list(admins)[0] if admins else None
        if not admin_id:
            return
        
        # Formater le message pour l'admin
        username = f"@{user.username}" if user.username else "Pas de @username"
        name = f"{user.first_name} {user.last_name}".strip() if user.last_name else user.first_name
        
        # Créer le message avec profil Telegram
        admin_message = (
            f"Message envoyé par {name} [{user.id}]\n"
            f"#{user.id}\n"
            f"• Pour répondre, répondez à ce message.\n\n"
            f"💬 **Message :**\n{message_text}"
        )
        
        # Créer un clavier avec bouton pour voir le profil
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton(f"👤 Voir le profil de {name}", url=f"tg://user?id={user.id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Envoyer le message à l'admin avec bouton de réponse
        await context.bot.send_message(
            chat_id=admin_id,
            text=admin_message,
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Erreur lors de la notification admin: {e}")

# --- Fonction utilitaire pour l'édition sécurisée de messages ---
async def safe_edit_message(query, text, reply_markup=None, parse_mode=None):
    """Édite un message de manière sécurisée avec gestion d'erreurs"""
    try:
        # Vérifier si le message a du texte à éditer
        if not query.message.text and not query.message.caption:
            # Si le message n'a pas de texte, envoyer un nouveau message
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    except Exception as e:
        # Si l'édition échoue, envoyer un nouveau message
        try:
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e2:
            print(f"Erreur lors de l'envoi du message: {e2}")
            await query.answer("❌ Erreur lors de l'affichage du contenu")

async def safe_edit_message_media(query, media, reply_markup=None):
    """Édite un message média de manière sécurisée avec gestion d'erreurs"""
    try:
        await query.edit_message_media(
            media=media,
            reply_markup=reply_markup
        )
    except Exception as e:
        # Si l'édition du média échoue, essayer d'éditer le texte
        try:
            caption = media.caption if hasattr(media, 'caption') else ""
            await safe_edit_message(
                query,
                text=f"{caption}\n\n🖼️ *Média disponible*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except Exception as e2:
            # Si tout échoue, envoyer un nouveau message
            try:
                if hasattr(media, 'media'):
                    await query.message.reply_photo(
                        photo=media.media,
                        caption=media.caption,
                        reply_markup=reply_markup
                    )
                else:
                    await query.message.reply_text(
                        text=f"{media.caption}\n\n🖼️ *Média disponible*",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
            except Exception as e3:
                print(f"Erreur lors de l'affichage du média: {e3}")
                await query.answer("❌ Erreur lors de l'affichage du contenu")


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
    
    # Supprimer tous les anciens messages du bot dans cette conversation
    await force_delete_all_bot_messages(context, user.id)
    
    # Attendre un peu pour s'assurer que la suppression est terminée
    await asyncio.sleep(1)
    
    keyboard = [
        [
            InlineKeyboardButton("📞 Contact", callback_data="contact"),
            InlineKeyboardButton("💼 Nos Services", callback_data="services"),
        ],
        [
            InlineKeyboardButton("💬 Nous contacter", callback_data="contact_us"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = data.get("welcome_text", "👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :")
    welcome_photo = data.get("welcome_photo")
    
    # Attendre un peu après la suppression
    await asyncio.sleep(0.5)
    
    # Essayer d'éditer le message de commande /start au lieu d'en créer un nouveau
    try:
        if welcome_photo:
            await update.message.reply_photo(
                photo=welcome_photo,
                caption=welcome_text,
                reply_markup=reply_markup,
            )
        else:
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=reply_markup,
            )
    except Exception as e:
        print(f"Erreur lors de l'affichage du menu: {e}")
        # En cas d'erreur, envoyer un message simple
        await update.message.reply_text(
            text=welcome_text,
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
            ],
            [
                InlineKeyboardButton("💬 Nous contacter", callback_data="contact_us"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = data.get("welcome_text", "👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :")
        welcome_photo = data.get("welcome_photo")
        
        if welcome_photo:
            # Si on a une photo d'accueil, essayer d'éditer le média
            try:
                await query.edit_message_media(
                    media=InputMediaPhoto(media=welcome_photo, caption=welcome_text),
                    reply_markup=reply_markup
                )
            except Exception as e:
                # Si l'édition du média échoue, essayer d'éditer le texte
                try:
                    await safe_edit_message(
                        query,
                        f"{welcome_text}\n\n🖼️ *Photo d'accueil disponible*",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                except Exception as e2:
                    # Si tout échoue, envoyer un nouveau message
                    try:
                        await query.message.reply_photo(
                            photo=welcome_photo,
                            caption=welcome_text,
                            reply_markup=reply_markup
                        )
                    except Exception as e3:
                        print(f"Erreur lors de l'affichage de la photo: {e3}")
                        await query.answer("Erreur lors de l'affichage du contenu")
        else:
            try:
                await safe_edit_message(
                    query,
                    welcome_text,
                    reply_markup=reply_markup
                )
            except Exception as e:
                # Si l'édition échoue, envoyer un nouveau message
                try:
                    await query.message.reply_text(
                        welcome_text,
                        reply_markup=reply_markup
                    )
                except Exception as e2:
                    print(f"Erreur lors de l'envoi du message: {e2}")
                    await query.answer("Erreur lors de l'affichage du contenu")
    elif query.data == "contact_us":
        # Menu pour contacter l'admin
        keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        content = ("💬 **Nous contacter**\n\n"
                  "Vous pouvez nous envoyer un message directement !\n\n"
                  "Écrivez votre message ci-dessous et nous vous répondrons rapidement.\n\n"
                  "📝 *Tapez votre message...*")
        
        # Vérifier s'il y a une photo d'accueil pour l'afficher avec le contenu
        welcome_photo = data.get("welcome_photo")
        
        if welcome_photo:
            # Si on a une photo d'accueil, essayer d'éditer le média
            try:
                await query.edit_message_media(
                    media=InputMediaPhoto(media=welcome_photo, caption=content),
                    reply_markup=reply_markup
                )
            except Exception as e:
                # Si l'édition du média échoue, essayer d'éditer le texte
                try:
                    await query.edit_message_text(
                        text=f"{content}\n\n🖼️ *Photo d'accueil disponible*",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                except Exception as e2:
                    # Si tout échoue, envoyer un nouveau message
                    try:
                        await query.message.reply_photo(
                            photo=welcome_photo,
                            caption=content,
                            reply_markup=reply_markup
                        )
                    except Exception as e3:
                        print(f"Erreur lors de l'affichage de la photo: {e3}")
                        await query.answer("Erreur lors de l'affichage du contenu")
        else:
            # Pas de photo, éditer le texte normalement
            try:
                await query.edit_message_text(text=content, reply_markup=reply_markup, parse_mode="Markdown")
            except Exception as e:
                # Si l'édition échoue, envoyer un nouveau message
                try:
                    await query.message.reply_text(text=content, reply_markup=reply_markup, parse_mode="Markdown")
                except Exception as e2:
                    print(f"Erreur lors de l'envoi du message: {e2}")
                    await query.answer("Erreur lors de l'affichage du contenu")
        
        # Marquer l'utilisateur comme en mode contact
        context.user_data["contact_mode"] = True
        
    else:
        content = data.get(query.data, "Texte non défini.")
        keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Vérifier s'il y a une photo d'accueil pour l'afficher avec le contenu
        welcome_photo = data.get("welcome_photo")
        
        if welcome_photo:
            # Si on a une photo d'accueil, essayer d'éditer le média
            try:
                await query.edit_message_media(
                    media=InputMediaPhoto(media=welcome_photo, caption=content),
                    reply_markup=reply_markup
                )
            except Exception as e:
                # Si l'édition du média échoue, essayer d'éditer le texte
                try:
                    await query.edit_message_text(
                        text=f"{content}\n\n🖼️ *Photo d'accueil disponible*",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                except Exception as e2:
                    # Si tout échoue, envoyer un nouveau message
                    try:
                        await query.message.reply_photo(
                            photo=welcome_photo,
                            caption=content,
                            reply_markup=reply_markup
                        )
                    except Exception as e3:
                        print(f"Erreur lors de l'affichage de la photo: {e3}")
                        await query.answer("Erreur lors de l'affichage du contenu")
        else:
            # Pas de photo, éditer le texte normalement
            try:
                await query.edit_message_text(text=content, reply_markup=reply_markup)
            except Exception as e:
                # Si l'édition échoue, envoyer un nouveau message
                try:
                    await query.message.reply_text(text=content, reply_markup=reply_markup)
                except Exception as e2:
                    print(f"Erreur lors de l'envoi du message: {e2}")
                    await query.answer("Erreur lors de l'affichage du contenu")


# --- Commande /répondre ---
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande pour répondre à un utilisateur"""
    # Vérifier si c'est un admin
    if update.message.from_user.id not in admins:
        await update.message.reply_text("❌ Cette commande est réservée aux administrateurs.")
        return
    
    # Vérifier la syntaxe : /répondre <user_id> <message>
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📝 **Utilisation :** `/répondre <user_id> <message>`\n\n"
            "**Exemple :** `/répondre 123456789 Bonjour ! Comment puis-je vous aider ?`",
            parse_mode="Markdown"
        )
        return
    
    try:
        user_id = int(context.args[0])
        message_text = " ".join(context.args[1:])
        
        # Envoyer le message à l'utilisateur
        await context.bot.send_message(
            chat_id=user_id,
            text=f"💬 **Réponse de l'admin :**\n\n{message_text}",
            parse_mode="Markdown"
        )
        
        # Confirmer à l'admin
        await update.message.reply_text(f"✅ Message envoyé à l'utilisateur {user_id}")
        
    except ValueError:
        await update.message.reply_text("❌ L'ID utilisateur doit être un nombre.")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de l'envoi : {e}")


# --- Commande /admin ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Supprimer l'ancien message s'il existe
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
        except:
            pass
    
    # Supprimer tous les anciens messages du bot dans cette conversation
    user_id = update.effective_user.id
    await force_delete_all_bot_messages(context, user_id)
    
    # Attendre un peu pour s'assurer que la suppression est terminée
    await asyncio.sleep(0.5)
    
    await update.message.reply_text("🔐 Entrez le mot de passe admin :")
    context.user_data["awaiting_password"] = True


# --- Gestion du mot de passe ---
async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_password"):
        if update.message.text == ADMIN_PASSWORD:
            user_id = update.message.from_user.id
            admins.add(user_id)
            context.user_data["awaiting_password"] = False
            
            # Vérifier si c'est le premier admin (chef)
            admins_data = load_admins()
            if not admins_data:
                # Premier admin = Chef
                admins_data[str(user_id)] = {
                    "role": "CHEF",
                    "username": update.message.from_user.username,
                    "name": f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip(),
                    "added_by": "system",
                    "added_date": str(datetime.now())
                }
                save_admins(admins_data)
                await update.message.reply_text("✅ Connexion admin réussie ! Vous êtes maintenant le Chef.")
            else:
                await update.message.reply_text("✅ Connexion admin réussie !")
            
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
        try:
            await safe_edit_message(query, "❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
        except:
            await query.answer("❌ Accès refusé")
        return
    
    # Gestion d'erreurs globale pour les callbacks admin
    try:
        await handle_admin_callback_internal(query, context)
    except Exception as e:
        print(f"Erreur dans handle_admin_callback: {e}")
        try:
            await query.answer("❌ Erreur lors du traitement de la requête")
        except:
            pass

async def handle_admin_callback_internal(query, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    
    if query.data == "admin_edit_contact":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "✏️ **Modification du Contact**\n\n"
            "Envoie le nouveau texte pour *Contact* :\n\n"
            f"*Texte actuel :*\n{data.get('contact', 'Aucun texte défini')}",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        context.user_data["editing"] = "contact"
    elif query.data == "admin_edit_services":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "✏️ **Modification des Services**\n\n"
            "Envoie le nouveau texte pour *Services* :\n\n"
            f"*Texte actuel :*\n{data.get('services', 'Aucun texte défini')}",
            reply_markup=markup,
            parse_mode="Markdown"
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
        await safe_edit_message(
            query,
            f"🖼️ **Panel Admin Photo**\n\n"
            f"*Texte d'accueil actuel :*\n{data.get('welcome_text', 'Aucun texte défini')}\n\n"
            f"*Photo d'accueil :* {photo_status}",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    elif query.data == "admin_edit_welcome_text":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panel photo", callback_data="admin_photo_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "✏️ **Modification du Texte d'accueil**\n\n"
            "Envoie le nouveau texte pour l'accueil :\n\n"
            f"*Texte actuel :*\n{data.get('welcome_text', 'Aucun texte défini')}",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        context.user_data["editing"] = "welcome_text"
    elif query.data == "admin_edit_welcome_photo":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panel photo", callback_data="admin_photo_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "🖼️ **Modification de la Photo d'accueil**\n\n"
            "Envoie la nouvelle photo pour l'accueil :\n\n"
            "*Note :* Envoie une image en tant que photo (pas en tant que fichier)",
            reply_markup=markup,
            parse_mode="Markdown"
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
        await safe_edit_message(
            query,
            "✅ **Photo d'accueil supprimée !**\n\n"
            f"*Texte d'accueil actuel :*\n{data.get('welcome_text', 'Aucun texte défini')}\n\n"
            f"*Photo d'accueil :* ❌ Aucune photo",
            reply_markup=markup,
            parse_mode="Markdown"
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
        await safe_edit_message(
            query,
            f"📢 **Panel Message**\n\n"
            f"*Utilisateurs enregistrés :* {total_users}\n"
            f"*Messages reçus :* {total_messages}\n\n"
            "Choisissez une action :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    elif query.data == "admin_broadcast_message":
        keyboard = [[InlineKeyboardButton("🔙 Retour au panel message", callback_data="admin_message_panel")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "📤 **Envoi de message à tous les utilisateurs**\n\n"
            "Envoie le message que tu veux diffuser à tous les utilisateurs :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        context.user_data["editing"] = "broadcast_message"
    elif query.data == "admin_clear_messages":
        # Afficher un message de traitement
        await safe_edit_message(
            query,
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
        
        # Supprimer aussi les messages de confirmation et les callbacks
        # en supprimant les messages récents du bot dans tous les chats
        try:
            # Supprimer les messages du bot dans le chat admin actuel
            admin_chat_id = query.from_user.id
            await force_delete_all_bot_messages(context, admin_chat_id)
        except:
            pass
        
        keyboard = [
            [InlineKeyboardButton("📤 Envoyer Message à tous", callback_data="admin_broadcast_message")],
            [InlineKeyboardButton("🗑️ Supprimer tous les messages", callback_data="admin_clear_messages")],
            [InlineKeyboardButton("📊 Voir les messages reçus", callback_data="admin_view_messages")],
            [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        # Afficher le message de confirmation
        await safe_edit_message(
            query,
            f"✅ **Suppression terminée !**\n\n"
            f"*Messages supprimés :* {deleted_count}\n"
            f"*Messages stockés supprimés :* Tous\n\n"
            "📢 **Panel Message**\n\n"
            f"*Utilisateurs enregistrés :* {len(users_data['users'])}\n"
            f"*Messages reçus :* 0\n\n"
            "Choisissez une action :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
        # Supprimer le message de confirmation après 3 secondes
        try:
            await asyncio.sleep(3)
            await context.bot.delete_message(chat_id=query.from_user.id, message_id=query.message.message_id)
        except:
            pass
    elif query.data == "admin_view_messages":
        users_data = load_users()
        messages = users_data["messages"]
        
        if not messages:
            keyboard = [[InlineKeyboardButton("🔙 Retour au panel message", callback_data="admin_message_panel")]]
            markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                "📊 **Messages reçus**\n\n"
                "Aucun message reçu pour le moment.",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            # Afficher les 10 derniers messages
            recent_messages = messages[-10:]
            message_text = "📊 **Messages reçus** (10 derniers)\n\n"
            
            for i, msg in enumerate(recent_messages, 1):
                username = f"@{msg['username']}" if msg['username'] else "Sans @username"
                name = f"{msg['first_name']} {msg['last_name']}".strip()
                message_text += f"**{i}.** Message envoyé par {name} [{msg['user_id']}]\n"
                message_text += f"#{msg['user_id']}\n"
                message_text += f"• {username}\n"
                message_text += f"Message: {msg['message'][:100]}{'...' if len(msg['message']) > 100 else ''}\n\n"
            
            # Créer des boutons pour chaque message
            keyboard = []
            for i, msg in enumerate(recent_messages, 1):
                name = f"{msg['first_name']} {msg['last_name']}".strip()
                # Bouton de sélection + bouton profil
                keyboard.append([
                    InlineKeyboardButton(f"☑️ Sélectionner {i}", callback_data=f"select_msg_{i}"),
                    InlineKeyboardButton(f"👤 Profil {name}", url=f"tg://user?id={msg['user_id']}")
                ])
            
            keyboard.append([
                InlineKeyboardButton("🗑️ Supprimer sélectionnés", callback_data="delete_selected_messages"),
                InlineKeyboardButton("✅ Tout sélectionner", callback_data="select_all_messages")
            ])
            keyboard.append([InlineKeyboardButton("🔙 Retour au panel message", callback_data="admin_message_panel")])
            markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                message_text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
    
    
    elif query.data == "admin_panel":
        keyboard = [
            [
                InlineKeyboardButton("✏️ Modifier Contact", callback_data="admin_edit_contact"),
                InlineKeyboardButton("✏️ Modifier Services", callback_data="admin_edit_services")
            ],
            [InlineKeyboardButton("🖼️ Panel Admin Photo", callback_data="admin_photo_panel")],
            [InlineKeyboardButton("📢 Message", callback_data="admin_message_panel")],
            [InlineKeyboardButton("👥 Gestion Admins", callback_data="admin_manage_admins")],
            [InlineKeyboardButton("🚪 Quitter admin", callback_data="admin_quit")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, "⚙️ Panneau Admin :", reply_markup=markup)
    
    elif query.data == "admin_manage_admins":
        # Vérifier les permissions
        if not is_admin_or_higher(user_id):
            await query.answer("❌ Vous n'avez pas les permissions pour gérer les administrateurs.")
            return
        
        admins_data = load_admins()
        message_text = "👥 **Gestion des Administrateurs**\n\n"
        
        # Afficher la liste des admins
        if admins_data:
            for admin_id, admin_info in admins_data.items():
                role = admin_info.get("role", "STAFF")
                username = admin_info.get("username", "N/A")
                name = admin_info.get("name", "N/A")
                message_text += f"• **{name}** (@{username})\n"
                message_text += f"  ID: `{admin_id}` | Rôle: **{role}**\n\n"
        else:
            message_text += "Aucun administrateur enregistré.\n\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Ajouter Admin", callback_data="admin_add_admin")],
            [InlineKeyboardButton("❌ Supprimer Admin", callback_data="admin_remove_admin")],
            [InlineKeyboardButton("🔙 Retour au panel admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, message_text, reply_markup=markup, parse_mode="Markdown")
    
    elif query.data == "admin_add_admin":
        if not is_admin_or_higher(user_id):
            await query.answer("❌ Vous n'avez pas les permissions.")
            return
        
        context.user_data["adding_admin"] = True
        await safe_edit_message(
            query, 
            "➕ **Ajouter un Administrateur**\n\n"
            "Envoyez l'@username ou l'ID de l'utilisateur à ajouter :\n"
            "Exemple: `@username` ou `123456789`",
            parse_mode="Markdown"
        )
    
    elif query.data == "admin_remove_admin":
        if not is_chef(user_id):
            await query.answer("❌ Seul le Chef peut supprimer des administrateurs.")
            return
        
        context.user_data["removing_admin"] = True
        await safe_edit_message(
            query, 
            "❌ **Supprimer un Administrateur**\n\n"
            "Envoyez l'@username ou l'ID de l'utilisateur à supprimer :\n"
            "Exemple: `@username` ou `123456789`",
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("select_msg_"):
        # Gérer la sélection d'un message
        msg_index = int(query.data.split("_")[2]) - 1  # Convertir en index 0-based
        user_id = query.from_user.id
        
        if not is_admin_or_higher(user_id):
            await query.answer("❌ Vous n'avez pas les permissions.")
            return
        
        # Initialiser la liste des messages sélectionnés si elle n'existe pas
        if "selected_messages" not in context.user_data:
            context.user_data["selected_messages"] = []
        
        # Ajouter ou retirer le message de la sélection
        if msg_index in context.user_data["selected_messages"]:
            context.user_data["selected_messages"].remove(msg_index)
            await query.answer("❌ Message désélectionné")
        else:
            context.user_data["selected_messages"].append(msg_index)
            await query.answer("✅ Message sélectionné")
        
        # Mettre à jour l'affichage
        await update_message_display(query, context)
    
    elif query.data == "select_all_messages":
        # Sélectionner tous les messages
        user_id = query.from_user.id
        
        if not is_admin_or_higher(user_id):
            await query.answer("❌ Vous n'avez pas les permissions.")
            return
        
        users_data = load_users()
        messages = users_data.get("messages", [])
        recent_messages = messages[-10:]
        
        # Sélectionner tous les messages
        context.user_data["selected_messages"] = list(range(len(recent_messages)))
        await query.answer(f"✅ {len(recent_messages)} messages sélectionnés")
        
        # Mettre à jour l'affichage
        await update_message_display(query, context)
    
    elif query.data == "delete_selected_messages":
        # Supprimer les messages sélectionnés
        user_id = query.from_user.id
        
        if not is_admin_or_higher(user_id):
            await query.answer("❌ Vous n'avez pas les permissions.")
            return
        
        selected_messages = context.user_data.get("selected_messages", [])
        if not selected_messages:
            await query.answer("❌ Aucun message sélectionné")
            return
        
        # Charger les données
        users_data = load_users()
        messages = users_data.get("messages", [])
        recent_messages = messages[-10:]
        
        # Supprimer les messages sélectionnés (en ordre inverse pour éviter les problèmes d'index)
        deleted_count = 0
        for index in sorted(selected_messages, reverse=True):
            if 0 <= index < len(recent_messages):
                # Trouver l'index dans la liste complète
                full_index = len(messages) - 10 + index
                if 0 <= full_index < len(messages):
                    messages.pop(full_index)
                    deleted_count += 1
        
        # Sauvegarder les modifications
        users_data["messages"] = messages
        save_users(users_data)
        
        # Nettoyer la sélection
        context.user_data["selected_messages"] = []
        
        await query.answer(f"✅ {deleted_count} messages supprimés")
        
        # Mettre à jour l'affichage
        await update_message_display(query, context)
    
    elif query.data.startswith("role_"):
        # Gérer la sélection de rôle
        role = query.data.split("_")[1]
        user_id = query.from_user.id
        
        if not is_admin_or_higher(user_id):
            await query.answer("❌ Vous n'avez pas les permissions.")
            return
        
        if not context.user_data.get("choosing_role"):
            await query.answer("❌ Aucun administrateur en cours d'ajout.")
            return
        
        target_user_id = context.user_data.get("pending_admin_id")
        target_username = context.user_data.get("pending_admin_username")
        
        if not target_user_id:
            await query.answer("❌ Erreur: ID utilisateur manquant.")
            return
        
        # Ajouter l'administrateur
        admins_data = load_admins()
        admins_data[str(target_user_id)] = {
            "role": role,
            "username": target_username,
            "name": f"Utilisateur {target_user_id}",
            "added_by": user_id,
            "added_date": str(datetime.now())
        }
        save_admins(admins_data)
        
        # Nettoyer les données temporaires
        context.user_data.pop("choosing_role", None)
        context.user_data.pop("pending_admin_id", None)
        context.user_data.pop("pending_admin_username", None)
        
        await query.answer(f"✅ Administrateur ajouté avec le rôle {role}!")
        
        # Retourner au menu de gestion des admins
        await query.message.reply_text(
            f"✅ **Administrateur ajouté avec succès !**\n\n"
            f"ID: `{target_user_id}`\n"
            f"Username: @{target_username or 'N/A'}\n"
            f"Rôle: **{role}**",
            parse_mode="Markdown"
        )
    
    elif query.data == "admin_quit":
        user_id = query.from_user.id
        admins.discard(user_id)
        context.user_data.clear()
        keyboard = [
            [
                InlineKeyboardButton("📞 Contact", callback_data="contact"),
                InlineKeyboardButton("💼 Nos Services", callback_data="services"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "✅ Déconnecté du mode admin.\n\n👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :",
            reply_markup=reply_markup
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


# --- Gestion de l'ajout d'administrateur ---
async def handle_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gérer l'ajout d'un administrateur"""
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id
    
    # Vérifier les permissions
    if not is_admin_or_higher(user_id):
        await update.message.reply_text("❌ Vous n'avez pas les permissions.")
        return
    
    try:
        # Extraire l'ID utilisateur
        target_user_id = None
        target_username = None
        
        if user_input.startswith("@"):
            # C'est un @username
            target_username = user_input[1:]
            # Pour l'instant, on demande l'ID manuellement
            await update.message.reply_text(
                f"👤 Username détecté: @{target_username}\n\n"
                "Veuillez envoyer l'ID numérique de cet utilisateur :"
            )
            context.user_data["pending_username"] = target_username
            return
        else:
            # C'est un ID numérique
            target_user_id = int(user_input)
        
        # Si on a un username en attente, l'associer à l'ID
        if context.user_data.get("pending_username"):
            target_username = context.user_data["pending_username"]
            context.user_data.pop("pending_username", None)
        
        # Demander le rôle
        context.user_data["pending_admin_id"] = target_user_id
        context.user_data["pending_admin_username"] = target_username
        context.user_data["adding_admin"] = False
        context.user_data["choosing_role"] = True
        
        keyboard = [
            [InlineKeyboardButton("👑 Chef", callback_data="role_CHEF")],
            [InlineKeyboardButton("🛡️ Admin", callback_data="role_ADMIN")],
            [InlineKeyboardButton("👤 Staff", callback_data="role_STAFF")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👤 **Ajouter Administrateur**\n\n"
            f"ID: `{target_user_id}`\n"
            f"Username: @{target_username or 'N/A'}\n\n"
            f"Choisissez le rôle :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    except ValueError:
        await update.message.reply_text("❌ L'ID doit être un nombre valide.")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {e}")

# --- Gestion de la suppression d'administrateur ---
async def handle_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gérer la suppression d'un administrateur"""
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id
    
    # Vérifier les permissions (seul le chef peut supprimer)
    if not is_chef(user_id):
        await update.message.reply_text("❌ Seul le Chef peut supprimer des administrateurs.")
        return
    
    try:
        # Extraire l'ID utilisateur
        target_user_id = None
        
        if user_input.startswith("@"):
            # C'est un @username, on doit trouver l'ID
            target_username = user_input[1:]
            admins_data = load_admins()
            for admin_id, admin_info in admins_data.items():
                if admin_info.get("username") == target_username:
                    target_user_id = int(admin_id)
                    break
            
            if not target_user_id:
                await update.message.reply_text("❌ Utilisateur non trouvé dans la liste des administrateurs.")
                return
        else:
            # C'est un ID numérique
            target_user_id = int(user_input)
        
        # Vérifier que l'utilisateur existe dans la liste
        admins_data = load_admins()
        if str(target_user_id) not in admins_data:
            await update.message.reply_text("❌ Cet utilisateur n'est pas dans la liste des administrateurs.")
            return
        
        # Supprimer l'administrateur
        admin_info = admins_data.pop(str(target_user_id))
        save_admins(admins_data)
        
        # Retirer de la session active si connecté
        admins.discard(target_user_id)
        
        await update.message.reply_text(
            f"✅ Administrateur supprimé avec succès !\n\n"
            f"ID: `{target_user_id}`\n"
            f"Username: @{admin_info.get('username', 'N/A')}\n"
            f"Rôle: {admin_info.get('role', 'N/A')}",
            parse_mode="Markdown"
        )
        
        # Sortir du mode suppression
        context.user_data["removing_admin"] = False
        
    except ValueError:
        await update.message.reply_text("❌ L'ID doit être un nombre valide.")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {e}")

# --- Gestion du texte et des photos (mot de passe ou actions admin) ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_password(update, context):
        return
    
    # Si c'est un admin, gérer les actions admin
    if update.message.from_user.id in admins:
        # Gérer l'ajout d'administrateur
        if context.user_data.get("adding_admin"):
            await handle_add_admin(update, context)
            return
        
        # Gérer la suppression d'administrateur
        if context.user_data.get("removing_admin"):
            await handle_remove_admin(update, context)
            return
        
        await admin_actions(update, context)
        return
    
    # Vérifier si l'utilisateur est en mode contact
    if context.user_data.get("contact_mode"):
        # Enregistrer le message de contact
        user = update.effective_user
        message_text = update.message.text
        timestamp = str(update.effective_message.date)
        
        add_message(
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            message_text,
            timestamp
        )
        
        # Notifier l'admin du nouveau message de contact
        await notify_admin_contact(context, user, message_text)
        
        # Confirmer la réception du message
        await update.message.reply_text("✅ Message envoyé ! Nous vous répondrons bientôt.")
        
        # Désactiver le mode contact
        context.user_data["contact_mode"] = False
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
    app.add_handler(CommandHandler("repondre", reply_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot en marche...")
    app.run_polling()


if __name__ == "__main__":
    main()