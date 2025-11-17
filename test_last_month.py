#!/usr/bin/env python3
"""Test Clockify for just last month."""
import sys
sys.path.insert(0, 'scripts')

from connectors.clockify_client import ClockifyClient
from datetime import datetime, timedelta

print("=" * 60)
print("TESTING LAST MONTH ONLY")
print("=" * 60)

client = ClockifyClient()
client.set_workspace()

MAXCOM_PROJECTS = [
    "688a4bb2182ca836296a86b3",  # MAXCOM-020
    "688a4c4c182ca836296a899c",  # MAXCOM-021
    "688a4ce02fcd5d146c6cfa09",  # MAXCOM-022
    "688a4d532fcd5d146c6cfed5"   # MAXCOM-023
]

# Last month: October 1 - October 31, 2025
start = datetime(2025, 10, 1)
end = datetime(2025, 10, 31, 23, 59, 59)

print(f"\nDate Range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
print(f"Projects: 4 MAXCOM projects")

entries = client.get_time_entries(
    start_date=start,
    end_date=end,
    project_ids=MAXCOM_PROJECTS,
    limit=1000
)

print(f"\n{'='*60}")
print(f"RESULTS FOR OCTOBER 2025")
print(f"{'='*60}")
print(f"\nTotal entries: {len(entries)}")

if entries:
    # Group by user
    user_hours = {}
    user_entries = {}
    for entry in entries:
        user = entry.get('user_name', 'Unknown')
        if user not in user_hours:
            user_hours[user] = 0
            user_entries[user] = 0
        user_hours[user] += entry['hours']
        user_entries[user] += 1
    
    print(f"\nTeam Members: {len(user_hours)}")
    print(f"\nHours by user:")
    for user, hours in sorted(user_hours.items(), key=lambda x: x[1], reverse=True):
        count = user_entries[user]
        print(f"  {user}: {hours:.2f} hrs ({count} entries)")
    
    print(f"\nTOTAL HOURS: {sum(user_hours.values()):.2f}")
    
    # Group by project
    project_hours = {}
    for entry in entries:
        project = entry.get('project_name', 'Unknown')
        if project not in project_hours:
            project_hours[project] = 0
        project_hours[project] += entry['hours']
    
    print(f"\nHours by project:")
    for project, hours in sorted(project_hours.items(), key=lambda x: x[1], reverse=True):
        print(f"  {project}: {hours:.2f} hrs")
else:
    print("\n⚠️  No MAXCOM entries found for October 2025")

print(f"\n{'='*60}")
