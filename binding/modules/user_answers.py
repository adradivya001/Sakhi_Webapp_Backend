# modules/user_answers.py
from typing import List, Tuple

from supabase_client import supabase_insert


def save_user_answer(user_id: str, question_key: str, selected_options: List[str]):
    """
    Save a single answer row to sakhi_users_answer.
    """
    if not user_id:
        raise ValueError("user_id is required")
    if not question_key:
        raise ValueError("question_key is required")
    if not selected_options or not isinstance(selected_options, list):
        raise ValueError("selected_options must be a non-empty list of strings")

    payload = {
        "user_id": user_id,
        "question_key": question_key,
        "selected_options": selected_options,
    }

    return supabase_insert("sakhi_users_answer", payload)


def save_bulk_answers(user_id: str, answers: List[dict]) -> Tuple[int, List]:
    """
    Save multiple answers for a user. Returns (saved_count, raw_results).
    """
    if not answers:
        raise ValueError("answers cannot be empty")

    saved = 0
    results = []

    for answer in answers:
        q_key = answer.get("question_key")
        opts = answer.get("selected_options")

        result = save_user_answer(user_id, q_key, opts)
        results.append(result)
        saved += 1

    return saved, results
