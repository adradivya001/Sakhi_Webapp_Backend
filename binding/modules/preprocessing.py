# modules/preprocessing.py

import re
from langdetect import detect

def clean_text(text: str) -> str:
    """
    Removes extra spaces, newlines, emojis, and common garbage.
    Keeps message clean before embeddings.
    """
    if not text:
        return ""

    # Remove emojis
    text = re.sub(r"[^\w\s,.!?]", "", text)

    # Replace newlines with space
    text = text.replace("\n", " ")

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def detect_language(text: str) -> str:
    """
    Detects the language of the input text.
    Returns: 'en', 'hi', 'te', etc.
    """
    try:
        lang = detect(text)
        return lang
    except:
        return "en"
