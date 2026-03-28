import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import anthropic
from pyairtable import Api

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_CONTACT = 1

# Clients
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
airtable_api = Api(os.getenv("AIRTABLE_API_KEY"))
airtable_table = airtable_api.table(
    os.getenv("AIRTABLE_BASE_ID"),
    os.getenv("AIRTABLE_TABLE_NAME"),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_contact_with_claude(user_message: str) -> dict | None:
    """Use Claude to extract name, email and phone from a free-form message."""
    prompt = f"""Extrae el nombre, el email y el número de celular (con código de país si lo incluye) del siguiente mensaje de un usuario.
Devuelve SOLO un JSON con las claves "name", "email" y "phone".
Si no puedes encontrar alguno de los tres campos, pon null en ese campo.
No incluyas explicaciones, solo el JSON.

Mensaje del usuario: "{user_message}"
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()

    # Strip markdown code fences if Claude wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
        return data
    except json.JSONDecodeError:
        logger.error("Claude returned invalid JSON: %s", raw)
        return None


def save_to_airtable(name: str, email: str, phone: str | None) -> str:
    """Create a new record in Airtable. Returns the record ID."""
    fields = {
        "name": name,
        "email": email,
        "Owner": "roesinf2@gmail.com",
    }
    if phone:
        fields["phone"] = phone
    record = airtable_table.create(fields)
    logger.info("Lead guardado: %s / %s / %s", name, email, phone)
    return record["id"]


OPTION_LABELS = {
    "kanban_pro": "KanbanPRO (Free Trial)",
    "gifts": "Mis Regalos (Gifts)",
    "support": "Soporte / Consultas",
}


def build_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🚀 KanbanPRO (Free Trial)", callback_data="kanban_pro")],
        [InlineKeyboardButton("🎁 Mis Regalos (Gifts)", callback_data="gifts")],
        [InlineKeyboardButton("🛠 Soporte / Consultas", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def info_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Triggered when user sends 'info.'"""
    welcome = (
        "¡Hola! 👋 Bienvenido/a.\n\n"
        "Para enviarte todo, necesito:\n\n"
        "👤 Nombre\n"
        "📧 Email\n"
        "📱 Celular (ej: +52 55 1234 5678)\n\n"
        "Escríbelos aquí 👇"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")
    return WAITING_FOR_CONTACT


async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Extracts name + email via Claude and saves to Airtable."""
    user_message = update.message.text
    username = update.effective_user.username

    await update.message.reply_text("⏳ Un momento, procesando tu información...")

    contact = extract_contact_with_claude(user_message)

    if not contact or not contact.get("name") or not contact.get("email"):
        await update.message.reply_text(
            "Hmm, no pude encontrar tu nombre o email. "
            "¿Podrías escribirlos de nuevo? Por ejemplo:\n\n"
            "_Soy Ana, mi correo es ana@ejemplo.com y mi cel es +52 55 1234 5678_",
            parse_mode="Markdown",
        )
        return WAITING_FOR_CONTACT

    name = contact["name"].strip()
    email = contact["email"].strip().lower()
    phone = contact.get("phone")
    if phone:
        phone = str(phone).strip()

    try:
        record_id = save_to_airtable(name, email, phone)
        context.user_data["airtable_record_id"] = record_id
    except Exception as exc:
        logger.error("Airtable error: %s", exc)
        await update.message.reply_text(
            "Hubo un problema al guardar tus datos. Por favor intenta de nuevo."
        )
        return WAITING_FOR_CONTACT

    phone_line = f"📱 Celular: *{phone}*\n" if phone else ""
    confirmation = (
        f"¡Perfecto, *{name}*! 🎉\n\n"
        f"📧 Email: *{email}*\n"
        f"{phone_line}"
        "\nTodo registrado correctamente. ¿Qué te gustaría explorar primero? 👇"
    )
    await update.message.reply_text(
        confirmation,
        parse_mode="Markdown",
        reply_markup=build_main_menu(),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Conversación cancelada. Escribe *info.* cuando quieras empezar de nuevo.", parse_mode="Markdown")
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Inline button callbacks
# ---------------------------------------------------------------------------

BUTTON_RESPONSES = {
    "kanban_pro": (
        "🚀 *KanbanPRO — Free Trial*\n\n"
        "Gracias por proporcionar la información, en breve recibirás un correo con los detalles. 📩"
    ),
    "gifts": (
        "🎁 *Mis Regalos*\n\n"
        "Aquí tienes tu regalo exclusivo 👇\n"
        "https://azure-ferry-3c3.notion.site/High-Intensity-Training-HIT-2694f515cfb080778403e01c6ba843d4"
    ),
    "support": (
        "🛠 *Soporte / Consultas*\n\n"
        "Encuentra respuestas a las preguntas más frecuentes aquí 👇\n"
        "https://azure-ferry-3c3.notion.site/PREGUNTAS-FRECUENTES-15e4f515cfb080b0b635d0779fab3673"
    ),
}


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Update Airtable record with selected option
    record_id = context.user_data.get("airtable_record_id")
    label = OPTION_LABELS.get(query.data)
    if record_id and label:
        try:
            airtable_table.update(record_id, {"option selected": label})
            logger.info("Opción guardada en Airtable: %s -> %s", record_id, label)
        except Exception as exc:
            logger.error("Error guardando opción en Airtable: %s", exc)

    response_text = BUTTON_RESPONSES.get(query.data, "Opción no reconocida.")
    await query.edit_message_text(
        response_text,
        parse_mode="Markdown",
        reply_markup=build_main_menu(),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def post_init(application) -> None:
    webhook_info = await application.bot.get_webhook_info()
    if webhook_info.url:
        logger.info("Webhook activo detectado: %s — eliminando...", webhook_info.url)
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook eliminado. Bot listo para polling.")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en .env")

    app = ApplicationBuilder().token(token).post_init(post_init).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", info_trigger)],
        states={
            WAITING_FOR_CONTACT: [
                CommandHandler("start", info_trigger),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot iniciado. Esperando mensajes...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
