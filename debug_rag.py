import os
import sys

# Ensure modules can be imported
sys.path.append(os.getcwd())

from search_hierarchical import hierarchical_rag_query

def test_query():
    query = "What is the cost of IVF?"
    with open("debug_output_utf8.txt", "w", encoding="utf-8") as f:
        f.write(f"Testing query: '{query}'\n")
        
        results = hierarchical_rag_query(query)
        
        f.write("\n--- Raw Results ---\n")
        for i, res in enumerate(results):
            f.write(f"Result {i+1}:\n")
            f.write(f"  Source Type: {res.get('source_type')}\n")
            f.write(f"  YouTube Link: {res.get('youtube_link')}\n")
            f.write(f"  Infographic URL: {res.get('infographic_url')}\n")
            f.write(f"  Follow-up Questions: {res.get('follow_up_questions')}\n")
            f.write(f"  Keys present: {list(res.keys())}\n")
            f.write("-" * 20 + "\n")
    print("Done writing to debug_output_utf8.txt")

if __name__ == "__main__":
    test_query()
