#!/usr/bin/env python3
"""Test what the Jira API token can actually access."""

import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

print("Testing Jira API Token Permissions")
print("=" * 60)

# Test 1: Get current user info
print("\n1. Current User Info:")
try:
    response = requests.get(f"{JIRA_URL}/rest/api/3/myself", auth=auth, headers=headers)
    response.raise_for_status()
    user = response.json()
    print(f"  ✅ Logged in as: {user.get('displayName')} ({user.get('emailAddress')})")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 2: List all accessible projects
print("\n2. Accessible Projects:")
try:
    response = requests.get(f"{JIRA_URL}/rest/api/3/project", auth=auth, headers=headers)
    response.raise_for_status()
    projects = response.json()
    print(f"  ✅ Found {len(projects)} projects:")
    for p in projects[:10]:
        print(f"     - {p['key']}: {p['name']}")
    if len(projects) > 10:
        print(f"     ... and {len(projects) - 10} more")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 3: Search for ANY issues (no project filter)
print("\n3. All Accessible Issues (any project):")
try:
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    payload = {'jql': 'ORDER BY created DESC', 'maxResults': 5}
    response = requests.post(url, auth=auth, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"  ❌ Status: {response.status_code}")
        print(f"  ❌ Response: {response.text[:200]}")
    response.raise_for_status()
    data = response.json()
    total = data.get('total', 0)
    issues = data.get('values', [])
    print(f"  ✅ Found {total} total issues across all projects")
    if issues:
        print(f"  Sample issues:")
        for issue in issues:
            proj = issue.get('fields', {}).get('project', {}).get('key', 'N/A')
            summary = issue.get('fields', {}).get('summary', 'N/A')[:40]
            print(f"     - {issue['key']} ({proj}): {summary}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 4: Get specific project permissions
print("\n4. MAXCOM Project Permissions:")
try:
    response = requests.get(f"{JIRA_URL}/rest/api/3/project/MAXCOM", auth=auth, headers=headers)
    response.raise_for_status()
    project = response.json()
    print(f"  ✅ Project: {project['name']}")
    print(f"     ID: {project['id']}")
    print(f"     Key: {project['key']}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")
