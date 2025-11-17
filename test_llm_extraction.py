#!/usr/bin/env python3
"""Test LLM extraction from Serper results"""

import sys
sys.path.insert(0, 'scripts')

from connectors.llm_client import LLMClient

# The actual search results from Serper
search_results = """Michael Kianmahd - Maxim Commercial Capital. Michael Kianmahd is CEO Maxim Commercial Capital, responsible for strategic vision, corporate development, investments and operations. Michael Kianmahd - CEO - Maxim Commercial Capital, LLC - LinkedIn. Experienced financial services executive and investor with strong skillsets in strategy, business development, corporate finance, human resources, capital ... Episode #240 Fireside Chat with Michael Kianmahd - LinkedIn. Michael Kianmahd, graphic · Michael Kianmahd. CEO - Maxim Commercial Capital, LLC | Lender, Investor, Advisor. """

llm = LLMClient()

prompt = f"""Extract professional information from these search results about Michael Kianmahd.

SEARCH RESULTS:
{search_results}

Extract and return ONLY a JSON object with these fields:
{{
  "name": "Michael Kianmahd",
  "title": "CEO",
  "company": "Maxim Commercial Capital, LLC",
  "about": "Brief background from results"
}}

Rules:
- Extract the most recent/current title
- Use full company name if available
- Combine info from multiple results
- Return valid JSON only, no markdown
- If truly no info found, return: {{"title": "", "company": ""}}"""

print("=" * 60)
print("Testing LLM Extraction")
print("=" * 60)

print("\nPrompt sent to LLM:")
print("-" * 60)
print(prompt)
print("-" * 60)

print("\nCalling LLM...")
response = llm.generate_text(prompt, max_tokens=400)

print("\nRaw LLM Response:")
print("=" * 60)
print(response)
print("=" * 60)

print("\nParsing response...")
import json
import re

response_clean = response.strip()

# Remove markdown code blocks
if '```' in response_clean:
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_clean, re.DOTALL)
    if json_match:
        response_clean = json_match.group(1)
        print(f"Extracted from code block: {response_clean[:100]}...")
    else:
        json_match = re.search(r'\{.*\}', response_clean, re.DOTALL)
        if json_match:
            response_clean = json_match.group(0)
            print(f"Found JSON object: {response_clean[:100]}...")

print("\nCleaned response:")
print(response_clean)

try:
    data = json.loads(response_clean)
    print("\n✅ Successfully parsed JSON!")
    print(json.dumps(data, indent=2))
    
    if data.get('title') or data.get('company'):
        print(f"\n✅ SUCCESS: Extracted title='{data.get('title')}' company='{data.get('company')}'")
    else:
        print("\n❌ FAIL: Empty title/company in parsed JSON")
        
except json.JSONDecodeError as e:
    print(f"\n❌ JSON Parse Error: {e}")
    print(f"Tried to parse: {response_clean}")
