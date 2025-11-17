#!/usr/bin/env python3
"""Test Jira search using GET with query parameters instead of POST."""

import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
headers = {'Accept': 'application/json'}

print("Testing Jira /search endpoint with GET")
print("=" * 60)

# Try the old /search endpoint with GET (not POST to /search/jql)
url = f"{JIRA_URL}/rest/api/3/search"
params = {
    'jql': 'project = MAXCOM',
    'maxResults': 5
}

print(f"\nURL: {url}")
print(f"JQL: {params['jql']}")
print("-" * 60)

try:
    response = requests.get(url, auth=auth, headers=headers, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        total = data.get('total', 0)
        issues = data.get('issues', [])
        
        print(f"✅ Success! Found {total} issues")
        if issues:
            print("\nSample issues:")
            for issue in issues[:5]:
                summary = issue['fields'].get('summary', 'N/A')[:50]
                print(f"  • {issue['key']}: {summary}")
        else:
            print("  (but no issues returned)")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text[:300]}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 60)
