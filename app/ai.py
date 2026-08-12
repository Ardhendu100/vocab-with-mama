import json
import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

AI_API_KEY = os.getenv("AI_API_KEY")

if not AI_API_KEY:
    raise RuntimeError("AI_API_KEY environment variable is not set.")


client = genai.Client(api_key=AI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"


def generate_lesson(word):
    """Generate a vocabulary lesson for the given word."""

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

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "temperature": 0.7
        }
    )

    if not response.text:
        raise RuntimeError("AI returned an empty response.")

    try:
        lesson = json.loads(response.text)
    except json.JSONDecodeError as exc:
        print("Raw AI response:")
        print(response.text)

        raise RuntimeError(
            "AI returned invalid JSON."
        ) from exc

    validate_lesson(lesson, word)

    return lesson


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