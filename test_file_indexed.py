#!/usr/bin/env python3
"""Test if a specific file is indexed in the RAG system."""

import sys
sys.path.insert(0, '/Users/adrianboerstra/projects/maximQBR/scripts')

from scripts.connectors.rag_manager import RAGManager
from pathlib import Path

def check_file_indexed(filename):
    """Check if a file is indexed in the RAG system."""
    try:
        rag = RAGManager()
        
        # Get collection stats
        doc_count = rag.collection.count()
        print(f"\n📊 Total documents in RAG index: {doc_count}")
        
        # Query for this specific file
        results = rag.collection.get(
            where={"source": {"$contains": filename}},
            limit=100
        )
        
        if results and results['ids']:
            print(f"\n✅ File '{filename}' IS indexed!")
            print(f"   Found {len(results['ids'])} chunks from this file")
            print(f"\n   Sample metadata from first chunk:")
            if results['metadatas']:
                import json
                print(json.dumps(results['metadatas'][0], indent=2))
            
            # Show a sample of content
            if results['documents']:
                print(f"\n   Sample content (first 200 chars):")
                print(f"   {results['documents'][0][:200]}...")
        else:
            print(f"\n❌ File '{filename}' is NOT indexed")
            print(f"\n   Searching for any files with 'faye' in the name...")
            
            # Try broader search
            faye_results = rag.collection.get(
                where={"source": {"$contains": "faye"}},
                limit=10
            )
            
            if faye_results and faye_results['ids']:
                print(f"   Found {len(faye_results['ids'])} documents with 'faye' in source")
                unique_sources = set()
                if faye_results['metadatas']:
                    for meta in faye_results['metadatas']:
                        if 'source' in meta:
                            unique_sources.add(meta['source'])
                
                print(f"\n   Files with 'faye' in name:")
                for source in sorted(unique_sources):
                    print(f"   - {source}")
            else:
                print(f"   No files with 'faye' found in index")
        
        return results and len(results['ids']) > 0
        
    except Exception as e:
        print(f"\n❌ Error checking index: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    filename = "faye-portfolio-Laura 1 agressive.json"
    print(f"🔍 Checking if '{filename}' is indexed in RAG system...")
    check_file_indexed(filename)
