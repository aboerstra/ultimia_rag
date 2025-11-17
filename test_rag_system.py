#!/usr/bin/env python3
"""Test RAG (Retrieval Augmented Generation) system."""
import requests
import time

BASE_URL = "http://localhost:8000"

print("🧪 Testing RAG System...\n")

# 1. Check RAG status (before indexing)
print("1️⃣ Checking RAG status (before indexing)...")
response = requests.get(f"{BASE_URL}/api/rag/status")
print(f"Status: {response.json()}")
print()

# 2. Trigger indexing
print("2️⃣ Triggering knowledge base indexing...")
response = requests.post(f"{BASE_URL}/api/rag/index")
print(f"Response: {response.json()}")
print("⏳ Waiting 10 seconds for indexing to complete...")
time.sleep(10)
print()

# 3. Check RAG status (after indexing)
print("3️⃣ Checking RAG status (after indexing)...")
response = requests.get(f"{BASE_URL}/api/rag/status")
status = response.json()
print(f"Status: {status}")
print(f"✅ Documents indexed: {status.get('document_count', 0)}")
print()

# 4. Test semantic search via chat
print("4️⃣ Testing semantic search with AI chat...")
test_question = "What are the main topics discussed in meetings?"
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={"question": test_question}
)
result = response.json()
print(f"Question: {test_question}")
print(f"Sources used: {result.get('sources_used', [])}")
print(f"Answer preview: {result.get('answer', '')[:200]}...")
print()

print("✅ RAG system test complete!")
