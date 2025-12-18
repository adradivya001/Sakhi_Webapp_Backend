import json
import time
from typing import List, Dict, Any

# --- Import your existing modules ---
# Ensure supabase_client.py and rag.py are in the same folder
try:
    from supabase_client import supabase_insert
    from rag import generate_embedding
except ImportError:
    print("Error: Could not import 'supabase_client' or 'rag'. Ensure these files exist.")
    exit(1)

def process_node(node: Dict[str, Any], path_stack: List[str]):
    """
    Recursive function to traverse the JSON tree.
    It identifies H3 nodes as the 'Leaf/Parent' entry for the database
    and processes their chunks.
    """
    
    current_level = node.get("level", "")
    title = node.get("title", "Untitled")
    
    # Update path stack for this node
    current_path = path_stack + [title]
    
    # Case 1: We are at the H3 level (The "Section")
    # This is where we act: Insert Parent -> Insert Chunks
    if current_level == "H3":
        process_h3_section(node, current_path)
        return

    # Case 2: We are at H1 or H2 (Container levels)
    # Recurse into children if they exist
    if "children" in node:
        for child in node["children"]:
            process_node(child, current_path)

def process_h3_section(node: Dict[str, Any], path_stack: List[str]):
    """
    Ingests a specific H3 section and its chunks into Supabase.
    """
    # 1. Construct Header Path (e.g., "Inner Battle > Psychology > Why do I feel guilty?")
    header_path = " > ".join(path_stack)
    
    chunks = node.get("chunks", [])
    if not chunks:
        print(f"Skipping empty H3 section: {header_path}")
        return

    # 2. Prepare Parent Section Data
    # We combine all chunk texts to create the 'full content' representation for the parent
    full_content = "\n".join([c.get("text", "") for c in chunks])
    
    parent_data = {
        "header_path": header_path,
        "content": full_content,
        "token_count": len(full_content.split())
    }

    try:
        # A. Insert Parent into 'sakhi_sections'
        print(f"Inserting Parent: {header_path}")
        response_data = supabase_insert("sakhi_sections", parent_data)
        
        if not response_data:
            print(f"Error: DB returned no data for section: {header_path}")
            return
            
        parent_id = response_data[0]['id']
        
        # B. Process and Insert Chunks
        for i, chunk_item in enumerate(chunks):
            chunk_text = chunk_item.get("text", "").strip()
            
            if not chunk_text:
                continue

            # Generate Embedding
            vector = generate_embedding(chunk_text)
            
            child_data = {
                "section_id": parent_id,
                "chunk_content": chunk_text,
                "embedding": vector,
                # Optional: You can store source_id if your DB schema allows metadata
                # "metadata": {"source_id": chunk_item.get("source_id")} 
            }
            
            # Insert into 'sakhi_section_chunks'
            supabase_insert("sakhi_section_chunks", child_data)
            print(f"  -> Ingested Chunk {i+1}/{len(chunks)}")

    except Exception as e:
        print(f"Failed to process section '{header_path}': {e}")

def ingest_json_file(file_path: str):
    """
    Main entry point to read JSON and start traversal.
    """
    print(f"Reading JSON file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        root_nodes = data.get("document_structure", [])
        print(f"Found {len(root_nodes)} root (H1) nodes.")
        
        for node in root_nodes:
            process_node(node, [])
            
        print("\n--- Ingestion Complete ---")
        
    except FileNotFoundError:
        print("Error: File not found.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Ingest Hierarchical JSON into Supabase')
    parser.add_argument('file', nargs='?', help='Path to the .json file')
    args = parser.parse_args()

    file_path = args.file

    # Default to looking for a json file if not provided
    if not file_path:
        json_files = [f for f in os.listdir('.') if f.endswith('.json')]
        if json_files:
            file_path = json_files[0]
            print(f"Auto-detected file: {file_path}")
        else:
            print("Usage: python ingest_json.py <path_to_json_file>")
            exit(1)

    ingest_json_file(file_path)