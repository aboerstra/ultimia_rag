#!/usr/bin/env python3
"""Test Clockify client with MAXCOM projects."""
import sys
sys.path.insert(0, 'scripts')

from connectors.clockify_client import ClockifyClient
from datetime import datetime, timedelta

print("=" * 60)
print("TESTING CLOCKIFY CLIENT - MAXCOM PROJECTS")
print("=" * 60)

# Initialize client
client = ClockifyClient()

# MAXCOM project IDs from config
MAXCOM_PROJECTS = [
    "688a4bb2182ca836296a86b3",  # MAXCOM-020
    "688a4c4c182ca836296a899c",  # MAXCOM-021
    "688a4ce02fcd5d146c6cfa09",  # MAXCOM-022
    "688a4d532fcd5d146c6cfed5"   # MAXCOM-023
]

print(f"\n1. Testing workspace connection...")
client.set_workspace()
print(f"   ✓ Connected to workspace: {client.workspace_id}")

print(f"\n2. Fetching MAXCOM projects by client ID...")
projects = client.get_projects(client_id="6089c2a542687c75f1cf4d64")
print(f"   ✓ Found {len(projects)} MAXCOM projects:")
for p in projects:
    print(f"     - {p['name']}")

print(f"\n3. Fetching time entries for MAXCOM projects (last 6 months)...")
start_date = datetime.now() - timedelta(days=180)
end_date = datetime.now()

entries = client.get_time_entries(
    start_date=start_date,
    end_date=end_date,
    project_ids=MAXCOM_PROJECTS
)

print(f"\n4. RESULTS:")
print(f"   Total entries: {len(entries)}")

if entries:
    # Group by user
    user_hours = {}
    for entry in entries:
        user = entry.get('user_name', 'Unknown')
        if user not in user_hours:
            user_hours[user] = 0
        user_hours[user] += entry['hours']
    
    print(f"\n   Hours by user:")
    for user, hours in sorted(user_hours.items(), key=lambda x: x[1], reverse=True):
        print(f"     {user}: {hours:.2f} hrs")
    
    print(f"\n   Total hours: {sum(user_hours.values()):.2f}")
    
    # Group by project
    project_hours = {}
    for entry in entries:
        project = entry.get('project_name', 'Unknown')
        if project not in project_hours:
            project_hours[project] = 0
        project_hours[project] += entry['hours']
    
    print(f"\n   Hours by project:")
    for project, hours in sorted(project_hours.items(), key=lambda x: x[1], reverse=True):
        print(f"     {project}: {hours:.2f} hrs")
    
    print(f"\n   Sample entries:")
    for i, entry in enumerate(entries[:5], 1):
        print(f"     {i}. {entry['user_name']}: {entry['hours']:.2f}h on {entry['project_name']}")
        print(f"        {entry['description'][:60]}...")
else:
    print("   ⚠️  No entries found!")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
