
import os
from supabase_client import supabase_select
from rag import generate_embedding
from modules.model_gateway import get_model_gateway

def test_connection():
    print("--- Diagnostic Tests ---")

    try:
        # 1. Supabase test
        rows = supabase_select("sakhi_users", limit=1)
        print(f"✅ Supabase: Success! Found {len(rows)} users.")
        if rows:
            print(f"   Sample User ID: {rows[0].get('user_id')}")
            print(f"   Name: {rows[0].get('name')}")
    except Exception as e:
        print(f"❌ Supabase: Failed: {e}")

    try:
        # 2. OpenAI Embedding test
        print("Testing OpenAI Embedding...")
        emb = generate_embedding("hello")
        print(f"✅ OpenAI: Success! Vector length: {len(emb)}")
    except Exception as e:
        print(f"❌ OpenAI: Failed: {e}")

    try:
        # 3. ModelGateway test
        query = "what is ivf?"
        print(f"Testing ModelGateway with query: '{query}'")
        gateway = get_model_gateway()
        route = gateway.decide_route(query)
        print(f"✅ Gateway: Success! Route: {route}")
    except Exception as e:
        print(f"❌ Gateway: Failed: {e}")

if __name__ == "__main__":
    test_connection()
