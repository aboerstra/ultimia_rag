"""Jira API client with workaround for /search/jql bug."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from requests.auth import HTTPBasicAuth
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config


class JiraClient:
    """
    Jira client with workaround for the /search/jql bug.
    
    Uses Agile Board API as fallback when JQL search returns 0 results.
    Future-proof implementation using new /search/jql endpoint with Board API fallback.
    """
    
    def __init__(self):
        self.base_url = Config.JIRA_URL
        self.auth = HTTPBasicAuth(Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_all_projects(self) -> List[Dict]:
        """Get all accessible Jira projects."""
        try:
            url = f"{self.base_url}/rest/api/3/project"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            projects = response.json()
            return projects
        except Exception as e:
            print(f"Error getting projects: {e}")
            return []
    
    def get_boards(self, max_results: int = 50) -> List[Dict]:
        """Get all boards."""
        try:
            url = f"{self.base_url}/rest/agile/1.0/board"
            params = {'maxResults': max_results}
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            result = response.json()
            return result.get('values', [])
        except Exception as e:
            print(f"Error getting boards: {e}")
            return []
    
    def get_issues(
        self, 
        project_key: str = None,
        months_back: int = 6,
        max_results: int = 1000
    ) -> List[Dict]:
        """
        Get issues with fallback strategy:
        1. Try JQL search
        2. If 0 results, try board-based search
        3. If still 0, try direct issue range
        """
        start_date = datetime.now() - timedelta(days=months_back * 30)
        date_filter = start_date.strftime('%Y-%m-%d')
        
        # Strategy 1: Try JQL with pagination (the proper way)
        jql = f"project = {project_key} AND updated >= '{date_filter}' ORDER BY updated DESC" if project_key else f"updated >= '{date_filter}' ORDER BY updated DESC"
        
        url = f"{self.base_url}/rest/api/3/search/jql"
        fields = [
            'summary', 'status', 'issuetype', 'priority',
            'created', 'updated', 'resolutiondate',
            'assignee', 'reporter', 'labels', 'project',
            'customfield_10016', 'customfield_10014'
        ]
        
        try:
            all_issues = []
            page_size = 50  # Jira cloud limit per request
            next_page_token = None
            
            while len(all_issues) < max_results:
                payload = {
                    'jql': jql,
                    'fields': fields,
                    'maxResults': min(page_size, max_results - len(all_issues))
                }
                
                if next_page_token:
                    payload['pageToken'] = next_page_token
                
                response = requests.post(url, auth=self.auth, headers=self.headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                new_issues = result.get('values', [])
                if not new_issues:
                    break  # No more issues
                
                all_issues.extend(new_issues)
                
                # Check for next page token
                next_page_token = result.get('nextPageToken')
                if not next_page_token:
                    break  # Last page reached
            
            if all_issues:
                print(f"✅ JQL search successful: {len(all_issues)} issues (paginated)")
                return self._process_issues(all_issues)
            
            print(f"⚠️  JQL returned 0 results, trying workaround...")
            
        except Exception as e:
            print(f"⚠️  JQL search failed: {e}, trying workaround...")
        
        # Strategy 2: Try board-based search
        if project_key:
            board_issues = self._get_issues_via_board(project_key, max_results)
            if board_issues:
                print(f"✅ Board API successful: {len(board_issues)} issues")
                # Filter by date
                filtered = [
                    i for i in board_issues 
                    if i.get('updated', '1900-01-01') >= date_filter
                ]
                return filtered
        
        # Strategy 3: Try known issue keys
        print(f"ℹ️  Trying direct issue key fetch...")
        known_issues = self._try_known_issue_keys(project_key, max_results)
        if known_issues:
            print(f"✅ Direct fetch successful: {len(known_issues)} issues")
            return known_issues
        
        print(f"❌ All strategies failed")
        return []
    
    def _get_issues_via_board(self, project_key: str, max_results: int) -> List[Dict]:
        """Get issues via Agile Board API with pagination (different permission model)."""
        try:
            # Get boards for project
            boards_url = f"{self.base_url}/rest/agile/1.0/board"
            params = {'projectKeyOrId': project_key, 'type': 'scrum,kanban'}
            response = requests.get(boards_url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            boards = response.json().get('values', [])
            
            if not boards:
                return []
            
            # Get issues from first board with pagination
            board_id = boards[0]['id']
            issues_url = f"{self.base_url}/rest/agile/1.0/board/{board_id}/issue"
            
            all_issues = []
            start_at = 0
            page_size = 50  # Board API default/max page size
            
            while len(all_issues) < max_results:
                params = {
                    'startAt': start_at,
                    'maxResults': min(page_size, max_results - len(all_issues))
                }
                response = requests.get(issues_url, auth=self.auth, headers=self.headers, params=params)
                response.raise_for_status()
                result = response.json()
                
                issues = result.get('issues', [])  # Board API uses 'issues' not 'values'
                if not issues:
                    break  # No more issues
                
                all_issues.extend(issues)
                
                # Check if we have all issues
                total = result.get('total', 0)
                if len(all_issues) >= total or len(all_issues) >= max_results:
                    break
                
                start_at += len(issues)
            
            print(f"   Retrieved {len(all_issues)} total issues via Board API pagination")
            return self._process_issues(all_issues)
            
        except Exception as e:
            print(f"Board API error: {e}")
            return []
    
    def _try_known_issue_keys(self, project_key: str, max_results: int) -> List[Dict]:
        """Try fetching issues by guessing common key patterns."""
        issues = []
        
        # Try fetching issues 1-max_results
        for i in range(1, min(max_results + 1, 100)):
            key = f"{project_key}-{i}"
            try:
                url = f"{self.base_url}/rest/api/3/issue/{key}"
                response = requests.get(url, auth=self.auth, headers=self.headers)
                if response.status_code == 200:
                    issue = response.json()
                    issues.append(issue)
            except:
                continue
        
        return self._process_issues(issues) if issues else []
    
    def _process_issues(self, raw_issues: List) -> List[Dict]:
        """Process raw Jira issues into structured data."""
        processed = []
        
        for issue in raw_issues:
            fields = issue.get('fields', {})
            status = fields.get('status', {})
            issuetype = fields.get('issuetype', {})
            priority = fields.get('priority', {})
            assignee = fields.get('assignee', {})
            reporter = fields.get('reporter', {})
            project = fields.get('project', {})
            
            processed.append({
                'key': issue.get('key'),
                'summary': fields.get('summary'),
                'status': status.get('name') if status else None,
                'type': issuetype.get('name') if issuetype else None,
                'priority': priority.get('name') if priority else None,
                'created': fields.get('created'),
                'updated': fields.get('updated'),
                'resolved': fields.get('resolutiondate'),
                'assignee': assignee.get('displayName') if assignee else 'Unassigned',
                'reporter': reporter.get('displayName') if reporter else None,
                'story_points': fields.get('customfield_10016'),
                'epic_link': fields.get('customfield_10014'),
                'labels': fields.get('labels', []),
                'project': project.get('key') if project else None,
            })
        
        return processed
