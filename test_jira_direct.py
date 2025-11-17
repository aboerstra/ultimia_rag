#!/usr/bin/env python3
"""Direct test of Jira API to debug issue retrieval."""

from atlassian import Jira
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Get credentials from environment
JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')
PROJECT_KEY = 'MAXCOM'

print(f"Testing Jira connection to {JIRA_URL}")
print(f"Project: {PROJECT_KEY}")
print("-" * 60)

# Create client
client = Jira(
    url=JIRA_URL,
    username=JIRA_EMAIL,
    password=JIRA_TOKEN,
    cloud=True,
    api_version='3'
)

# Test 1: Get project info
print("\n1. Testing project access...")
try:
    projects = client.projects(included_archived=False)
    maxcom_project = [p for p in projects if p['key'] == PROJECT_KEY]
    if maxcom_project:
        print(f"✅ Found project: {maxcom_project[0]['name']} (ID: {maxcom_project[0]['id']})")
    else:
        print(f"❌ Project {PROJECT_KEY} not found")
        print(f"Available projects: {[p['key'] for p in projects[:10]]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Try various JQL queries
print("\n2. Testing JQL queries...")

# Calculate date 6 months ago
start_date = datetime.now() - timedelta(days=180)
date_str = start_date.strftime('%Y-%m-%d')

queries = [
    f"project = {PROJECT_KEY}",
    f"project = {PROJECT_KEY} AND updated >= '{date_str}'",
    f"project = {PROJECT_KEY} AND created >= '{date_str}'",
    f"project = {PROJECT_KEY} ORDER BY updated DESC",
]

for jql in queries:
    print(f"\nTesting: {jql}")
    try:
        result = client.jql(jql, limit=5)
        count = result.get('total', 0)
        print(f"  ✅ Found {count} issues")
        if count > 0:
            print(f"  Sample issues:")
            for issue in result.get('issues', [])[:3]:
                print(f"    - {issue['key']}: {issue['fields'].get('summary', 'N/A')[:50]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")
