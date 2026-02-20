# rag.py
import os

import supabase_client  # ensures .env is loaded once
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions

_api_key = os.getenv("OPENAI_API_KEY")
client = None
if _api_key:
    client = OpenAI(api_key=_api_key)



def generate_embedding(text: str):
    """
    Converts text into a 1536-dimensional embedding vector using OpenAI.
    """
    if not client:
        raise Exception("OPENAI_API_KEY missing. Cannot generate embeddings.")
    cleaned = text.strip().replace("\n", " ")

    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=cleaned
    )

    return resp.data[0].embedding


def generate_embeddings(texts: list[str]):
    """
    Converts a list of texts into embedding vectors in a single batch call.
    """
    if not client:
        raise Exception("OPENAI_API_KEY missing. Cannot generate embeddings.")
    
    cleaned_texts = [t.strip().replace("\n", " ") for t in texts]
    
    # OpenAI supports up to 2048 inputs per request (ours will be much less)
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=cleaned_texts
    )
    
    # Match embeddings to input order
    return [item.embedding for item in resp.data]
