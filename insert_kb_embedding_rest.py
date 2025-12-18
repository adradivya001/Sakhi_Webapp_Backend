# insert_kb_embedding_rest.py
from supabase_client import supabase_select, supabase_update
from rag import generate_embedding

# Step 1: Fetch all rows
rows = supabase_select("sakhi_bot_knowledge", "*")

print("\n================ RAW RESPONSE FROM SUPABASE ================")
print(rows)
print("============================================================\n")

# If not a list, stop
if not isinstance(rows, list):
    print("ERROR: Supabase did NOT return a list. Cannot continue.")
    exit()

# Step 2: Filter rows without embedding
rows_to_update = [row for row in rows if row.get("embedding") is None]

print("Found rows needing embeddings:", len(rows_to_update))

# Step 3: Loop through rows and update
for row in rows_to_update:
    kb_id = row["kb_id"]
    content = row["content"]

    print(f"Generating embedding for KB ID: {kb_id}")

    emb = generate_embedding(content)

    match = f"kb_id=eq.{kb_id}"
    data = {"embedding": emb}

    resp = supabase_update("sakhi_bot_knowledge", match, data)
    print("Updated row:", resp)

print("All embeddings updated!")
