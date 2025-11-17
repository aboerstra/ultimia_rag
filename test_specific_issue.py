#!/usr/bin/env python3
"""Test accessing specific MAXCOM-431 issue."""

import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
import json

load_dotenv()

JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
headers = {'Accept': 'application/json'}

print("Testing access to specific issue: MAXCOM-431")
print("=" * 60)

# Try to get the specific issue
issue_key = "MAXCOM-431"
url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}"

try:
    response = requests.get(url, auth=auth, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        issue = response.json()
        print(f"✅ Successfully retrieved issue!")
        print(f"\nKey: {issue['key']}")
        print(f"Summary: {issue['fields'].get('summary', 'N/A')}")
        print(f"Status: {issue['fields'].get('status', {}).get('name', 'N/A')}")
        print(f"Created: {issue['fields'].get('created', 'N/A')}")
        print(f"Updated: {issue['fields'].get('updated', 'N/A')}")
        print(f"Project: {issue['fields'].get('project', {}).get('key', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text[:300]}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 60)
print("If this works but JQL queries return 0:")
print("  → The issue exists but isn't indexed in JQL search")
print("  → This is a Jira Server/Cloud indexing issue")
print("=" * 60)
