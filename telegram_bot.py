import json
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
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
    await update.message.reply_text(
        "👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :",
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
        await query.edit_message_text(
            "👋 Bonjour et bienvenue sur notre bot !\nChoisissez une option :",
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
            await show_admin_panel(update)
        else:
            await update.message.reply_text("❌ Mot de passe incorrect.")
        return True
    return False


# --- Panneau admin principal ---
async def show_admin_panel(update: Update):
    keyboard = [
        [
            InlineKeyboardButton("✏️ Modifier Contact", callback_data="admin_edit_contact"),
            InlineKeyboardButton("✏️ Modifier Services", callback_data="admin_edit_services")
        ],
        [InlineKeyboardButton("🚪 Quitter admin", callback_data="admin_quit")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Panneau Admin :", reply_markup=markup)


# --- Gestion des callbacks admin ---
async def handle_admin_callback(query, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    if user_id not in admins:
        await query.edit_message_text("❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
        return
    
    if query.data == "admin_edit_contact":
        await query.edit_message_text(
            "✏️ **Modification du Contact**\n\n"
            "Envoie le nouveau texte pour *Contact* :\n\n"
            f"*Texte actuel :*\n{data.get('contact', 'Aucun texte défini')}",
            parse_mode="Markdown"
        )
        context.user_data["editing"] = "contact"
    elif query.data == "admin_edit_services":
        await query.edit_message_text(
            "✏️ **Modification des Services**\n\n"
            "Envoie le nouveau texte pour *Services* :\n\n"
            f"*Texte actuel :*\n{data.get('services', 'Aucun texte défini')}",
            parse_mode="Markdown"
        )
        context.user_data["editing"] = "services"
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
        data[section] = update.message.text
        save_data(data)
        context.user_data["editing"] = None
        
        # Retour au menu admin
        keyboard = [
            [
                InlineKeyboardButton("✏️ Modifier Contact", callback_data="admin_edit_contact"),
                InlineKeyboardButton("✏️ Modifier Services", callback_data="admin_edit_services")
            ],
            [InlineKeyboardButton("🚪 Quitter admin", callback_data="admin_quit")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"✅ Texte '{section}' mis à jour !\n\n⚙️ Panneau Admin :",
            reply_markup=markup
        )
    else:
        await update.message.reply_text("Commande non reconnue.")


# --- Gestion du texte (mot de passe ou actions admin) ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_password(update, context):
        return
    await admin_actions(update, context)


# --- Fonction principale ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot en marche...")
    app.run_polling()


if __name__ == "__main__":
    main()