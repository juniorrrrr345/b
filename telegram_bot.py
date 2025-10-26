import json
import os
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


data = load_data()
admins = set()  # liste des ID admins connectés


# --- Commande /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await query.edit_message_media(
                media=InputMediaPhoto(media=welcome_photo, caption=welcome_text),
                reply_markup=reply_markup
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
        await query.edit_message_text(text=content, reply_markup=reply_markup)


# --- Commande /admin ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    elif query.data == "admin_panel":
        keyboard = [
            [
                InlineKeyboardButton("✏️ Modifier Contact", callback_data="admin_edit_contact"),
                InlineKeyboardButton("✏️ Modifier Services", callback_data="admin_edit_services")
            ],
            [InlineKeyboardButton("🖼️ Panel Admin Photo", callback_data="admin_photo_panel")],
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
    await admin_actions(update, context)

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