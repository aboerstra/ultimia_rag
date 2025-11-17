#!/usr/bin/env python3
"""Test Clockify RAG integration in AI chat after fix."""

import requests
import json

# Test the chat endpoint
API_URL = "http://localhost:8000/api/chat"

print("🧪 Testing Clockify RAG Integration Fix\n")

# Test query about Clockify
test_query = "How many hours were tracked for MAXCOM projects in Clockify?"

print(f"Question: {test_query}\n")

response = requests.post(
    API_URL,
    json={
        "question": test_query,
        "conversation_history": [],
        "use_general_knowledge": False,
        "use_web_search": False
    }
)

if response.status_code == 200:
    data = response.json()
    
    print("=" * 60)
    print("RESPONSE:")
    print("=" * 60)
    print(f"\nAnswer:\n{data.get('answer', 'No answer')}\n")
    
    print("=" * 60)
    print("METADATA:")
    print("=" * 60)
    print(f"Sources Used: {data.get('sources_used', [])}")
    print(f"Tools Called: {data.get('tools_used', [])}")
    
    if data.get('web_sources'):
        print(f"Web Sources: {data.get('web_sources', [])}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    
    # Verify the fix worked
    tools_used = data.get('tools_used', [])
    sources_used = data.get('sources_used', [])
    answer = data.get('answer', '').lower()
    
    checks = {
        "Tools were called": len(tools_used) > 0,
        "search_rag or get_stats used": any(t in tools_used for t in ['search_rag', 'get_stats']),
        "Sources include Clockify or Semantic Search": any(s in ['Clockify', 'Semantic Search', 'Direct Query'] for s in sources_used),
        "Answer mentions hours or numbers": any(word in answer for word in ['hour', 'hours', '111', '135', '101', '114', '461']),
        "Answer does NOT say 'no access'": 'no access' not in answer and 'cannot access' not in answer
    }
    
    all_passed = all(checks.values())
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ FIX VERIFIED: Clockify RAG integration working!")
    else:
        print("❌ FIX NOT WORKING: Some checks failed")
    print("=" * 60)
    
else:
    print(f"❌ Error: HTTP {response.status_code}")
    print(response.text)
