# backfill_embeddings.py
"""
Backfill embeddings for sakhi_kb rows that are missing an embedding.

Usage:
    python backfill_embeddings.py
Requires:
    - .env with OPENAI_API_KEY and Supabase service role credentials
"""

from supabase_client import supabase_select, supabase_update
from modules.rag_search import _generate_embedding


def main():
    # Target the real KB table
    rows = supabase_select("sakhi_bot_knowledge", select="kb_id,title,content,embedding")
    if not rows or not isinstance(rows, list):
        print("No rows returned from sakhi_bot_knowledge")
        return

    updated = 0
    for row in rows:
        if row.get("embedding"):
            continue
        content = (row.get("content") or "").strip()
        if not content:
            continue

        emb = _generate_embedding(content)
        match = f"kb_id=eq.{row['kb_id']}"
        supabase_update("sakhi_bot_knowledge", match, {"embedding": emb})
        updated += 1
        print(f"Updated embedding for: {row.get('kb_id')} ({row.get('title')})")

    print(f"Completed. Updated embeddings for {updated} rows.")


if __name__ == "__main__":
    main()
