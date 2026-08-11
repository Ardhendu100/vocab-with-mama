import json
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

USERS_FILE = BASE_DIR / "data" / "users.json"
LATEST_FILE = BASE_DIR / "data" / "latest.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN environment variable is not set."
    )


def load_json(file_path):
    """Load JSON data from a file."""

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(file_path, data):
    """Save JSON data to a file."""

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_users():
    """Return the list of subscribed Telegram users."""

    data = load_json(USERS_FILE)

    return data.get("users", [])


def save_users(users):
    """Save the subscribed users."""

    save_json(
        USERS_FILE,
        {
            "users": users
        },
    )


def format_lesson(lesson):
    """Convert AI lesson JSON into the Vocab with Mama message."""

    examples = "\n".join(
        f"{index}. {example}"
        for index, example in enumerate(lesson["examples"], start=1)
    )

    synonyms = ", ".join(lesson["synonyms"])

    message = f"""👩‍🏫 <b>Vocab with Mama</b>

📚 <b>Today's Word: {lesson["word"].capitalize()}</b>

🔊 <b>Pronunciation:</b>
{lesson["pronunciation"]}

📖 <b>Meaning:</b>
{lesson["meaning"]}

📝 <b>Examples:</b>

{examples}

🔄 <b>Synonyms:</b>
{synonyms}

💡 <b>Mama's Tip:</b>
{lesson["memory_tip"]}
"""

    return message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""

    chat_id = update.effective_chat.id

    users = load_users()

    if chat_id not in users:
        users.append(chat_id)
        save_users(users)

        message = """👩‍🏫 <b>Welcome to Vocab with Mama! ❤️</b>

I'll send you one useful English word every day.

See you tomorrow! 📚"""

    else:
        message = """👩‍🏫 <b>You're already subscribed! ❤️</b>

I'll keep sending you one useful English word every day. 📚"""

    await update.message.reply_text(
        message,
        parse_mode="HTML",
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command."""

    chat_id = update.effective_chat.id

    users = load_users()

    if chat_id in users:
        users.remove(chat_id)
        save_users(users)

        message = """👋 <b>You've been unsubscribed.</b>

You won't receive the daily vocabulary lessons anymore.

You can always come back with /start. ❤️"""

    else:
        message = """You're not currently subscribed.

Use /start if you'd like to receive daily vocabulary lessons. 📚"""

    await update.message.reply_text(
        message,
        parse_mode="HTML",
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /today command."""

    latest_data = load_json(LATEST_FILE)

    lesson = latest_data.get("lesson")

    if not lesson:
        await update.message.reply_text(
            "📚 Mama hasn't prepared today's lesson yet. Check back soon! ❤️"
        )
        return

    message = format_lesson(lesson)

    await update.message.reply_text(
        message,
        parse_mode="HTML",
    )


def create_bot_application():
    """Create and configure the Telegram bot."""

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("stop", stop)
    )

    application.add_handler(
        CommandHandler("today", today)
    )

    return application


if __name__ == "__main__":
    application = create_bot_application()

    print("Vocab with Mama bot is running...")

    application.run_polling()