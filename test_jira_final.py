#!/usr/bin/env python3
"""Comprehensive Jira diagnostic test."""

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

print("=" * 70)
print("COMPREHENSIVE JIRA DIAGNOSTIC TEST")
print("=" * 70)

# Test MAXCOM specifically
print("\n🔍 Testing MAXCOM Project:")
print("-" * 70)

# 1. Get project info
try:
    response = requests.get(f"{JIRA_URL}/rest/api/3/project/MAXCOM", auth=auth, headers=headers)
    response.raise_for_status()
    project = response.json()
    print(f"✅ Project found: {project['name']} (ID: {project['id']})")
except Exception as e:
    print(f"❌ Cannot access project: {e}")
    exit(1)

# 2. Try various JQL queries on MAXCOM
test_queries = [
    ("All issues", "project = MAXCOM"),
    ("Last 6 months (updated)", f"project = MAXCOM AND updated >= '{(datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')}'"),
    ("Last 12 months (updated)", f"project = MAXCOM AND updated >= '{(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')}'"),
    ("All time", "project = MAXCOM ORDER BY created ASC"),
]

url = f"{JIRA_URL}/rest/api/3/search/jql"

for name, jql in test_queries:
    print(f"\n📊 {name}:")
    print(f"   JQL: {jql}")
    
    payload = {
        'jql': jql,
        'maxResults': 3,
        'fields': ['summary', 'status', 'created', 'updated', 'issuetype']
    }
    
    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        total = data.get('total', 0)
        issues = data.get('values', [])
        
        if total == 0:
            print(f"   ⚠️  Result: 0 issues found")
        else:
            print(f"   ✅ Result: {total} issues found")
            for issue in issues:
                itype = issue.get('fields', {}).get('issuetype', {}).get('name', 'N/A')
                summary = issue.get('fields', {}).get('summary', 'N/A')[:50]
                created = issue.get('fields', {}).get('created', 'N/A')[:10]
                print(f"      • {issue['key']} ({itype}): {summary} [created: {created}]")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# 3. Check if user has browse permission
print(f"\n🔐 Permission Check:")
try:
    response = requests.get(
        f"{JIRA_URL}/rest/api/3/mypermissions?projectKey=MAXCOM",
        auth=auth,
        headers=headers
    )
    response.raise_for_status()
    perms = response.json()
    browse = perms.get('permissions', {}).get('BROWSE_PROJECTS', {})
    print(f"   BROWSE_PROJECTS: {browse.get('havePermission', False)}")
except Exception as e:
    print(f"   ❌ Cannot check permissions: {e}")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("-" * 70)
print("If all queries show 0 issues:")
print("  • The MAXCOM project has no issues visible to your API token")
print("  • Check if issues exist in Jira web UI")
print("  • Verify API token has correct permissions")
print("=" * 70)
