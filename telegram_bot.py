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
    try:
        users_data = load_users()
        messages = users_data.get("messages", [])
        recent_messages = messages[-10:]
        selected_messages = context.user_data.get("selected_messages", [])
        
        print(f"DEBUG: selected_messages = {selected_messages}")
        print(f"DEBUG: recent_messages count = {len(recent_messages)}")
        
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
            
            try:
                await query.edit_message_text(
                    text=message_text,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
                print("DEBUG: Message édité avec succès")
            except Exception as e:
                print(f"Erreur lors de l'édition du message: {e}")
                await query.answer("Erreur lors de la mise à jour")
        else:
            # Aucun message
            keyboard = [[InlineKeyboardButton("🔙 Retour au panel message", callback_data="admin_message_panel")]]
            markup = InlineKeyboardMarkup(keyboard)
            try:
                await query.edit_message_text(
                    text="📊 **Messages reçus**\n\nAucun message reçu pour le moment.",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Erreur lors de l'édition du message: {e}")
                await query.answer("Erreur lors de la mise à jour")
    except Exception as e:
        print(f"Erreur dans update_message_display: {e}")
        await query.answer("Erreur lors de la mise à jour de l'affichage")

# --- Fonction pour forcer la suppression de tous les messages du bot ---
async def force_delete_all_bot_messages(context, chat_id):
    """Force la suppression de tous les messages du bot dans un chat"""
    deleted_count = 0
    try:
        print(f"DEBUG: force_delete_all_bot_messages pour chat_id {chat_id}")
        
        # Utiliser get_updates pour récupérer les messages
        message_ids = []
        try:
            # Récupérer les updates récents
            updates = await context.bot.get_updates(limit=100, timeout=10)
            print(f"DEBUG: Récupéré {len(updates)} updates")
            
            for update in updates:
                if update.message and update.message.chat_id == chat_id:
                    if update.message.from_user and update.message.from_user.id == context.bot.id:
                        message_ids.append(update.message.message_id)
                        print(f"DEBUG: Message du bot trouvé: {update.message.message_id}")
            
            print(f"DEBUG: Première passe - trouvé {len(message_ids)} messages du bot")
        except Exception as e:
            print(f"DEBUG: Erreur get_updates dans force_delete_all_bot_messages: {e}")
            return 0
        
        # Supprimer du plus récent au plus ancien
        for message_id in reversed(message_ids):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                deleted_count += 1
                print(f"DEBUG: Message {message_id} supprimé")
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"DEBUG: Erreur suppression message {message_id}: {e}")
                continue
                
        # Deuxième passe : essayer de récupérer plus d'updates
        await asyncio.sleep(1)
        message_ids = []
        try:
            # Récupérer plus d'updates avec un offset
            updates = await context.bot.get_updates(limit=200, timeout=10)
            print(f"DEBUG: Deuxième passe - récupéré {len(updates)} updates")
            
            for update in updates:
                if update.message and update.message.chat_id == chat_id:
                    if update.message.from_user and update.message.from_user.id == context.bot.id:
                        message_ids.append(update.message.message_id)
                        print(f"DEBUG: Message du bot trouvé (2ème passe): {update.message.message_id}")
            
            print(f"DEBUG: Deuxième passe - trouvé {len(message_ids)} messages du bot")
        except Exception as e:
            print(f"DEBUG: Erreur get_updates deuxième passe: {e}")
            return deleted_count
        
        for message_id in reversed(message_ids):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                deleted_count += 1
                print(f"DEBUG: Message {message_id} supprimé (deuxième passe)")
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"DEBUG: Erreur suppression message {message_id} (deuxième passe): {e}")
                continue
                
        print(f"DEBUG: force_delete_all_bot_messages terminé - {deleted_count} messages supprimés")
        return deleted_count
    except Exception as e:
        print(f"DEBUG: Erreur générale dans force_delete_all_bot_messages: {e}")
        return deleted_count

