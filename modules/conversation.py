# modules/conversation.py
from datetime import datetime
import uuid

from supabase_client import supabase_insert, supabase_select


def _save_message(user_id: str, message: str, lang: str, message_type: str, chat_id: str | None = None):
    payload = {
        "user_id": user_id,
        "message_text": message,
        "message_type": message_type,
        "language": lang,
        "created_at": datetime.utcnow().isoformat(),
    }
    if chat_id:
        payload["chat_id"] = chat_id
    return supabase_insert("sakhi_conversations", payload)


def save_user_message(user_id: str, text: str, lang: str = "en"):
    return _save_message(user_id, text, lang, "user")


def save_sakhi_message(user_id: str, text: str, lang: str = "en"):
    chat_id = str(uuid.uuid4())
    return _save_message(user_id, text, lang, "sakhi", chat_id=chat_id)


def save_conversation(user_id: str, message: str, message_type: str, language: str):
    return _save_message(user_id, message, language, message_type)


def get_last_messages(user_id: str, limit: int = 5):
    """
    Fetch last N messages for a user ordered by created_at descending.
    Returns list of {"role": "user"|"sakhi", "content": "..."}.
    """
    rows = supabase_select(
        "sakhi_conversations",
        select="user_id,message_text,message_type,language,created_at",
        filters=f"user_id=eq.{user_id}",
        limit=50,  # grab recent chunk, then trim
    )

    if not rows or not isinstance(rows, list):
        return []

    sorted_rows = sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)
    recent = sorted_rows[:limit]

    history = []
    for r in reversed(recent):  # oldest to newest
        role = "user" if r.get("message_type") == "user" else "sakhi"
        history.append({"role": role, "content": r.get("message_text", "")})

    return history
