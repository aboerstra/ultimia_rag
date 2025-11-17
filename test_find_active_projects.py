#!/usr/bin/env python3
"""Find which projects actually have issues."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from connectors.jira_client import JiraClient
import requests

print("=" * 80)
print("FINDING PROJECTS WITH ISSUES")
print("=" * 80)

client = JiraClient()

# Get all projects
print("\n1. Getting all projects...")
projects = client.get_all_projects()
print(f"   Found {len(projects)} total projects")

# Check each project for issues
print("\n2. Checking which projects have issues...")
projects_with_issues = []

for i, project in enumerate(projects[:50], 1):  # Check first 50 to avoid rate limits
    key = project['key']
    
    try:
        url = f"{client.base_url}/rest/api/3/search/jql"
        payload = {
            'jql': f'project = {key}',
            'maxResults': 1,
            'fields': ['summary']
        }
        response = requests.post(url, auth=client.auth, headers=client.headers, json=payload)
        response.raise_for_status()
        result = response.json()
        total = result.get('total', 0)
        
        if total > 0:
            projects_with_issues.append({
                'key': key,
                'name': project['name'],
                'issue_count': total
            })
            print(f"   ✅ {key}: {project['name'][:40]:40} ({total} issues)")
        
        # Show progress every 10 projects
        if i % 10 == 0:
            print(f"   ... checked {i} projects so far")
            
    except Exception as e:
        print(f"   ⚠️  {key}: Error - {e}")
        continue

print(f"\n" + "=" * 80)
print(f"SUMMARY: Found {len(projects_with_issues)} projects with issues")
print("=" * 80)

if projects_with_issues:
    print("\nProjects with issues (sorted by count):")
    projects_with_issues.sort(key=lambda x: x['issue_count'], reverse=True)
    for p in projects_with_issues[:20]:
        print(f"  • {p['key']:10} - {p['name'][:50]:50} ({p['issue_count']:,} issues)")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
print("The MAXCOM project exists but has 0 issues.")
print("Your issues may be in a different project.")
print("Check the list above to find which project contains your actual work.")
print("=" * 80)
