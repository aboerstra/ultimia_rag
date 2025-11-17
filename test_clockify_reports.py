#!/usr/bin/env python3
"""Debug script to test Clockify Reports API response format."""
import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('CLOCKIFY_API_KEY')

# Get workspace dynamically like the real code does
headers_temp = {
    'X-Api-Key': API_KEY,
    'Content-Type': 'application/json'
}
workspaces_resp = requests.get('https://api.clockify.me/api/v1/workspaces', headers=headers_temp)
workspaces = workspaces_resp.json()
WORKSPACE_ID = workspaces[0]['id'] if workspaces else None

print(f"Fetched Workspace ID: {WORKSPACE_ID}")

# Get MAXCOM project IDs
MAXCOM_PROJECTS = [
    "688a4bb2182ca836296a86b3",  # MAXCOM-020
    "688a4c4c182ca836296a899c",  # MAXCOM-021
    "688a4ce02fcd5d146c6cfa09",  # MAXCOM-022
    "688a4d532fcd5d146c6cfed5"   # MAXCOM-023
]

headers = {
    'X-Api-Key': API_KEY,
    'Content-Type': 'application/json'
}

# Test with project filter
start = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
end = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')

body = {
    "dateRangeStart": start,
    "dateRangeEnd": end,
    "detailedFilter": {
        "page": 1,
        "pageSize": 5,  # Just 5 for debugging
        "projects": MAXCOM_PROJECTS,
        "users": [],
        "clients": [],
        "tags": [],
        "rounding": False
    },
    "exportType": "JSON"
}

print("=" * 60)
print("TESTING CLOCKIFY REPORTS API")
print("=" * 60)
print(f"\nWorkspace ID: {WORKSPACE_ID}")
print(f"Project IDs: {len(MAXCOM_PROJECTS)}")
print(f"\nRequest Body:")
print(json.dumps(body, indent=2))

url = f"https://reports.api.clockify.me/v1/workspaces/{WORKSPACE_ID}/reports/detailed"

print(f"\n\nSending POST to: {url}")
resp = requests.post(url, headers=headers, json=body)

print(f"\nStatus Code: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    entries = data.get('timeentries', [])
    
    print(f"\nTotal Entries Returned: {len(entries)}")
    
    if entries:
        print(f"\n\nFIRST ENTRY STRUCTURE:")
        print("=" * 60)
        print(json.dumps(entries[0], indent=2))
        
        print(f"\n\nALL ENTRIES SUMMARY:")
        print("=" * 60)
        for i, entry in enumerate(entries, 1):
            project_name = entry.get('projectName', 'Unknown')
            user_name = entry.get('userName', 'Unknown')
            
            # Check different possible duration locations
            time_interval = entry.get('timeInterval', {})
            duration_ms = time_interval.get('duration')
            
            # Also check top level
            duration_top = entry.get('duration')
            
            print(f"{i}. {user_name} on {project_name}")
            print(f"   - duration in timeInterval: {duration_ms}")
            print(f"   - duration at top level: {duration_top}")
            print(f"   - timeInterval keys: {list(time_interval.keys())}")
            
    else:
        print("\n⚠️  No entries returned!")
        print("\nFull response:")
        print(json.dumps(data, indent=2))
else:
    print(f"\n❌ Error: {resp.status_code}")
    print(resp.text)
