import json
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

VOCABULARY_POOL_FILE = BASE_DIR / "data" / "vocabulary_pool.json"
USED_WORDS_FILE = BASE_DIR / "data" / "words.json"


def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_new_word():
    """Return one unused vocabulary word."""

    data = load_json(VOCABULARY_POOL_FILE)

    available_words = data.get("words", [])

    if not available_words:
        raise RuntimeError("No vocabulary words remaining.")

    return random.choice(available_words)


def mark_word_as_used(word):
    """
    Remove the word from the vocabulary pool
    and add it to the used words history.
    """

    # Load vocabulary pool
    pool_data = load_json(VOCABULARY_POOL_FILE)
    available_words = pool_data.get("words", [])

    # Remove the successfully generated word
    pool_data["words"] = [
        item for item in available_words
        if item.lower() != word.lower()
    ]

    save_json(VOCABULARY_POOL_FILE, pool_data)

    # Load used words
    used_data = load_json(USED_WORDS_FILE)
    used_words = used_data.get("words", [])

    # Add word to history
    if word.lower() not in {item.lower() for item in used_words}:
        used_words.append(word)

    used_data["words"] = used_words

    save_json(USED_WORDS_FILE, used_data)


if __name__ == "__main__":
    word = get_new_word()

    print(f"Selected word: {word}")

    # We are NOT marking it as used here.
    # It will only be marked after AI successfully generates the lesson.