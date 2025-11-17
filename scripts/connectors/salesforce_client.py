"""Salesforce API client for metadata and org analysis."""
from simple_salesforce import Salesforce
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sys
import json
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import Config


class SalesforceClient:
    """Client for interacting with Salesforce orgs."""
    
    def __init__(self, is_sandbox: bool = False, org_alias: Optional[str] = None):
        """
        Connect to Salesforce org using CLI OAuth or credentials.
        
        Tries in this order:
        1. Specific org if org_alias provided
        2. Org from SF_PRODUCTION_ORG/SF_SANDBOX_ORG env var
        3. First matching org from CLI (sandbox/production)
        4. Environment variables (username/password/token)
        
        Args:
            is_sandbox: True for sandbox, False for production
            org_alias: Specific org alias or username to use (optional)
        """
        self.env = 'sandbox' if is_sandbox else 'production'
        self.org_name = None
        self.org_id = None
        self.connection_method = None
        
        # Determine which org to use
        target_org = org_alias
        if not target_org:
            # Check env var for specific org
            target_org = Config.SF_SANDBOX_ORG if is_sandbox else Config.SF_PRODUCTION_ORG
        
        # Try CLI OAuth
        cli_auth = self._get_cli_auth(is_sandbox, target_org)
        
        if cli_auth:
            # Use CLI OAuth
            self.sf = Salesforce(
                instance_url=cli_auth['instance_url'],
                session_id=cli_auth['access_token']
            )
            self.org_name = cli_auth['username']
            self.org_id = cli_auth['org_id']
            self.org_alias = cli_auth.get('alias')
            self.connection_method = 'CLI OAuth'
            print(f"✅ Connected to Salesforce {self.env} using CLI OAuth")
            if self.org_alias:
                print(f"   Org: {self.org_alias} ({self.org_name})")
            else:
                print(f"   Org: {self.org_name}")
        else:
            # Fall back to env credentials
            if is_sandbox:
                username = Config.SF_SANDBOX_USERNAME
                password = Config.SF_SANDBOX_PASSWORD
                token = Config.SF_SANDBOX_TOKEN
                domain = 'test'
            else:
                username = Config.SF_PRODUCTION_USERNAME
                password = Config.SF_PRODUCTION_PASSWORD
                token = Config.SF_PRODUCTION_TOKEN
                domain = 'login'
            
            if not all([username, password, token]):
                raise ValueError(
                    f"No Salesforce {self.env} connection available. "
                    f"Either run 'sf org login web' or add credentials to .env"
                )
            
            self.sf = Salesforce(
                username=username,
                password=password,
                security_token=token,
                domain=domain
            )
            self.org_name = username
            self.connection_method = 'Username/Password'
            print(f"✅ Connected to Salesforce {self.env} using credentials")
            print(f"   User: {username}")
    
    def _get_cli_auth(self, is_sandbox: bool, target_org: Optional[str] = None) -> Optional[Dict]:
        """
        Get auth info from Salesforce CLI.
        
        Args:
            is_sandbox: Whether to look for sandbox vs production
            target_org: Specific org alias/username to use (optional)
        
        Returns:
            Dict with instance_url and access_token, or None if CLI not available
        """
        try:
            # Check if sf CLI is installed
            result = subprocess.run(
                ['sf', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            # If specific org requested, use it directly
            if target_org:
                result = subprocess.run(
                    ['sf', 'org', 'display', '--target-org', target_org, '--json'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    auth_data = json.loads(result.stdout)
                    auth_result = auth_data.get('result', {})
                    
                    return {
                        'instance_url': auth_result.get('instanceUrl'),
                        'access_token': auth_result.get('accessToken'),
                        'username': auth_result.get('username'),
                        'org_id': auth_result.get('id'),
                        'alias': auth_result.get('alias')
                    }
                return None
            
            # Otherwise, list all authorized orgs and find matching one
            result = subprocess.run(
                ['sf', 'org', 'list', '--json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            
            # Look for a matching org
            orgs = data.get('result', {}).get('nonScratchOrgs', [])
            
            # Find production or sandbox org
            for org in orgs:
                is_org_sandbox = org.get('isSandbox', False)
                
                # Match sandbox/production
                if is_org_sandbox == is_sandbox:
                    # Get auth info for this org
                    alias = org.get('alias') or org.get('username')
                    
                    result = subprocess.run(
                        ['sf', 'org', 'display', '--target-org', alias, '--json'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        auth_data = json.loads(result.stdout)
                        auth_result = auth_data.get('result', {})
                        
                        return {
                            'instance_url': auth_result.get('instanceUrl'),
                            'access_token': auth_result.get('accessToken'),
                            'username': auth_result.get('username'),
                            'org_id': auth_result.get('id'),
                            'alias': auth_result.get('alias')
                        }
            
            return None
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
            # SF CLI not available or error occurred
            return None
    
    def get_custom_objects(self) -> List[Dict]:
        """Get all custom objects in the org."""
        describe = self.sf.describe()
        custom_objects = []
        
        for obj in describe['sobjects']:
            if obj['custom']:  # Only custom objects
                try:
                    fields = self._get_object_fields(obj['name'])
                    custom_objects.append({
                        'name': obj['name'],
                        'label': obj['label'],
                        'custom': obj['custom'],
                        'createdDate': obj.get('createdDate'),
                        'fields': len(fields),
                        'field_list': [f['name'] for f in fields if f.get('custom', False)]
                    })
                except Exception as e:
                    print(f"  Warning: Could not get fields for {obj['name']}: {e}")
                    custom_objects.append({
                        'name': obj['name'],
                        'label': obj['label'],
                        'custom': obj['custom'],
                        'createdDate': obj.get('createdDate'),
                        'fields': 0,
                        'field_list': []
                    })
        
        return custom_objects
    
    def _get_object_fields(self, object_name: str) -> List:
        """Get fields for an object."""
        try:
            return getattr(self.sf, object_name).describe()['fields']
        except:
            return []
    
    def get_apex_classes(self) -> List[Dict]:
        """Get all Apex classes with metrics."""
        query = """
            SELECT Id, Name, CreatedDate, CreatedBy.Name,
                   LastModifiedDate, LengthWithoutComments, Status
            FROM ApexClass
            WHERE NamespacePrefix = null
            ORDER BY CreatedDate DESC
        """
        
        try:
            result = self.sf.query_all(query)
            return result['records']
        except Exception as e:
            print(f"  Warning: Could not query Apex classes: {e}")
            return []
    
    def get_apex_coverage(self) -> Dict:
        """Get Apex test coverage summary."""
        query = """
            SELECT PercentCovered
            FROM ApexOrgWideCoverage
        """
        
        try:
            result = self.sf.query(query)
            if result['records']:
                return {
                    'overall_coverage': result['records'][0]['PercentCovered']
                }
        except Exception as e:
            print(f"  Warning: Could not get test coverage: {e}")
        
        return {'overall_coverage': 0}
    
    def get_flows(self) -> List[Dict]:
        """Get all Flows in the org."""
        query = """
            SELECT Id, MasterLabel, ProcessType, Status,
                   CreatedDate, LastModifiedDate
            FROM Flow
            WHERE Status = 'Active'
            ORDER BY CreatedDate DESC
        """
        
        try:
            result = self.sf.query_all(query)
            return result['records']
        except Exception as e:
            print(f"  Warning: Could not query Flows: {e}")
            return []
    
    def get_validation_rules(self) -> List[Dict]:
        """Get validation rules (requires Tooling API)."""
        query = """
            SELECT Id, ValidationName, EntityDefinitionId,
                   Active, CreatedDate
            FROM ValidationRule
            ORDER BY CreatedDate DESC
        """
        
        try:
            result = self.sf.query_all(query)
            return result['records']
        except Exception as e:
            print(f"  Warning: Could not query validation rules: {e}")
            return []
    
    def get_deployment_history(self, days_back: int = 180) -> List[Dict]:
        """
        Get deployment history from Setup Audit Trail.
        
        Note: Limited to last 6 months in most orgs.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of deployment records
        """
        start_date = datetime.now() - timedelta(days=days_back)
        
        query = f"""
            SELECT Id, Action, Section, CreatedDate, CreatedBy.Name,
                   Display
            FROM SetupAuditTrail
            WHERE CreatedDate >= {start_date.isoformat()}
            AND (
                Action LIKE '%Deploy%'
                OR Action LIKE '%Create%'
                OR Action LIKE '%Update%'
            )
            ORDER BY CreatedDate DESC
        """
        
        try:
            result = self.sf.query_all(query)
            return result['records']
        except Exception as e:
            print(f"  Warning: Could not query deployment history: {e}")
            return []
    
    def compare_with_environment(self, other_client: 'SalesforceClient', start_date: str = None, end_date: str = None) -> Dict:
        """
        Compare this org with another (e.g., prod vs sandbox).
        
        Can do both current state comparison and time-based deployment comparison.
        
        Args:
            other_client: Another SalesforceClient instance
            start_date: Optional ISO date string for deployment comparison (e.g., '2025-01-01')
            end_date: Optional ISO date string for deployment comparison (e.g., '2025-03-31')
            
        Returns:
            Dict with differences including current state and optionally deployment history
        """
        # Current state comparison
        my_objects = {obj['name']: obj for obj in self.get_custom_objects()}
        other_objects = {obj['name']: obj for obj in other_client.get_custom_objects()}
        
        only_in_mine = set(my_objects.keys()) - set(other_objects.keys())
        only_in_other = set(other_objects.keys()) - set(my_objects.keys())
        in_both = set(my_objects.keys()) & set(other_objects.keys())
        
        field_diffs = {}
        for obj_name in in_both:
            if my_objects[obj_name]['fields'] != other_objects[obj_name]['fields']:
                field_diffs[obj_name] = {
                    f'{self.env}_fields': my_objects[obj_name]['fields'],
                    f'{other_client.env}_fields': other_objects[obj_name]['fields']
                }
        
        result = {
            f'only_in_{self.env}': list(only_in_mine),
            f'only_in_{other_client.env}': list(only_in_other),
            'field_differences': field_diffs,
            'summary': {
                'total_in_' + self.env: len(my_objects),
                'total_in_' + other_client.env: len(other_objects),
                'in_both': len(in_both),
                'drift_count': len(only_in_mine) + len(only_in_other) + len(field_diffs)
            }
        }
        
        # Time-based deployment comparison if dates provided
        if start_date and end_date:
            from datetime import datetime
            
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            # Get deployments for both orgs in date range
            my_deployments = self._filter_deployments_by_date(
                self.get_deployment_history(),
                start,
                end
            )
            other_deployments = self._filter_deployments_by_date(
                other_client.get_deployment_history(),
                start,
                end
            )
            
            # Compare deployment activities
            result['deployment_comparison'] = {
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                f'{self.env}_deployments': {
                    'count': len(my_deployments),
                    'actions': self._summarize_deployment_actions(my_deployments)
                },
                f'{other_client.env}_deployments': {
                    'count': len(other_deployments),
                    'actions': self._summarize_deployment_actions(other_deployments)
                },
                'deployment_gap': abs(len(my_deployments) - len(other_deployments)),
                'analysis': self._analyze_deployment_differences(
                    my_deployments,
                    other_deployments,
                    self.env,
                    other_client.env
                )
            }
        
        return result
    
    def _filter_deployments_by_date(self, deployments: List[Dict], start: datetime, end: datetime) -> List[Dict]:
        """Filter deployments to those within date range."""
        filtered = []
        for dep in deployments:
            created_date = dep.get('CreatedDate')
            if created_date:
                try:
                    dep_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    if start <= dep_date <= end:
                        filtered.append(dep)
                except:
                    pass
        return filtered
    
    def _summarize_deployment_actions(self, deployments: List[Dict]) -> Dict:
        """Summarize deployment actions by type."""
        actions = {}
        for dep in deployments:
            action = dep.get('Action', 'Unknown')
            actions[action] = actions.get(action, 0) + 1
        return actions
    
    def _analyze_deployment_differences(self, my_deps: List[Dict], other_deps: List[Dict], 
                                       my_env: str, other_env: str) -> Dict:
        """Analyze differences in deployment patterns."""
        # Extract unique items deployed
        my_items = {dep.get('Display', dep.get('Section', 'Unknown')) for dep in my_deps}
        other_items = {dep.get('Display', dep.get('Section', 'Unknown')) for dep in other_deps}
        
        only_in_mine = my_items - other_items
        only_in_other = other_items - my_items
        
        return {
            f'only_deployed_to_{my_env}': list(only_in_mine),
            f'only_deployed_to_{other_env}': list(only_in_other),
            'sync_status': 'in_sync' if len(only_in_mine) == 0 and len(only_in_other) == 0 else 'out_of_sync',
            'items_needing_sync': len(only_in_mine) + len(only_in_other)
        }
