#!/usr/bin/env python3
"""Test calling the NEW Jira v3 JQL search API."""

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Get credentials
JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')
PROJECT_KEY = 'MAXCOM'

print(f"Testing NEW Jira v3 /search/jql API to {JIRA_URL}")
print(f"Project: {PROJECT_KEY}")
print("-" * 60)

# Setup auth
auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Calculate date
start_date = datetime.now() - timedelta(days=180)
date_str = start_date.strftime('%Y-%m-%d')

# Test JQL queries using NEW v3 /search/jql endpoint
queries = [
    f"project = {PROJECT_KEY}",
    f"project = {PROJECT_KEY} AND updated >= '{date_str}'",
    f"project = {PROJECT_KEY} ORDER BY created DESC",  # No date filter
]

for jql in queries:
    print(f"\nTesting: {jql}")
    
    # Use NEW v3 /search/jql endpoint (POST request with body)
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    payload = {
        'jql': jql,
        'maxResults': 5,
        'fields': ['summary', 'status', 'created', 'updated']
    }
    
    try:
        response = requests.post(url, headers=headers, auth=auth, json=payload)
        response.raise_for_status()
        
        data = response.json()
        total = data.get('total', 0)
        issues = data.get('values', [])  # Note: uses 'values' not 'issues'
        
        print(f"  ✅ Found {total} total issues")
        if issues:
            print(f"  Sample issues:")
            for issue in issues[:3]:
                summary = issue.get('fields', {}).get('summary', 'N/A')
                print(f"    - {issue['key']}: {summary[:60]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")
