#!/usr/bin/env python3
"""Test migration endpoint with sample localStorage data"""
import requests
import json

# Sample localStorage conversation data (what would be in the browser)
sample_conversations = [
    {
        "id": "conv_123456_test1",
        "title": "Test Conversation 1",
        "messages": [
            {
                "id": "1",
                "role": "system",
                "content": "Hello! How can I help?",
                "timestamp": "2025-11-13T19:00:00.000Z"
            },
            {
                "id": "2",
                "role": "user",
                "content": "Tell me about Jira issues",
                "timestamp": "2025-11-13T19:01:00.000Z"
            }
        ],
        "createdAt": "2025-11-13T19:00:00.000Z",
        "updatedAt": "2025-11-13T19:01:00.000Z"
    },
    {
        "id": "conv_123456_test2",
        "title": "Another Chat",
        "messages": [
            {
                "id": "1",
                "role": "system",
                "content": "Welcome!",
                "timestamp": "2025-11-13T18:00:00.000Z"
            }
        ],
        "createdAt": "2025-11-13T18:00:00.000Z",
        "updatedAt": "2025-11-13T18:00:00.000Z"
    }
]

# Test the migration endpoint
url = "http://localhost:8000/api/conversations/migrate"
payload = {"conversations": sample_conversations}

print("Testing migration endpoint with sample data...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...\n")

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
