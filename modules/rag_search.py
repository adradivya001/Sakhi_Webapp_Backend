# modules/rag_search.py
import os
from typing import List, Dict

import supabase_client  # ensures .env is loaded once
from openai import OpenAI

from supabase_client import supabase_rpc, supabase_insert

EMBEDDING_MODEL = "text-embedding-3-small"

_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise Exception("OPENAI_API_KEY missing")

_client = OpenAI(api_key=_api_key)


def _clean_text(text: str) -> str:
    return (text or "").strip().replace("\n", " ")


def _generate_embedding(text: str) -> List[float]:
    cleaned = _clean_text(text)
    resp = _client.embeddings.create(model=EMBEDDING_MODEL, input=cleaned)
    return resp.data[0].embedding


def search_sakhi_kb(text: str, limit: int = 3) -> List[dict]:
    """
    Generate an embedding and query both match_sakhi_kb and match_faq RPCs.
    Returns merged top-N results sorted by similarity.
    """
    embedding = _generate_embedding(text)

    payload = {"query_embedding": embedding, "match_count": limit}

    kb_results = supabase_rpc("match_sakhi_kb", payload)
    faq_results = supabase_rpc("match_faq", payload)

    merged: List[Dict] = []

    if isinstance(kb_results, list):
        for item in kb_results:
            item = dict(item or {})
            item["source"] = "KNOWLEDGE"
            merged.append(item)
    if isinstance(faq_results, list):
        for item in faq_results:
            item = dict(item or {})
            item["source"] = "FAQ"
            merged.append(item)

    merged.sort(key=lambda r: r.get("similarity", 0), reverse=True)
    top = merged[:limit]
    print(f"RAG: Found {len(top)} merged results")
    return top


def add_kb_entry(title: str, content: str):
    """
    Insert a new KB entry with computed embedding.
    """
    if not content.strip():
        return None
    emb = _generate_embedding(content)
    payload = {
        "title": title[:120] if title else "Sakhi note",
        "content": content,
        "embedding": emb,
    }
    return supabase_insert("sakhi_bot_knowledge", payload)


def format_context(results: List[dict]) -> str:
    """
    Format retrieved knowledge into numbered bullet list for the prompt.
    """
    if not results or not isinstance(results, list):
        return "### Retrieved Knowledge:\nNone."

    lines = ["### Retrieved Knowledge:"]
    for idx, item in enumerate(results, start=1):
        source = item.get("source") or "KNOWLEDGE"
        if source.upper() == "FAQ":
            q = item.get("question") or "FAQ question"
            a = item.get("answer") or ""
            link = item.get("youtube_link")
            video_text = f"\n    YouTube: {link}" if link else ""
            lines.append(f"{idx}. (source: FAQ) Q: {q} → A: {a}{video_text}")
        else:
            title = item.get("title") or "Knowledge"
            content = item.get("content") or ""
            lines.append(f"{idx}. (source: KNOWLEDGE) {content or title}")

    return "\n".join(lines)
