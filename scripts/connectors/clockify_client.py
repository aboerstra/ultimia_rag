"""Clockify API client for time tracking data collection."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from config import Config


class ClockifyClient:
    """Client for interacting with Clockify API."""
    
    def __init__(self):
        self.api_key = Config.CLOCKIFY_API_KEY
        self.base_url = Config.CLOCKIFY_BASE_URL
        self.headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        self.workspace_id = None
        
    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to Clockify API."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_workspaces(self) -> List[Dict]:
        """Get all workspaces for the user."""
        try:
            workspaces = self._get('workspaces')
            return workspaces
        except Exception as e:
            print(f"Error fetching workspaces: {e}")
            return []
    
    def set_workspace(self, workspace_id: str = None):
        """Set the active workspace. If no ID provided, uses first workspace."""
        if workspace_id:
            self.workspace_id = workspace_id
        else:
            workspaces = self.get_workspaces()
            if workspaces:
                self.workspace_id = workspaces[0]['id']
                print(f"Using workspace: {workspaces[0]['name']}")
    
    def get_clients(self) -> List[Dict]:
        """Get all clients in the workspace."""
        if not self.workspace_id:
            self.set_workspace()
        
        try:
            # Fetch all clients with large page size
            params = {
                'page-size': 5000  # Maximum page size to get all clients
            }
            clients = self._get(f'workspaces/{self.workspace_id}/clients', params)
            return [
                {
                    'id': c['id'],
                    'name': c['name']
                }
                for c in clients
            ]
        except Exception as e:
            print(f"Error fetching clients: {e}")
            return []
    
    def get_projects(self, client_id: str = None) -> List[Dict]:
        """Get all projects in the workspace, optionally filtered by client."""
        if not self.workspace_id:
            self.set_workspace()
        
        try:
            # Fetch all projects with large page size to avoid pagination issues
            params = {
                'page-size': 5000,  # Maximum page size to get all projects
                'archived': 'false'  # Only active projects
            }
            projects = self._get(f'workspaces/{self.workspace_id}/projects', params)
            
            # Filter by client if specified
            if client_id:
                projects = [p for p in projects if p.get('clientId') == client_id]
            
            return [
                {
                    'id': p['id'],
                    'name': p['name'],
                    'client': p.get('clientName'),
                    'clientId': p.get('clientId'),
                    'billable': p.get('billable', False),
                    'color': p.get('color')
                }
                for p in projects
            ]
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return []
    
    def get_time_entries(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        project_ids: List[str] = None,
        user_email: str = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get time entries for a date range using Reports API (gets ALL users in one call).
        
        Args:
            start_date: Start date (defaults to 6 months ago)
            end_date: End date (defaults to now)
            project_ids: Optional list of project IDs to filter
            user_email: Optional user email to filter
            limit: Maximum number of entries
            
        Returns:
            List of time entry dictionaries
        """
        if not self.workspace_id:
            self.set_workspace()
        
        # Default to last 6 months
        if not start_date:
            start_date = datetime.now() - timedelta(days=180)
        if not end_date:
            end_date = datetime.now()
        
        # Use Reports API - gets ALL users' entries in one call
        try:
            print(f"  Fetching ALL time entries via Reports API...")
            
            # Reports API endpoint
            reports_url = f"https://reports.api.clockify.me/v1/workspaces/{self.workspace_id}/reports/detailed"
            
            # Get client ID from first project to filter by client instead of individual projects
            client_id = None
            if project_ids:
                # Get project details to find client ID
                all_projects = self.get_projects()
                for proj in all_projects:
                    if proj['id'] in project_ids:
                        client_id = proj.get('clientId')
                        if client_id:
                            print(f"  Filtering by client ID: {client_id}")
                            break
            
            # Build request body
            body = {
                "dateRangeStart": start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "dateRangeEnd": end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "detailedFilter": {
                    "page": 1,
                    "pageSize": limit,
                    "projects": [],  # Don't filter by project
                    "users": [],  # Empty = all users
                    "clients": [client_id] if client_id else [],  # Filter by client!
                    "tags": [],
                    "rounding": False
                },
                "exportType": "JSON"
            }
            
            # Add user filter if specified
            if user_email:
                users = self.get_users()
                matching_user = next((u for u in users if u.get('email') == user_email), None)
                if matching_user:
                    body["detailedFilter"]["users"] = [matching_user['id']]
            
            # Implement pagination to get ALL entries
            all_entries = []
            page = 1
            
            while True:
                body["detailedFilter"]["page"] = page
                
                response = requests.post(reports_url, headers=self.headers, json=body)
                response.raise_for_status()
                data = response.json()
                
                page_entries = data.get('timeentries', [])
                
                if not page_entries:
                    break  # No more entries
                
                all_entries.extend(page_entries)
                print(f"  Page {page}: {len(page_entries)} entries (total so far: {len(all_entries)})")
                
                if len(page_entries) < limit:
                    break  # Last page (partial page means we're done)
                
                page += 1
                
                if page > 20:  # Safety limit
                    print(f"  ⚠️  Reached page limit (20), stopping")
                    break
            
            print(f"  Total entries fetched: {len(all_entries)}")
            
            # NOW filter by project IDs (after getting ALL entries)
            if project_ids:
                entries = [e for e in all_entries if e.get('projectId') in project_ids]
                print(f"  Filtered to {len(entries)} MAXCOM entries")
            else:
                entries = all_entries
            
            # Count by user for visibility
            user_counts = {}
            for entry in entries:
                user_name = entry.get('userName', 'Unknown')
                user_counts[user_name] = user_counts.get(user_name, 0) + 1
            
            for user_name, count in sorted(user_counts.items()):
                print(f"    {user_name}: {count} entries")
            
            return self._process_reports_entries(entries)
            
        except Exception as e:
            print(f"Error fetching time entries: {e}")
            return []
    
    def _process_reports_entries(self, raw_entries: List) -> List[Dict]:
        """Process Reports API time entries into structured data."""
        processed = []
        
        for entry in raw_entries:
            # Reports API: duration is in SECONDS (not milliseconds!)
            duration_seconds = entry.get('timeInterval', {}).get('duration', 0)
            hours = duration_seconds / 3600 if duration_seconds else 0
            
            processed.append({
                'id': entry.get('_id'),
                'description': entry.get('description', 'No description'),
                'start': entry.get('timeInterval', {}).get('start'),
                'end': entry.get('timeInterval', {}).get('end'),
                'hours': round(hours, 2),
                'project_id': entry.get('projectId'),
                'user_id': entry.get('userId'),
                'billable': entry.get('billable', False),
                'tags': [t.get('name') for t in entry.get('tags', [])],
                'user_name': entry.get('userName'),
                'project_name': entry.get('projectName'),
            })
        
        return processed
    
    def _process_time_entries(self, raw_entries: List) -> List[Dict]:
        """Process raw time entries into structured data."""
        processed = []
        
        for entry in raw_entries:
            time_interval = entry.get('timeInterval', {})
            start = time_interval.get('start')
            end = time_interval.get('end')
            duration = time_interval.get('duration')
            
            # Calculate duration in hours if not provided
            if duration and duration.startswith('PT'):
                # Parse ISO 8601 duration
                duration_seconds = self._parse_duration(duration)
                hours = duration_seconds / 3600
            else:
                hours = 0
            
            processed.append({
                'id': entry.get('id'),
                'description': entry.get('description', 'No description'),
                'start': start,
                'end': end,
                'hours': round(hours, 2),
                'project_id': entry.get('projectId'),
                'user_id': entry.get('userId'),
                'billable': entry.get('billable', False),
                'tags': [t.get('name') for t in entry.get('tags', [])],
            })
        
        return processed
    
    def _parse_duration(self, duration_str: str) -> float:
        """Parse ISO 8601 duration string to seconds."""
        # Simple parser for PT format (e.g., PT2H30M15S)
        import re
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = float(match.group(3)) if match.group(3) else 0
        
        return hours * 3600 + minutes * 60 + seconds
    
    def get_users(self) -> List[Dict]:
        """Get all users in the workspace."""
        if not self.workspace_id:
            self.set_workspace()
        
        try:
            users = self._get(f'workspaces/{self.workspace_id}/users')
            return [
                {
                    'id': u['id'],
                    'name': u.get('name'),
                    'email': u.get('email')
                }
                for u in users
            ]
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []
    
    def get_summary_by_project(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        project_ids: List[str] = None
    ) -> Dict:
        """
        Get time tracking summary grouped by project.
        
        Args:
            start_date: Start date
            end_date: End date
            project_ids: Optional list of project IDs to filter
            
        Returns:
            Dict with project summaries
        """
        entries = self.get_time_entries(start_date, end_date, project_ids=project_ids)
        projects = {p['id']: p['name'] for p in self.get_projects()}
        
        summary = {}
        for entry in entries:
            project_id = entry['project_id']
            project_name = projects.get(project_id, 'Unknown Project')
            
            if project_name not in summary:
                summary[project_name] = {
                    'total_hours': 0,
                    'billable_hours': 0,
                    'entry_count': 0
                }
            
            summary[project_name]['total_hours'] += entry['hours']
            if entry.get('billable'):
                summary[project_name]['billable_hours'] += entry['hours']
            summary[project_name]['entry_count'] += 1
        
        return summary
