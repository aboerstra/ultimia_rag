#!/usr/bin/env python3
"""Test date range to find all MAXCOM entries."""
import sys
sys.path.insert(0, 'scripts')

from connectors.clockify_client import ClockifyClient
from datetime import datetime, timedelta

print("=" * 60)
print("TESTING DIFFERENT DATE RANGES")
print("=" * 60)

client = ClockifyClient()
client.set_workspace()

MAXCOM_PROJECTS = [
    "688a4bb2182ca836296a86b3",  # MAXCOM-020
    "688a4c4c182ca836296a899c",  # MAXCOM-021
    "688a4ce02fcd5d146c6cfa09",  # MAXCOM-022
    "688a4d532fcd5d146c6cfed5"   # MAXCOM-023
]

# Test 1: Last 12 months
print("\n1. Testing LAST 12 MONTHS...")
start = datetime.now() - timedelta(days=365)
end = datetime.now()
print(f"   Range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")

entries = client.get_time_entries(
    start_date=start,
    end_date=end,
    project_ids=MAXCOM_PROJECTS,
    limit=5000  # Increase limit
)
print(f"   Result: {len(entries)} entries")

if entries:
    user_hours = {}
    for entry in entries:
        user = entry.get('user_name', 'Unknown')
        user_hours[user] = user_hours.get(user, 0) + entry['hours']
    
    print(f"\n   Users ({len(user_hours)}):")
    for user, hours in sorted(user_hours.items(), key=lambda x: x[1], reverse=True):
        print(f"     {user}: {hours:.2f} hrs")
    print(f"\n   TOTAL: {sum(user_hours.values()):.2f} hours")

# Test 2: All of 2024
print("\n2. Testing ALL OF 2024...")
start = datetime(2024, 1, 1)
end = datetime(2024, 12, 31)
print(f"   Range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")

entries_2024 = client.get_time_entries(
    start_date=start,
    end_date=end,
    project_ids=MAXCOM_PROJECTS,
    limit=5000
)
print(f"   Result: {len(entries_2024)} entries")

if entries_2024:
    user_hours_2024 = {}
    for entry in entries_2024:
        user = entry.get('user_name', 'Unknown')
        user_hours_2024[user] = user_hours_2024.get(user, 0) + entry['hours']
    
    print(f"\n   Users ({len(user_hours_2024)}):")
    for user, hours in sorted(user_hours_2024.items(), key=lambda x: x[1], reverse=True):
        print(f"     {user}: {hours:.2f} hrs")
    print(f"\n   TOTAL: {sum(user_hours_2024.values()):.2f} hours")

# Test 3: All of 2025 so far
print("\n3. Testing ALL OF 2025 (so far)...")
start = datetime(2025, 1, 1)
end = datetime.now()
print(f"   Range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")

entries_2025 = client.get_time_entries(
    start_date=start,
    end_date=end,
    project_ids=MAXCOM_PROJECTS,
    limit=5000
)
print(f"   Result: {len(entries_2025)} entries")

if entries_2025:
    user_hours_2025 = {}
    for entry in entries_2025:
        user = entry.get('user_name', 'Unknown')
        user_hours_2025[user] = user_hours_2025.get(user, 0) + entry['hours']
    
    print(f"\n   Users ({len(user_hours_2025)}):")
    for user, hours in sorted(user_hours_2025.items(), key=lambda x: x[1], reverse=True):
        print(f"     {user}: {hours:.2f} hrs")
    print(f"\n   TOTAL: {sum(user_hours_2025.values()):.2f} hours")

print("\n" + "=" * 60)
