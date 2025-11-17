#!/usr/bin/env python3
"""Test Gemini 2.5 Pro with function calling."""
import os
from scripts.connectors.gemini_client import GeminiClient
from dotenv import load_dotenv

load_dotenv()

# Initialize
gemini = GeminiClient(os.getenv('GEMINI_API_KEY'))

# Test without tools first
print("Testing basic text generation...")
try:
    result = gemini.generate_text("What is 2+2?")
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test with tools
print("\nTesting with tools...")
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stats",
            "description": "Get statistics about data",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

try:
    result = gemini.chat_with_tools("How many issues?", tools)
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
