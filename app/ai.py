import json
import os
import random
import time

from dotenv import load_dotenv
from google import genai

MAX_RETRIES = 3
BASE_DELAY = 2

load_dotenv()

AI_API_KEY = os.getenv("AI_API_KEY")

if not AI_API_KEY:
    raise RuntimeError("AI_API_KEY environment variable is not set.")


client = genai.Client(api_key=AI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"

def is_retryable_error(exc):
    """Return True when an AI error is likely temporary."""

    error_message = str(exc).upper()

    retryable_statuses = [
        "429",
        "500",
        "502",
        "503",
        "504",
        "UNAVAILABLE",
        "RESOURCE_EXHAUSTED",
        "INTERNAL",
        "TIMEOUT",
        "TIMED OUT",
        "CONNECTION",
    ]

    return any(
        status in error_message
        for status in retryable_statuses
    )

def generate_lesson(word):
    """Generate a vocabulary lesson with exponential backoff retries."""

    prompt = f"""
You are "Vocab with Mama", a friendly English vocabulary teacher.

Create a vocabulary lesson for this word:

WORD: {word}

Target learner:
An intermediate English speaker who wants to improve:
- Daily English communication
- Workplace communication
- Meetings
- Professional conversations

Important rules:

1. Keep the language simple and natural.
2. The word should be explained accurately.
3. Give a simple pronunciation that an Indian English learner can easily read.
4. Give a short and clear meaning.
5. Give exactly 5 natural example sentences.
6. Examples should be useful in real-life or workplace situations.
7. Give 3-5 common synonyms.
8. Give a simple and memorable "Mama's Tip".
9. Do not use unnecessarily complicated English.
10. Do not use rare or unnatural examples.
11. Do not change the given word.
12. Return ONLY valid JSON.
13. Do not return Markdown.
14. Do not add any explanation outside the JSON.

Return exactly this JSON structure:

{{
    "word": "{word}",
    "pronunciation": "...",
    "meaning": "...",
    "examples": [
        "...",
        "...",
        "...",
        "...",
        "..."
    ],
    "synonyms": [
        "...",
        "...",
        "..."
    ],
    "memory_tip": "..."
}}
"""

    for attempt in range(MAX_RETRIES + 1):
        try:
            print(
                f"Generating lesson with AI "
                f"(attempt {attempt + 1}/{MAX_RETRIES + 1})..."
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7,
                },
            )

            if not response.text:
                raise RuntimeError("AI returned an empty response.")

            try:
                lesson = json.loads(response.text)
            except json.JSONDecodeError as exc:
                print("AI returned invalid JSON.")

                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY * (2 ** attempt)
                    jitter = random.uniform(0, 0.5)  # It prevents multiple workers/services from retrying at exactly the same time
                    total_delay = delay + jitter

                    print(
                        f"Retrying in {total_delay:.2f} seconds..."
                    )

                    time.sleep(total_delay)
                    continue

                print("Raw AI response:")
                print(response.text)

                raise RuntimeError(
                    "AI returned invalid JSON after all retries."
                ) from exc

            validate_lesson(lesson, word)

            print("AI lesson generated successfully.")

            return lesson

        except Exception as exc:
            if not is_retryable_error(exc):
                raise

            if attempt == MAX_RETRIES:
                print(
                    f"AI request failed after "
                    f"{MAX_RETRIES + 1} attempts."
                )
                raise

            delay = BASE_DELAY * (2 ** attempt)
            jitter = random.uniform(0, 0.5)
            total_delay = delay + jitter

            print(f"AI request failed: {exc}")
            print(
                f"Retrying in {total_delay:.2f} seconds..."
            )

            time.sleep(total_delay)

    raise RuntimeError("AI generation failed.")

def validate_lesson(lesson, expected_word):
    """Validate the AI-generated vocabulary lesson."""

    required_fields = [
        "word",
        "pronunciation",
        "meaning",
        "examples",
        "synonyms",
        "memory_tip",
    ]

    for field in required_fields:
        if field not in lesson:
            raise RuntimeError(
                f"AI response is missing required field: {field}"
            )

    if not isinstance(lesson["word"], str):
        raise RuntimeError("Word must be a string.")

    if lesson["word"].lower() != expected_word.lower():
        raise RuntimeError("AI returned a different word.")

    if not isinstance(lesson["pronunciation"], str):
        raise RuntimeError("Pronunciation must be a string.")

    if not isinstance(lesson["meaning"], str):
        raise RuntimeError("Meaning must be a string.")

    if not isinstance(lesson["examples"], list):
        raise RuntimeError("Examples must be a list.")

    if len(lesson["examples"]) != 5:
        raise RuntimeError("AI must return exactly 5 examples.")

    if not isinstance(lesson["synonyms"], list):
        raise RuntimeError("Synonyms must be a list.")

    if not 3 <= len(lesson["synonyms"]) <= 5:
        raise RuntimeError("AI must return 3-5 synonyms.")

    if not isinstance(lesson["memory_tip"], str):
        raise RuntimeError("Memory tip must be a string.")


if __name__ == "__main__":
    test_word = "meticulous"

    lesson = generate_lesson(test_word)

    print(json.dumps(lesson, indent=2, ensure_ascii=False))