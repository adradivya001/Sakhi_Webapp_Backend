# search_kb_rest.py
from rag import generate_embedding
from supabase_client import SUPABASE_URL, SUPABASE_SERVICE_ROLE, HEADERS
import requests
import json

def search_sakhi_knowledge(query: str, top_k: int = 5):
    # 1. Generate embedding for user query
    query_embedding = generate_embedding(query)

    # 2. Send REST RPC call using pgvector cosine operator
    url = f"{SUPABASE_URL}/rest/v1/rpc/match_sakhi_kb"

    payload = {
        "query_embedding": query_embedding,
        "match_count": top_k
    }

    r = requests.post(url, headers=HEADERS, json=payload)

    try:
        return r.json()
    except:
        print("Raw response:", r.text)
        return None


# Test the search
results = search_sakhi_knowledge("what are the pregnancy signs?")
print(json.dumps(results, indent=2))