# --- Fonction pour notifier l'admin des messages de contact ---
async def notify_admin_contact(context, user, message_text, timestamp=None):
    """Notifie l'admin d'un nouveau message de contact"""
    try:
        # Récupérer l'ID admin (premier admin connecté)
        admin_id = list(admins)[0] if admins else None
        if not admin_id:
            return
        
        # Formater le message pour l'admin
        username = f"@{user.username}" if user.username else "Pas de @username"
        name = f"{user.first_name} {user.last_name}".strip() if user.last_name else user.first_name
        
        # Formater l'heure
        from datetime import datetime
        if timestamp:
            try:
                time_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = time_obj.strftime('%H:%M:%S')
            except:
                time_str = "Maintenant"
        else:
            time_str = "Maintenant"
        
        # Créer le message de notification avec emoji et formatage
        admin_message = (
            f"🔔 **NOUVEAU MESSAGE REÇU !**\n\n"
            f"👤 **De :** {name}\n"
            f"📱 **@username :** {username}\n"
            f"🆔 **ID :** `{user.id}`\n"
            f"⏰ **Heure :** {time_str}\n\n"
            f"💬 **Message :**\n{message_text}\n\n"
            f"📝 *Utilisez /repondre {user.id} <votre message> pour répondre*"
        )
        
        # Créer un clavier avec boutons d'action
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton(f"👤 Voir le profil de {name}", url=f"tg://user?id={user.id}")],
            [InlineKeyboardButton("📊 Voir tous les messages", callback_data="admin_view_messages")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Envoyer le message à l'admin avec notification
        await context.bot.send_message(
            chat_id=admin_id,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
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
    
    # Construire le clavier avec les menus du Service
    keyboard = []
    
    # Ajouter le bouton Contact
    keyboard.append([InlineKeyboardButton("📞 Contact", callback_data="contact")])
    
    # Ajouter les menus du Service
    services = data.get("services", [])
    if isinstance(services, str):
        services = []
    
    if services:
        # Ajouter chaque menu comme un bouton séparé
        for i, service in enumerate(services):
            keyboard.append([InlineKeyboardButton(service, callback_data=f"service_menu_{i}")])
    else:
        # Si pas de menus, garder le bouton Services par défaut
        keyboard.append([InlineKeyboardButton("💼 Nos Services", callback_data="services")])
    
    # Ajouter le bouton Nous contacter
    keyboard.append([InlineKeyboardButton("💬 Nous contacter", callback_data="contact_us")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = data.get("welcome_text", "👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :")
    welcome_photo = data.get("welcome_photo")
    
    # Vérifier s'il y a déjà un message principal à éditer
    main_message_id = context.user_data.get("main_message_id")
    
    if main_message_id:
        # Essayer d'éditer le message existant
        try:
            if welcome_photo:
                await context.bot.edit_message_media(
                    chat_id=user.id,
                    message_id=main_message_id,
                    media=InputMediaPhoto(media=welcome_photo, caption=welcome_text),
                    reply_markup=reply_markup
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=user.id,
                    message_id=main_message_id,
                    text=welcome_text,
                    reply_markup=reply_markup
                )
            return  # Succès, on sort de la fonction
        except Exception as e:
            print(f"Erreur lors de l'édition du message: {e}")
            # Si l'édition échoue, supprimer l'ancien message et continuer
            try:
                await context.bot.delete_message(chat_id=user.id, message_id=main_message_id)
            except:
                pass
            context.user_data.pop("main_message_id", None)  # Nettoyer l'ID invalide
    
    # Si pas de message existant ou édition échouée, envoyer un nouveau message
    try:
        if welcome_photo:
            sent_message = await update.message.reply_photo(
                photo=welcome_photo,
                caption=welcome_text,
                reply_markup=reply_markup,
            )
        else:
            sent_message = await update.message.reply_text(
                text=welcome_text,
                reply_markup=reply_markup,
            )
        
        # Stocker l'ID du message pour les prochaines éditions
        context.user_data["main_message_id"] = sent_message.message_id
        
    except Exception as e:
        print(f"Erreur lors de l'affichage du menu: {e}")
        # En cas d'erreur, envoyer un message simple
        sent_message = await update.message.reply_text(
            text=welcome_text,
            reply_markup=reply_markup,
        )
        context.user_data["main_message_id"] = sent_message.message_id


# --- Boutons ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    print(f"DEBUG: Callback reçu: {query.data}")
    
    # Gestion des callbacks admin
    if query.data.startswith("admin_"):
        print("DEBUG: Routage vers handle_admin_callback (admin_)")
        await handle_admin_callback(query, context)
        return
    
    # Gestion des callbacks de sélection de messages
    if query.data.startswith("select_msg_") or query.data == "select_all_messages" or query.data == "delete_selected_messages":
        print("DEBUG: Routage vers handle_admin_callback (sélection)")
        await handle_admin_callback(query, context)
        return
    
    # Gestion des callbacks des menus du Service
    if query.data.startswith("service_menu_"):
        # Gérer les menus du Service
        menu_index = int(query.data.split("_")[-1])
        data = load_data()
        services = data.get("services", [])
        
        # Si services est une chaîne, la convertir en liste
        if isinstance(services, str):
            services = []
        
        if 0 <= menu_index < len(services):
            # Afficher le contenu du menu sélectionné
            menu_content = services[menu_index]
            
            # Créer le clavier de retour
            keyboard = []
            
            # Ajouter le bouton Contact
            keyboard.append([InlineKeyboardButton("📞 Contact", callback_data="contact")])
            
            # Ajouter les menus du Service
            if services:
                for i, service in enumerate(services):
                    keyboard.append([InlineKeyboardButton(service, callback_data=f"service_menu_{i}")])
            else:
                keyboard.append([InlineKeyboardButton("💼 Nos Services", callback_data="services")])
            
            # Ajouter le bouton Nous contacter
            keyboard.append([InlineKeyboardButton("💬 Nous contacter", callback_data="contact_us")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text=menu_content,
                reply_markup=reply_markup
            )
        else:
            await query.answer("❌ Menu introuvable")
        return
    
    # Gestion des callbacks normaux
    if query.data == "back_to_main":
        # Construire le clavier avec les menus du Service
        keyboard = []
        
        # Ajouter le bouton Contact
        keyboard.append([InlineKeyboardButton("📞 Contact", callback_data="contact")])
        
        # Ajouter les menus du Service
        data = load_data()
        services = data.get("services", [])
        if isinstance(services, str):
            services = []
        
        if services:
            # Ajouter chaque menu comme un bouton séparé
            for i, service in enumerate(services):
                keyboard.append([InlineKeyboardButton(service, callback_data=f"service_menu_{i}")])
        else:
            # Si pas de menus, garder le bouton Services par défaut
            keyboard.append([InlineKeyboardButton("💼 Nos Services", callback_data="services")])
        
        # Ajouter le bouton Nous contacter
        keyboard.append([InlineKeyboardButton("💬 Nous contacter", callback_data="contact_us")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = data.get("welcome_text", "👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :")
        welcome_photo = data.get("welcome_photo")
        
        # Vérifier s'il y a déjà un message principal à éditer
        main_message_id = context.user_data.get("main_message_id")
        
        if main_message_id:
            # Essayer d'éditer le message existant
            try:
                if welcome_photo:
                    await context.bot.edit_message_media(
                        chat_id=query.from_user.id,
                        message_id=main_message_id,
                        media=InputMediaPhoto(media=welcome_photo, caption=welcome_text),
                        reply_markup=reply_markup
                    )
                else:
                    await context.bot.edit_message_text(
                        chat_id=query.from_user.id,
                        message_id=main_message_id,
                        text=welcome_text,
                        reply_markup=reply_markup
                    )
                return  # Succès, on sort de la fonction
            except Exception as e:
                print(f"Erreur lors de l'édition du message: {e}")
                # Si l'édition échoue, supprimer l'ancien message et continuer
                try:
                    await context.bot.delete_message(chat_id=query.from_user.id, message_id=main_message_id)
                except:
                    pass
                context.user_data.pop("main_message_id", None)  # Nettoyer l'ID invalide
        
        # Si pas de message existant ou édition échouée, envoyer un nouveau message
        try:
            if welcome_photo:
                sent_message = await query.message.reply_photo(
                    photo=welcome_photo,
                    caption=welcome_text,
                    reply_markup=reply_markup
                )
            else:
                sent_message = await query.message.reply_text(
                    text=welcome_text,
                    reply_markup=reply_markup
                )
            
            # Stocker l'ID du message pour les prochaines éditions
            context.user_data["main_message_id"] = sent_message.message_id
            
        except Exception as e:
            print(f"Erreur lors de l'affichage du menu principal: {e}")
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
                    InlineKeyboardButton("👥 Admin", callback_data="admin_manage_admins"),
                    InlineKeyboardButton("⚙️ Service", callback_data="admin_service")
                ],
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
    print(f"DEBUG: handle_admin_callback appelé avec query.data = {query.data}")
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
            [InlineKeyboardButton("🗑️ Supprimer messages reçus", callback_data="admin_clear_received_messages")],
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
    elif query.data == "admin_clear_received_messages":
        # Afficher un message de traitement
        await safe_edit_message(
            query,
            "🗑️ **Suppression en cours...**\n\n"
            "Suppression des messages reçus par le bot...\n"
            "Cela peut prendre quelques instants.",
            parse_mode="Markdown"
        )
        
        # Supprimer SEULEMENT les messages reçus par le bot (pas les menus)
        users_data = load_users()
        users_data["messages"] = []  # Vider la liste des messages reçus
        save_users(users_data)
        
        # Afficher le résultat
        await safe_edit_message(
            query,
            "✅ **Suppression terminée !**\n\n"
            "🗑️ Tous les messages reçus ont été supprimés\n\n"
            "Les menus du bot ont été conservés.",
            parse_mode="Markdown"
        )
        
        # Retourner au menu principal après 3 secondes
        await asyncio.sleep(3)
        
        # Afficher le menu principal
        users_data = load_users()
        keyboard = [
            [InlineKeyboardButton("📤 Envoyer Message à tous", callback_data="admin_broadcast_message")],
            [InlineKeyboardButton("🗑️ Supprimer messages reçus", callback_data="admin_clear_received_messages")],
            [InlineKeyboardButton("📊 Voir les messages reçus", callback_data="admin_view_messages")],
            [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        
        await safe_edit_message(
            query,
            "📢 **Panel Message**\n\n"
            f"*Utilisateurs enregistrés :* {len(users_data['users'])}\n"
            f"*Messages reçus :* {len(users_data.get('messages', []))}\n\n"
            "Choisissez une action :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    elif query.data == "admin_clear_received_messages":
        # Supprimer les messages reçus par le bot
        users_data = load_users()
        messages_count = len(users_data.get("messages", []))
        
        # Supprimer les messages stockés
        users_data["messages"] = []
        save_users(users_data)
        
        await safe_edit_message(
            query,
            f"✅ **Messages reçus supprimés !**\n\n"
            f"🗑️ {messages_count} messages reçus supprimés\n\n"
            "Les menus du bot ont été conservés.",
            parse_mode="Markdown"
        )
        
        # Retourner au menu principal après 3 secondes
        await asyncio.sleep(3)
        
        # Afficher le menu principal
        keyboard = [
            [InlineKeyboardButton("📤 Envoyer Message à tous", callback_data="admin_broadcast_message")],
            [InlineKeyboardButton("🗑️ Supprimer messages reçus", callback_data="admin_clear_received_messages")],
            [InlineKeyboardButton("📊 Voir les messages reçus", callback_data="admin_view_messages")],
            [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        
        await safe_edit_message(
            query,
            "📢 **Panel Message**\n\n"
            f"*Utilisateurs enregistrés :* {len(users_data['users'])}\n"
            f"*Messages reçus :* 0\n\n"
            "Choisissez une action :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
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
            [InlineKeyboardButton("⚙️ Service", callback_data="admin_service")],
            [InlineKeyboardButton("👥 Gestion Admins", callback_data="admin_manage_admins")],
            [InlineKeyboardButton("🚪 Quitter admin", callback_data="admin_quit")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, "⚙️ Panneau Admin :", reply_markup=markup)
    
    elif query.data == "admin_service":
        # Menu Service - Gestion des menus du /start
        keyboard = [
            [InlineKeyboardButton("📋 Voir les menus actuels", callback_data="admin_view_menus")],
            [InlineKeyboardButton("➕ Ajouter un menu", callback_data="admin_add_menu")],
            [InlineKeyboardButton("✏️ Modifier un menu", callback_data="admin_edit_menu")],
            [InlineKeyboardButton("🗑️ Supprimer un menu", callback_data="admin_delete_menu")],
            [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "⚙️ **Service - Gestion des Menus**\n\n"
            "Gérez les menus qui s'affichent dans la commande /start\n\n"
            "Choisissez une action :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    elif query.data == "admin_view_menus":
        # Afficher les menus actuels
        data = load_data()
        services = data.get("services", [])
        
        # Si services est une chaîne, la convertir en liste
        if isinstance(services, str):
            services = []
        
        if not services:
            message_text = "📋 **Menus actuels**\n\n❌ Aucun menu configuré"
        else:
            message_text = "📋 **Menus actuels**\n\n"
            for i, service in enumerate(services, 1):
                message_text += f"**{i}.** {service}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Retour au Service", callback_data="admin_service")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, message_text, reply_markup=markup, parse_mode="Markdown")
    
    elif query.data == "admin_add_menu":
        # Ajouter un nouveau menu
        keyboard = [[InlineKeyboardButton("🔙 Retour au Service", callback_data="admin_service")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "➕ **Ajouter un Menu**\n\n"
            "Envoyez le texte du nouveau menu que vous voulez ajouter :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        context.user_data["editing"] = "add_menu"
    
    elif query.data == "admin_edit_menu":
        # Modifier un menu existant
        data = load_data()
        services = data.get("services", [])
        
        # Si services est une chaîne, la convertir en liste
        if isinstance(services, str):
            services = []
        
        if not services:
            keyboard = [[InlineKeyboardButton("🔙 Retour au Service", callback_data="admin_service")]]
            markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                "✏️ **Modifier un Menu**\n\n❌ Aucun menu à modifier",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            return
        
        # Créer les boutons pour chaque menu
        keyboard = []
        for i, service in enumerate(services):
            keyboard.append([InlineKeyboardButton(f"✏️ {service[:30]}...", callback_data=f"admin_edit_menu_{i}")])
        keyboard.append([InlineKeyboardButton("🔙 Retour au Service", callback_data="admin_service")])
        
        markup = InlineKeyboardMarkup(keyboard)
        message_text = "✏️ **Modifier un Menu**\n\nChoisissez le menu à modifier :"
        await safe_edit_message(query, message_text, reply_markup=markup, parse_mode="Markdown")
    
    elif query.data == "admin_delete_menu":
        # Supprimer un menu
        data = load_data()
        services = data.get("services", [])
        
        # Si services est une chaîne, la convertir en liste
        if isinstance(services, str):
            services = []
        
        if not services:
            keyboard = [[InlineKeyboardButton("🔙 Retour au Service", callback_data="admin_service")]]
            markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                "🗑️ **Supprimer un Menu**\n\n❌ Aucun menu à supprimer",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            return
        
        # Créer les boutons pour chaque menu
        keyboard = []
        for i, service in enumerate(services):
            keyboard.append([InlineKeyboardButton(f"🗑️ {service[:30]}...", callback_data=f"admin_delete_menu_{i}")])
        keyboard.append([InlineKeyboardButton("🔙 Retour au Service", callback_data="admin_service")])
        
        markup = InlineKeyboardMarkup(keyboard)
        message_text = "🗑️ **Supprimer un Menu**\n\nChoisissez le menu à supprimer :"
        await safe_edit_message(query, message_text, reply_markup=markup, parse_mode="Markdown")
    
    elif query.data.startswith("admin_edit_menu_"):
        # Modifier un menu spécifique
        menu_index = int(query.data.split("_")[-1])
        data = load_data()
        services = data.get("services", [])
        
        # Si services est une chaîne, la convertir en liste
        if isinstance(services, str):
            services = []
        
        if 0 <= menu_index < len(services):
            context.user_data["editing_menu_index"] = menu_index
            keyboard = [[InlineKeyboardButton("🔙 Retour au Service", callback_data="admin_service")]]
            markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                f"✏️ **Modifier le Menu**\n\n"
                f"Menu actuel : {services[menu_index]}\n\n"
                f"Envoyez le nouveau texte pour ce menu :",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            context.user_data["editing"] = "edit_menu"
        else:
            await query.answer("❌ Menu introuvable")
    
    elif query.data.startswith("admin_delete_menu_"):
        # Supprimer un menu spécifique
        menu_index = int(query.data.split("_")[-1])
        data = load_data()
        services = data.get("services", [])
        
        # Si services est une chaîne, la convertir en liste
        if isinstance(services, str):
            services = []
        
        if 0 <= menu_index < len(services):
            # Supprimer le menu
            deleted_menu = services.pop(menu_index)
            data["services"] = services
            save_data(data)
            
            # Recharger les données pour s'assurer de la cohérence
            data = load_data()
            
            keyboard = [[InlineKeyboardButton("🔙 Retour au Service", callback_data="admin_service")]]
            markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                f"✅ **Menu supprimé**\n\n"
                f"Le menu '{deleted_menu}' a été supprimé avec succès !",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ Menu introuvable")
    
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
        
        # Afficher la liste des utilisateurs récents pour sélection
        users_data = load_users()
        users = users_data.get("users", [])
        
        if not users:
            keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="admin_manage_admins")]]
            markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                "➕ **Ajouter un Administrateur**\n\n"
                "❌ Aucun utilisateur trouvé pour ajouter comme admin.",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            return
        
        # Créer les boutons pour chaque utilisateur
        keyboard = []
        for user in users[:10]:  # Limiter à 10 utilisateurs récents
            user_id = user["user_id"]
            username = user.get("username", "N/A")
            name = user.get("name", "N/A")
            button_text = f"➕ {name} (@{username})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"admin_add_user_{user_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="admin_manage_admins")])
        markup = InlineKeyboardMarkup(keyboard)
        
        await safe_edit_message(
            query,
            "➕ **Ajouter un Administrateur**\n\n"
            "Choisissez un utilisateur à ajouter comme administrateur :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    elif query.data == "admin_remove_admin":
        if not is_chef(user_id):
            await query.answer("❌ Seul le Chef peut supprimer des administrateurs.")
            return
        
        # Afficher la liste des administrateurs pour sélection
        admins_data = load_admins()
        
        if not admins_data:
            keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="admin_manage_admins")]]
            markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                "❌ **Supprimer un Administrateur**\n\n"
                "❌ Aucun administrateur à supprimer.",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            return
        
        # Créer les boutons pour chaque admin
        keyboard = []
        for admin_id, admin_info in admins_data.items():
            role = admin_info.get("role", "STAFF")
            username = admin_info.get("username", "N/A")
            name = admin_info.get("name", "N/A")
            button_text = f"❌ {name} (@{username}) - {role}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"admin_remove_user_{admin_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="admin_manage_admins")])
        markup = InlineKeyboardMarkup(keyboard)
        
        await safe_edit_message(
            query,
            "❌ **Supprimer un Administrateur**\n\n"
            "Choisissez un administrateur à supprimer :",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("admin_add_user_"):
        # Ajouter un utilisateur comme administrateur
        target_user_id = int(query.data.split("_")[-1])
        
        # Récupérer les informations de l'utilisateur
        users_data = load_users()
        target_user = None
        for user in users_data.get("users", []):
            if user["user_id"] == target_user_id:
                target_user = user
                break
        
        if not target_user:
            await query.answer("❌ Utilisateur introuvable")
            return
        
        # Ajouter comme administrateur
        admins_data = load_admins()
        admins_data[str(target_user_id)] = {
            "username": target_user.get("username", "N/A"),
            "name": target_user.get("name", "N/A"),
            "role": "STAFF",
            "added_by": user_id,
            "added_date": str(update.effective_message.date)
        }
        save_admins(admins_data)
        
        # Mettre à jour la liste des admins en mémoire
        admins.add(target_user_id)
        
        keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="admin_manage_admins")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            f"✅ **Administrateur ajouté !**\n\n"
            f"**{target_user.get('name', 'N/A')}** (@{target_user.get('username', 'N/A')})\n"
            f"ID: `{target_user_id}`\n"
            f"Rôle: **STAFF**",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("admin_remove_user_"):
        # Supprimer un administrateur
        target_user_id = int(query.data.split("_")[-1])
        
        # Vérifier que ce n'est pas le chef qui se supprime lui-même
        if target_user_id == user_id:
            await query.answer("❌ Vous ne pouvez pas vous supprimer vous-même")
            return
        
        # Récupérer les informations de l'admin
        admins_data = load_admins()
        admin_info = admins_data.get(str(target_user_id))
        
        if not admin_info:
            await query.answer("❌ Administrateur introuvable")
            return
        
        # Supprimer l'administrateur
        del admins_data[str(target_user_id)]
        save_admins(admins_data)
        
        # Mettre à jour la liste des admins en mémoire
        admins.discard(target_user_id)
        
        keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="admin_manage_admins")]]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            f"✅ **Administrateur supprimé !**\n\n"
            f"**{admin_info.get('name', 'N/A')}** (@{admin_info.get('username', 'N/A')})\n"
            f"ID: `{target_user_id}`\n"
            f"Rôle: **{admin_info.get('role', 'STAFF')}**",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("select_msg_"):
        # Gérer la sélection d'un message
        msg_index = int(query.data.split("_")[2]) - 1  # Convertir en index 0-based
        user_id = query.from_user.id
        
        print(f"DEBUG: Sélection du message {msg_index} par l'utilisateur {user_id}")
        
        if not is_admin_or_higher(user_id):
            await query.answer("❌ Vous n'avez pas les permissions.")
            return
        
        # Initialiser la liste des messages sélectionnés si elle n'existe pas
        if "selected_messages" not in context.user_data:
            context.user_data["selected_messages"] = []
        
        print(f"DEBUG: Avant sélection - selected_messages = {context.user_data['selected_messages']}")
        
        # Ajouter ou retirer le message de la sélection
        if msg_index in context.user_data["selected_messages"]:
            context.user_data["selected_messages"].remove(msg_index)
            await query.answer("❌ Message désélectionné")
            print(f"DEBUG: Message {msg_index} désélectionné")
        else:
            context.user_data["selected_messages"].append(msg_index)
            await query.answer("✅ Message sélectionné")
            print(f"DEBUG: Message {msg_index} sélectionné")
        
        print(f"DEBUG: Après sélection - selected_messages = {context.user_data['selected_messages']}")
        
        # Mettre à jour l'affichage
        try:
            await update_message_display(query, context)
            print("DEBUG: update_message_display appelé avec succès")
        except Exception as e:
            print(f"DEBUG: Erreur dans update_message_display: {e}")
            await query.answer("Erreur lors de la mise à jour")
    
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
        
        print(f"DEBUG: Tentative de suppression par l'utilisateur {user_id}")
        
        if not is_admin_or_higher(user_id):
            await query.answer("❌ Vous n'avez pas les permissions.")
            return
        
        selected_messages = context.user_data.get("selected_messages", [])
        print(f"DEBUG: Messages sélectionnés: {selected_messages}")
        
        if not selected_messages:
            await query.answer("❌ Aucun message sélectionné")
            return
        
        # Charger les données
        users_data = load_users()
        messages = users_data.get("messages", [])
        recent_messages = messages[-10:]
        
        print(f"DEBUG: Nombre total de messages: {len(messages)}")
        print(f"DEBUG: Messages récents: {len(recent_messages)}")
        
        # Supprimer les messages sélectionnés (en ordre inverse pour éviter les problèmes d'index)
        deleted_count = 0
        for index in sorted(selected_messages, reverse=True):
            print(f"DEBUG: Traitement de l'index {index}")
            if 0 <= index < len(recent_messages):
                # Trouver l'index dans la liste complète
                # Les messages récents sont les 10 derniers, donc l'index dans la liste complète est :
                full_index = len(messages) - len(recent_messages) + index
                print(f"DEBUG: Index complet calculé: {full_index} (len(messages)={len(messages)}, len(recent)={len(recent_messages)}, index={index})")
                if 0 <= full_index < len(messages):
                    print(f"DEBUG: Suppression du message à l'index {full_index}")
                    messages.pop(full_index)
                    deleted_count += 1
                    print(f"DEBUG: Message supprimé, count = {deleted_count}")
                else:
                    print(f"DEBUG: Index {full_index} hors limites")
            else:
                print(f"DEBUG: Index {index} hors limites des messages récents")
        
        print(f"DEBUG: Nombre de messages supprimés: {deleted_count}")
        print(f"DEBUG: Nouveau nombre total de messages: {len(messages)}")
        
        # Sauvegarder les modifications
        users_data["messages"] = messages
        save_users(users_data)
        print("DEBUG: Données sauvegardées")
        
        # Nettoyer la sélection
        context.user_data["selected_messages"] = []
        
        await query.answer(f"✅ {deleted_count} messages supprimés")
        
        # Mettre à jour l'affichage
        try:
            await update_message_display(query, context)
            print("DEBUG: Affichage mis à jour avec succès")
        except Exception as e:
            print(f"DEBUG: Erreur lors de la mise à jour de l'affichage: {e}")
            await query.answer("Erreur lors de la mise à jour")
    
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
        elif section == "add_menu":
            # Ajouter un nouveau menu
            new_menu = update.message.text
            data = load_data()
            if "services" not in data:
                data["services"] = []
            # Si services est une chaîne, la convertir en liste
            if isinstance(data["services"], str):
                data["services"] = []
            data["services"].append(new_menu)
            save_data(data)
            context.user_data["editing"] = None
            
            # Recharger les données pour s'assurer de la cohérence
            data = load_data()
            
            # Retour au menu Service
            keyboard = [
                [InlineKeyboardButton("📋 Voir les menus actuels", callback_data="admin_view_menus")],
                [InlineKeyboardButton("➕ Ajouter un menu", callback_data="admin_add_menu")],
                [InlineKeyboardButton("✏️ Modifier un menu", callback_data="admin_edit_menu")],
                [InlineKeyboardButton("🗑️ Supprimer un menu", callback_data="admin_delete_menu")],
                [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            
            # Supprimer le message de l'utilisateur et envoyer la réponse
            try:
                await update.message.delete()
            except:
                pass
            
            await update.message.reply_text(
                f"✅ **Menu ajouté !**\n\n"
                f"Le menu '{new_menu}' a été ajouté avec succès !\n\n"
                f"⚙️ **Service - Gestion des Menus**",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        elif section == "edit_menu":
            # Modifier un menu existant
            new_text = update.message.text
            menu_index = context.user_data.get("editing_menu_index")
            data = load_data()
            services = data.get("services", [])
            
            # Si services est une chaîne, la convertir en liste
            if isinstance(services, str):
                services = []
            
            if 0 <= menu_index < len(services):
                old_menu = services[menu_index]
                services[menu_index] = new_text
                data["services"] = services
                save_data(data)
                context.user_data["editing"] = None
                context.user_data["editing_menu_index"] = None
                
                # Recharger les données pour s'assurer de la cohérence
                data = load_data()
                
                # Retour au menu Service
                keyboard = [
                    [InlineKeyboardButton("📋 Voir les menus actuels", callback_data="admin_view_menus")],
                    [InlineKeyboardButton("➕ Ajouter un menu", callback_data="admin_add_menu")],
                    [InlineKeyboardButton("✏️ Modifier un menu", callback_data="admin_edit_menu")],
                    [InlineKeyboardButton("🗑️ Supprimer un menu", callback_data="admin_delete_menu")],
                    [InlineKeyboardButton("🔙 Retour au panneau admin", callback_data="admin_panel")]
                ]
                markup = InlineKeyboardMarkup(keyboard)
                
                # Supprimer le message de l'utilisateur et envoyer la réponse
                try:
                    await update.message.delete()
                except:
                    pass
                
                await update.message.reply_text(
                    f"✅ **Menu modifié !**\n\n"
                    f"Ancien : {old_menu}\n"
                    f"Nouveau : {new_text}\n\n"
                    f"⚙️ **Service - Gestion des Menus**",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Erreur : Menu introuvable")
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
        await notify_admin_contact(context, user, message_text, timestamp)
        
        # Confirmer la réception du message
        await update.message.reply_text("✅ Message envoyé ! Nous vous répondrons bientôt.")
        
        # Désactiver le mode contact
        context.user_data["contact_mode"] = False
        return
    
    # Si c'est un utilisateur normal, enregistrer son message
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
    
    # Notifier l'admin du nouveau message
    await notify_admin_contact(context, user, message_text, timestamp)
    
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