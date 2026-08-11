import asyncio
import json
from datetime import date
from pathlib import Path

from ai import generate_lesson
from bot import (
    create_bot_application,
    load_users,
    send_lesson_to_user,
)
from vocabulary import (
    get_new_word,
    mark_word_as_used,
)


BASE_DIR = Path(__file__).resolve().parent.parent

LATEST_FILE = BASE_DIR / "data" / "latest.json"


def load_latest():
    """Load the latest generated lesson."""

    with open(LATEST_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_latest(lesson):
    """Replace latest.json with the new lesson."""

    data = {
        "date": date.today().isoformat(),
        "word": lesson["word"],
        "lesson": lesson,
    }

    with open(LATEST_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def lesson_already_generated():
    """Check whether today's lesson has already been generated."""

    data = load_latest()

    return data.get("date") == date.today().isoformat()


async def send_daily_lesson():
    """Generate and send today's vocabulary lesson."""

    print("Starting Vocab with Mama daily workflow...")

    # --------------------------------------------------
    # 1. Prevent duplicate daily execution
    # --------------------------------------------------

    if lesson_already_generated():
        print("Today's lesson has already been generated.")
        return

    # --------------------------------------------------
    # 2. Load Telegram subscribers
    # --------------------------------------------------

    users = load_users()

    if not users:
        print("No subscribers found.")
        print("The vocabulary word will not be consumed.")
        return

    print(f"Found {len(users)} subscribers.")

    # --------------------------------------------------
    # 3. Select a new vocabulary word
    # --------------------------------------------------

    word = get_new_word()

    print(f"Selected word: {word}")

    # --------------------------------------------------
    # 4. Generate lesson using AI
    # --------------------------------------------------

    try:
        print("Generating lesson with AI...")

        lesson = generate_lesson(word)

        print("AI lesson generated successfully.")

    except Exception as exc:
        print(f"AI generation failed: {exc}")
        print("Word will remain in the vocabulary pool.")
        return

    # --------------------------------------------------
    # 5. Save latest lesson
    # --------------------------------------------------

    save_latest(lesson)

    print("Latest lesson saved.")

    # --------------------------------------------------
    # 6. Create Telegram application
    # --------------------------------------------------

    application = create_bot_application()

    await application.initialize()

    all_sent = True

    try:

        # --------------------------------------------------
        # 7. Send SAME lesson to every subscriber
        # --------------------------------------------------

        for chat_id in users:

            try:

                await send_lesson_to_user(
                    application,
                    chat_id,
                    lesson,
                )

                print(f"Lesson successfully sent to {chat_id}")

            except Exception as exc:

                print(
                    f"Failed to send lesson to {chat_id}: {exc}"
                )

                all_sent = False

    finally:

        await application.shutdown()

    # --------------------------------------------------
    # 8. Mark word as used ONLY if everyone received it
    # --------------------------------------------------

    if all_sent:

        mark_word_as_used(word)

        print(
            f"All users received the lesson. "
            f"'{word}' marked as used."
        )

        print("Daily workflow completed successfully.")

    else:

        print(
            "At least one Telegram delivery failed."
        )

        print(
            f"'{word}' was NOT marked as used."
        )

        print(
            "The word remains in vocabulary_pool.json "
            "for retry."
        )


if __name__ == "__main__":
    asyncio.run(send_daily_lesson())