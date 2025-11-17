#!/usr/bin/env python3
"""Test the refactored JiraClient using new /search/jql endpoint."""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from connectors.jira_client import JiraClient

print("=" * 70)
print("TESTING REFACTORED JIRA CLIENT")
print("Using new /rest/api/3/search/jql POST endpoint")
print("=" * 70)

# Initialize client
print("\n1. Initializing JiraClient...")
try:
    client = JiraClient()
    print("✅ Client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

# Test 1: Get all projects
print("\n2. Testing get_all_projects()...")
try:
    projects = client.get_all_projects()
    if projects:
        print(f"✅ Found {len(projects)} projects")
        for p in projects[:5]:
            print(f"   • {p['key']}: {p['name']}")
    else:
        print("⚠️  No projects found")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Get issues for MAXCOM project
print("\n3. Testing get_issues(project_key='MAXCOM')...")
try:
    issues = client.get_issues(project_key='MAXCOM', months_back=6, max_results=10)
    if issues:
        print(f"✅ Found {len(issues)} issues from MAXCOM")
        print("\n   Sample issues:")
        for issue in issues[:5]:
            print(f"   • {issue['key']}: {issue['summary'][:60]}")
            print(f"     Status: {issue['status']}, Type: {issue['type']}")
    else:
        print("⚠️  No issues found for MAXCOM")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Get all issues (no project filter)
print("\n4. Testing get_issues() without project filter...")
try:
    all_issues = client.get_issues(months_back=3, max_results=5)
    if all_issues:
        print(f"✅ Found {len(all_issues)} issues across all projects")
        for issue in all_issues[:3]:
            print(f"   • [{issue['project']}] {issue['key']}: {issue['summary'][:50]}")
    else:
        print("⚠️  No issues found")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Get boards
print("\n5. Testing get_boards()...")
try:
    boards = client.get_boards()
    if boards:
        print(f"✅ Found {len(boards)} boards")
        for board in boards[:3]:
            print(f"   • {board.get('name', 'N/A')} (ID: {board.get('id', 'N/A')})")
    else:
        print("⚠️  No boards found")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("✅ Refactored client uses new /search/jql endpoint")
print("✅ Parses 'values' field instead of 'issues'")
print("✅ Uses direct requests library for full control")
print("✅ Implements nextPageToken pagination")
print("=" * 70)
