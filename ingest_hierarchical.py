import re
import time
from typing import List, Dict, Any

# Import from existing modules
from supabase_client import supabase_insert
from rag import generate_embedding

def parse_hierarchical_text(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses the text to respect H1 > H2 > H3 hierarchy.
    Returns a list of 'Parent' sections.
    """
    lines = raw_text.split('\n')
    
    parsed_data = []
    
    # State trackers
    h1 = "Document"
    h2 = "General"
    h3 = "Overview"
    current_content = []
    
    # Regex to identify headers and content
    # Matches: (H1): Title or (H2): Title or (H3): Title
    # Note: The user's example showed "(H1): Title", so we match that.
    header_pattern = re.compile(r"\(H(\d)\): (.+)")
    # Matches: (Source) Content... or just Content if no source tag
    # The user's example showed content lines starting with "(...)" sometimes or just text.
    # We will treat any non-header line as content.
    
    def save_current_section():
        """Helper to save the accumulated content before switching headers"""
        if current_content:
            full_text = " ".join(current_content).strip()
            if len(full_text) > 0:
                # Create a path string: "Fertility Fundamentals > Definition of Fertility"
                path = f"{h1} > {h2} > {h3}"
                parsed_data.append({
                    "header_path": path,
                    "content": full_text
                })
    
    for line in lines:
        line = line.strip()
        if not line: continue

        header_match = header_pattern.match(line)

        if header_match:
            # We found a new header (H1, H2, or H3)
            # 1. Save whatever we were working on previously
            save_current_section()
            current_content = [] # Reset content buffer

            # 2. Update hierarchy pointers
            level = header_match.group(1) # "1", "2", or "3"
            title = header_match.group(2).strip()

            if level == "1":
                h1 = title
                h2 = "General" # Reset lower levels
                h3 = "Overview"
            elif level == "2":
                h2 = title
                h3 = "Overview" # Reset lower level
            elif level == "3":
                h3 = title
        
        else:
            # It's a content line (and not a header)
            # We can do some basic cleaning if needed
            # For now, just append
            current_content.append(line)

    # Save the very last section
    save_current_section()
    
    return parsed_data

def ingest_to_supabase(sections: List[Dict[str, Any]]):
    print(f"Starting ingestion of {len(sections)} parent sections...")
    
    for idx, section in enumerate(sections):
        # 1. Insert Parent Section
        parent_data = {
            "header_path": section['header_path'],
            "content": section['content'],
            "token_count": len(section['content'].split())
        }
        
        try:
            # Using supabase_insert from supabase_client.py
            # Note: supabase_insert returns the inserted data (list of dicts)
            response_data = supabase_insert("sakhi_sections", parent_data)
            
            if not response_data:
                print(f"Error inserting section: {section['header_path']}")
                continue
                
            parent_id = response_data[0]['id']
            
            # 2. Create Children (Chunks)
            # Split by period to get sentence-level chunks. 
            raw_chunks = section['content'].split('. ')
            
            # Clean chunks and filter empty ones
            chunks_to_embed = [c.strip() for c in raw_chunks if len(c) > 15]
            
            if not chunks_to_embed:
                continue

            # Process each chunk
            for chunk in chunks_to_embed:
                # Generate embedding using rag.py
                vector = generate_embedding(chunk)
                
                child_data = {
                    "section_id": parent_id,
                    "chunk_content": chunk,
                    "embedding": vector
                }
                
                # Insert child
                supabase_insert("sakhi_section_chunks", child_data)
                
            print(f"[{idx+1}/{len(sections)}] Processed: {section['header_path']}")
            
        except Exception as e:
            print(f"Failed to process section {idx}: {e}")
            # Optional: sleep to avoid rate limits if needed
            # time.sleep(0.5)

import sys
import os
try:
    from docx import Document
except ImportError:
    print("Error: python-docx is not installed. Please run: pip install python-docx")
    sys.exit(1)

def extract_text_from_docx(file_path: str) -> str:
    """
    Reads a .docx file and converts it to the text format expected by parse_hierarchical_text.
    It handles both:
    1. Explicit text tags: "(H1): Title"
    2. Word Styles: Heading 1 -> "(H1): Title"
    """
    doc = Document(file_path)
    full_text = []
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
            
        style_name = para.style.name
        
        # Map Word Styles to our text format
        if style_name.startswith('Heading 1'):
            # Avoid double tagging if the text already has it
            if not text.startswith('(H1):'):
                text = f"(H1): {text}"
        elif style_name.startswith('Heading 2'):
            if not text.startswith('(H2):'):
                text = f"(H2): {text}"
        elif style_name.startswith('Heading 3'):
            if not text.startswith('(H3):'):
                text = f"(H3): {text}"
                
        full_text.append(text)
        
    return "\n".join(full_text)

# --- EXECUTION ---
if __name__ == "__main__":
    # Check for command line argument or default file
    import argparse
    parser = argparse.ArgumentParser(description='Ingest Hierarchical Data from Word Document')
    parser.add_argument('file', nargs='?', help='Path to the .docx file')
    args = parser.parse_args()

    file_path = args.file
    
    # If no file provided, ask user or look for default
    if not file_path:
        # Try to find a .docx in current directory
        docx_files = [f for f in os.listdir('.') if f.endswith('.docx') and not f.startswith('~$')]
        if docx_files:
            print(f"Found {len(docx_files)} .docx files: {docx_files}")
            file_path = docx_files[0]
            print(f"Using: {file_path}")
        else:
            print("No .docx file provided or found in directory.")
            print("Usage: python ingest_hierarchical.py <path_to_docx>")
            # Fallback to dummy data for testing if user confirms? 
            # For now, just exit or use the dummy data from before?
            # Let's keep the dummy data as a fallback for demonstration if strictly requested,
            # but the user wants to use *their* document.
            sys.exit(1)

    print(f"Reading file: {file_path}")
    try:
        raw_file_content = extract_text_from_docx(file_path)
        
        print("Parsing text...")
        parsed_sections = parse_hierarchical_text(raw_file_content)
        print(f"Found {len(parsed_sections)} sections.")
        
        if parsed_sections:
            print("Sample Section 1:", parsed_sections[0]['header_path'])
            confirm = input("Proceed with ingestion to Supabase? (y/n): ")
            if confirm.lower() == 'y':
                ingest_to_supabase(parsed_sections)
                print("Ingestion Complete!")
            else:
                print("Ingestion aborted.")
        else:
            print("No sections found. Check document formatting.")

    except Exception as e:
        print(f"Error processing file: {e}")

