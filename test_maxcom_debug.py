#!/usr/bin/env python3
"""Deep diagnostic test for MAXCOM project issues."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from connectors.jira_client import JiraClient

print("=" * 80)
print("MAXCOM PROJECT DIAGNOSTIC TEST")
print("=" * 80)

client = JiraClient()

# Test 1: Verify MAXCOM project exists
print("\n1. Verifying MAXCOM project exists...")
try:
    import requests
    url = f"{client.base_url}/rest/api/3/project/MAXCOM"
    response = requests.get(url, auth=client.auth, headers=client.headers)
    response.raise_for_status()
    project = response.json()
    print(f"✅ Project found: {project['name']}")
    print(f"   ID: {project['id']}")
    print(f"   Key: {project['key']}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 2: Try getting issues WITHOUT date filter
print("\n2. Testing: Get ALL MAXCOM issues (no date filter)...")
try:
    url = f"{client.base_url}/rest/api/3/search/jql"
    payload = {
        'jql': 'project = MAXCOM ORDER BY created DESC',
        'maxResults': 10,
        'fields': ['summary', 'created', 'updated', 'status']
    }
    response = requests.post(url, auth=client.auth, headers=client.headers, json=payload)
    response.raise_for_status()
    result = response.json()
    total = result.get('total', 0)
    issues = result.get('values', [])
    
    print(f"   Total issues in MAXCOM: {total}")
    if issues:
        print(f"   Sample issues (showing {len(issues)}):")
        for issue in issues[:5]:
            created = issue.get('fields', {}).get('created', 'N/A')[:10]
            updated = issue.get('fields', {}).get('updated', 'N/A')[:10]
            summary = issue.get('fields', {}).get('summary', 'N/A')[:60]
            print(f"   • {issue['key']}: {summary}")
            print(f"     Created: {created}, Updated: {updated}")
    else:
        print("   ⚠️  No issues found even without date filter!")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Try with 1 year date filter
print("\n3. Testing: Last 12 months (updated)...")
try:
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    url = f"{client.base_url}/rest/api/3/search/jql"
    payload = {
        'jql': f"project = MAXCOM AND updated >= '{one_year_ago}' ORDER BY updated DESC",
        'maxResults': 10,
        'fields': ['summary', 'created', 'updated', 'status']
    }
    response = requests.post(url, auth=client.auth, headers=client.headers, json=payload)
    response.raise_for_status()
    result = response.json()
    total = result.get('total', 0)
    issues = result.get('values', [])
    
    print(f"   Issues updated in last 12 months: {total}")
    if issues:
        for issue in issues[:3]:
            updated = issue.get('fields', {}).get('updated', 'N/A')[:10]
            summary = issue.get('fields', {}).get('summary', 'N/A')[:50]
            print(f"   • {issue['key']}: {summary} (Updated: {updated})")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Try with 6 months date filter (what the app uses)
print("\n4. Testing: Last 6 months (updated) - SAME AS APP...")
try:
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    url = f"{client.base_url}/rest/api/3/search/jql"
    payload = {
        'jql': f"project = MAXCOM AND updated >= '{six_months_ago}' ORDER BY updated DESC",
        'maxResults': 10,
        'fields': ['summary', 'created', 'updated', 'status']
    }
    response = requests.post(url, auth=client.auth, headers=client.headers, json=payload)
    response.raise_for_status()
    result = response.json()
    total = result.get('total', 0)
    issues = result.get('values', [])
    
    print(f"   Issues updated in last 6 months: {total}")
    print(f"   Date filter: {six_months_ago}")
    if issues:
        for issue in issues[:3]:
            updated = issue.get('fields', {}).get('updated', 'N/A')[:10]
            summary = issue.get('fields', {}).get('summary', 'N/A')[:50]
            print(f"   • {issue['key']}: {summary} (Updated: {updated})")
    else:
        print("   ⚠️  This is why the app shows 0 issues!")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Use the actual client method
print("\n5. Testing: Using JiraClient.get_issues() method...")
try:
    issues = client.get_issues(project_key='MAXCOM', months_back=6, max_results=10)
    print(f"   Issues from client method: {len(issues)}")
    if issues:
        for issue in issues[:3]:
            print(f"   • {issue['key']}: {issue['summary'][:50]}")
            print(f"     Updated: {issue['updated'][:10]}")
    else:
        print("   ⚠️  Client method also returns 0 issues")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Check most recent issue
print("\n6. Finding most recently updated issue...")
try:
    url = f"{client.base_url}/rest/api/3/search/jql"
    payload = {
        'jql': 'project = MAXCOM ORDER BY updated DESC',
        'maxResults': 1,
        'fields': ['summary', 'created', 'updated', 'status']
    }
    response = requests.post(url, auth=client.auth, headers=client.headers, json=payload)
    response.raise_for_status()
    result = response.json()
    issues = result.get('values', [])
    
    if issues:
        issue = issues[0]
        updated = issue.get('fields', {}).get('updated', 'N/A')
        print(f"   Most recent issue: {issue['key']}")
        print(f"   Last updated: {updated}")
        print(f"   Summary: {issue.get('fields', {}).get('summary', 'N/A')}")
        
        # Calculate days ago
        updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00'))
        days_ago = (datetime.now(updated_date.tzinfo) - updated_date).days
        print(f"   Days since last update: {days_ago}")
        
        if days_ago > 180:
            print(f"   ⚠️  FOUND THE PROBLEM: Last update was {days_ago} days ago (>{180} days)")
            print(f"   💡 SOLUTION: Increase months_back parameter or update a ticket in MAXCOM")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
