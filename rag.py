# rag.py
import os

import supabase_client  # ensures .env is loaded once
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions

_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise Exception("OPENAI_API_KEY missing")

client = OpenAI(api_key=_api_key)


def generate_embedding(text: str):
    """
    Converts text into a 1536-dimensional embedding vector using OpenAI.
    """
    cleaned = text.strip().replace("\n", " ")

    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=cleaned
    )

    return resp.data[0].embedding
