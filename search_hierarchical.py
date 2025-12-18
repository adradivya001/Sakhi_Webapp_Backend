from typing import List, Dict, Any
from supabase_client import supabase_rpc
from rag import generate_embedding

def hierarchical_rag_query(user_question: str, match_threshold: float = 0.3, match_count: int = 4) -> List[Dict[str, Any]]:
    """
    Performs a hierarchical search:
    1. Embeds the user question.
    2. Searches 'section_chunks' for matches (Hierarchical) -> Primary Source for Answer.
    3. Searches 'faq' table for matches (FAQ) -> Primary Source for YouTube Link.
    4. Merges and returns results.
    """
    print(f"Querying: {user_question}...")
    
    # 1. Embed user query
    query_vector = generate_embedding(user_question)
    
    # 2. Call Supabase RPC functions
    params = {
        "query_embedding": query_vector,
        "match_threshold": match_threshold,
        "match_count": match_count
    }
    
    merged_results = []

    # A. Search Hierarchical Docs (Primary Content)
    try:
        doc_results = supabase_rpc("hierarchical_search", params)
        if doc_results:
            for item in doc_results:
                item["source_type"] = "DOCUMENT"
                merged_results.append(item)
    except Exception as e:
        print(f"Hierarchical search failed: {e}")

    # B. Search FAQ (For YouTube Link)
    # We only need the top match to find a relevant video
    # match_faq likely only accepts query_embedding and match_count
    faq_params = {
        "query_embedding": query_vector,
        "match_count": 1
    }
    
    try:
        faq_results = supabase_rpc("match_faq", faq_params)
        if faq_results:
            for item in faq_results:
                # Only add if it has a YouTube link or if we have no other results
                if item.get("youtube_link") or not merged_results:
                    item["source_type"] = "FAQ"
                    # Ensure infographic_url is preserved if present
                    if "infographic_url" not in item:
                        item["infographic_url"] = None 

                    merged_results.append(item)
    except Exception as e:
        print(f"FAQ search failed: {e}")
    
    return merged_results

def format_hierarchical_context(results: List[Dict[str, Any]]) -> str:
    """
    Formats the raw results into a context string for the LLM.
    Prioritizes Document content for the answer.
    Appends YouTube link if found in FAQ results.
    """
    if not results:
        return "No relevant information found."

    doc_context = ""
    youtube_link_found = None

    for match in results:
        source_type = match.get("source_type", "UNKNOWN")
        
        if source_type == "FAQ":
            # Extract YouTube link if available
            link = match.get("youtube_link")
            if link:
                youtube_link_found = link
            
            # If we have no doc context yet, we might use the FAQ answer as fallback
            # But primarily we want the link.
            if not doc_context: 
                 doc_context += f"FAQ Answer: {match.get('answer', '')}\n"

        else:
            # Document source
            path = match.get("header_path", "Unknown Path")
            content = match.get("section_content", "")
            similarity = match.get("similarity", 0)
            
            doc_context += f"""
--- SOURCE: DOCUMENT (Relevance: {similarity:.2f}) ---
Path: {path}
Content: {content}
--------------------------------------------------
"""

    final_context = doc_context
    if youtube_link_found:
        final_context += f"\n\n*** RELEVANT VIDEO ***\nYouTube: {youtube_link_found}\n"
        
    return final_context

# --- TEST ---
if __name__ == "__main__":
    q = "How much does IVF cost?"
    results = hierarchical_rag_query(q)
    context = format_hierarchical_context(results)
    
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write(context)
    print("Results written to debug_output.txt")

