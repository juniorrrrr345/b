import json
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

TOKEN = "TON_TOKEN_ICI"         # ← Ton token Telegram
ADMIN_PASSWORD = "1234"         # ← Ton mot de passe admin
DATA_FILE = "data.json"         # ← Fichier pour stocker les textes


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
    content = data.get(query.data, "Texte non défini.")
    await query.edit_message_text(text=content)


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
        [KeyboardButton("✏️ Modifier Contact")],
        [KeyboardButton("✏️ Modifier Services")],
        [KeyboardButton("🚪 Quitter admin")],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("⚙️ Panneau Admin :", reply_markup=markup)


# --- Gestion des actions admin ---
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in admins:
        return

    text = update.message.text
    if text == "✏️ Modifier Contact":
        await update.message.reply_text("Envoie le nouveau texte pour *Contact* :", parse_mode="Markdown")
        context.user_data["editing"] = "contact"
    elif text == "✏️ Modifier Services":
        await update.message.reply_text("Envoie le nouveau texte pour *Services* :", parse_mode="Markdown")
        context.user_data["editing"] = "services"
    elif text == "🚪 Quitter admin":
        admins.discard(user_id)
        context.user_data.clear()
        await update.message.reply_text("✅ Déconnecté du mode admin.", reply_markup=None)
    else:
        # Enregistrement d'une modification
        section = context.user_data.get("editing")
        if section:
            data[section] = text
            save_data(data)
            context.user_data["editing"] = None
            await update.message.reply_text(f"✅ Texte '{section}' mis à jour !")
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