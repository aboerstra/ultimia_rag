#!/usr/bin/env python3
"""Test hybrid search functionality."""
from scripts.connectors.rag_manager import RAGManager
from pathlib import Path

print("=== Testing Hybrid Search ===\n")
rag = RAGManager()
project_root = Path('.')

# Test 1: Search for exact issue ID
print("Test 1: Searching for 'MAXCOM-292'")
results = rag.search('MAXCOM-292', n_results=5, use_hybrid=True)
print(f"Found {len(results)} results\n")

for i, result in enumerate(results[:3], 1):
    print(f"Result {i}:")
    print(f"  Source: {result['metadata'].get('source')}")
    if result['metadata'].get('source') == 'jira':
        print(f"  Issue Key: {result['metadata'].get('key')}")
        print(f"  Summary: {result['metadata'].get('summary')}")
    elif result['metadata'].get('source') == 'clockify':
        print(f"  User: {result['metadata'].get('user_name')}")
    print(f"  Content preview: {result['content'][:150]}...")
    print()

# Test 2: Search without hybrid (semantic only)
print("\nTest 2: Searching for 'MAXCOM-292' (semantic only)")
results_semantic = rag.search('MAXCOM-292', n_results=5, use_hybrid=False)
print(f"Found {len(results_semantic)} results\n")

for i, result in enumerate(results_semantic[:2], 1):
    print(f"Result {i}:")
    print(f"  Source: {result['metadata'].get('source')}")
    if result['metadata'].get('source') == 'jira':
        print(f"  Issue Key: {result['metadata'].get('key')}")
    print()

# Test 3: Search for "Vinay Clockify" (should find time entries)  
print("\nTest 3: Searching for 'Vinay Vernekar Clockify'")
results_vinay = rag.search('Vinay Vernekar Clockify', n_results=3, use_hybrid=True)
print(f"Found {len(results_vinay)} results\n")

for i, result in enumerate(results_vinay, 1):
    print(f"Result {i}:")
    print(f"  Source: {result['metadata'].get('source')}")
    if 'MAXCOM-292' in result['content']:
        print(f"  ✓ Contains MAXCOM-292!")
    print()
