#!/usr/bin/env python3
"""Test if Portfolio data is properly indexed and searchable in RAG."""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from scripts.connectors.rag_manager import RAGManager
from scripts.config import Config

def test_portfolio_rag():
    """Test Portfolio data in RAG."""
    rag = RAGManager()
    
    print("=== Testing Portfolio Data in RAG ===\n")
    print(f"Total documents in RAG: {rag.collection.count()}\n")
    
    # Test queries specific to portfolio content
    queries = [
        "What initiatives are in the portfolio?",
        "Show me the faye portfolio",
        "What projects are in Laura's portfolio?",
        "List all initiatives",
        "What is the API Gateway initiative?",
    ]
    
    for query in queries:
        print(f"\n📊 Query: '{query}'")
        print("-" * 70)
        context, sources = rag.get_context_for_query(query, max_tokens=3000)
        
        if context:
            print(f"✅ Found {len(sources)} relevant sources")
            
            # Check if any sources mention portfolio
            portfolio_sources = [s for s in sources if 'portfolio' in s.lower() or 'faye' in s.lower()]
            if portfolio_sources:
                print(f"🟣 Portfolio-related sources: {len(portfolio_sources)}")
                for src in portfolio_sources[:3]:
                    print(f"   - {src}")
            
            print(f"\nContext preview (first 400 chars):")
            preview = context[:400].replace('\n', ' ')
            print(f"{preview}...")
            
        else:
            print("❌ No relevant context found in RAG")
    
    print("\n" + "=" * 70)
    print("Searching RAG for 'faye-portfolio' specifically...")
    print("=" * 70)
    
    # Direct search for portfolio file
    context, sources = rag.get_context_for_query("faye-portfolio-Laura", max_tokens=5000)
    if context:
        print(f"✅ Found portfolio data! ({len(context)} chars)")
        print(f"Sources: {sources}")
        print(f"\nSample content:\n{context[:600]}")
    else:
        print("❌ Portfolio file NOT found in RAG index")
        print("\n⚠️  This means the portfolio was NOT automatically indexed after upload")
        print("    The file exists but is not searchable in AI Chat")

if __name__ == "__main__":
    test_portfolio_rag()
