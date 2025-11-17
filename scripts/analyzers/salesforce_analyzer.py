"""Analyze Salesforce metadata for QBR insights."""
from typing import Dict, List
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import Config


class SalesforceAnalyzer:
    """Analyze Salesforce org data for QBR metrics."""
    
    def __init__(self, sf_data: Dict):
        """
        Initialize with Salesforce data.
        
        Args:
            sf_data: Dict from SalesforceClient
        """
        self.data = sf_data
    
    def calculate_deployment_metrics(self, start_date: str, end_date: str) -> Dict:
        """
        Calculate what was deployed in a date range.
        
        Args:
            start_date: ISO format date string
            end_date: ISO format date string
        
        Returns:
            Dict with deployment summary
        """
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Objects deployed
        objects_in_range = []
        for obj in self.data.get('custom_objects', []):
            created_date = obj.get('createdDate')
            if created_date:
                try:
                    obj_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    if start <= obj_date <= end:
                        objects_in_range.append(obj)
                except:
                    pass
        
        # Apex deployed
        apex_in_range = []
        for cls in self.data.get('apex_classes', []):
            created_date = cls.get('CreatedDate')
            if created_date:
                try:
                    cls_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    if start <= cls_date <= end:
                        apex_in_range.append(cls)
                except:
                    pass
        
        # Flows deployed
        flows_in_range = []
        for flow in self.data.get('flows', []):
            created_date = flow.get('CreatedDate')
            if created_date:
                try:
                    flow_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    if start <= flow_date <= end:
                        flows_in_range.append(flow)
                except:
                    pass
        
        return {
            'custom_objects_deployed': len(objects_in_range),
            'apex_classes_deployed': len(apex_in_range),
            'flows_deployed': len(flows_in_range),
            'total_deployments': len(objects_in_range) + len(apex_in_range) + len(flows_in_range),
            'details': {
                'objects': [obj['name'] for obj in objects_in_range],
                'apex': [cls['Name'] for cls in apex_in_range],
                'flows': [flow['MasterLabel'] for flow in flows_in_range]
            }
        }
    
    def calculate_code_metrics(self) -> Dict:
        """Calculate code quality metrics."""
        apex_classes = self.data.get('apex_classes', [])
        flows = self.data.get('flows', [])
        coverage = self.data.get('coverage', {})
        
        total_lines = sum(
            cls.get('LengthWithoutComments', 0) 
            for cls in apex_classes
        )
        
        return {
            'apex_classes_count': len(apex_classes),
            'total_lines_of_code': total_lines,
            'test_coverage': coverage.get('overall_coverage', 0),
            'active_flows': len([f for f in flows if f.get('Status') == 'Active']),
            'custom_objects_count': len(self.data.get('custom_objects', [])),
            'validation_rules_count': len(self.data.get('validation_rules', []))
        }
    
    def identify_recent_changes(self, days: int = 30) -> List[Dict]:
        """
        Identify components changed in last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of recent changes
        """
        cutoff = datetime.now() - timedelta(days=days)
        changes = []
        
        # Check Apex classes
        for cls in self.data.get('apex_classes', []):
            last_modified = cls.get('LastModifiedDate')
            if last_modified:
                try:
                    mod_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                    if mod_date >= cutoff:
                        changes.append({
                            'type': 'Apex Class',
                            'name': cls['Name'],
                            'date': last_modified,
                            'lines': cls.get('LengthWithoutComments', 0)
                        })
                except:
                    pass
        
        # Check Flows
        for flow in self.data.get('flows', []):
            last_modified = flow.get('LastModifiedDate')
            if last_modified:
                try:
                    mod_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                    if mod_date >= cutoff:
                        changes.append({
                            'type': 'Flow',
                            'name': flow['MasterLabel'],
                            'date': last_modified,
                            'process_type': flow.get('ProcessType', 'Unknown')
                        })
                except:
                    pass
        
        return sorted(changes, key=lambda x: x['date'], reverse=True)
    
    def generate_summary_report(self) -> str:
        """Generate a markdown summary report of SF metrics."""
        metrics = self.calculate_code_metrics()
        recent = self.identify_recent_changes(30)
        
        report = f"""# Salesforce Deliverables Summary

## Code Metrics
- **Custom Objects:** {metrics['custom_objects_count']}
- **Apex Classes:** {metrics['apex_classes_count']} ({metrics['total_lines_of_code']} lines of code)
- **Test Coverage:** {metrics['test_coverage']}%
- **Active Flows:** {metrics['active_flows']}
- **Validation Rules:** {metrics['validation_rules_count']}

## Recent Changes (Last 30 Days)
"""
        
        if recent:
            for change in recent[:10]:  # Top 10 recent changes
                report += f"\n- **{change['type']}:** {change['name']}"
                if 'lines' in change:
                    report += f" ({change['lines']} lines)"
                report += f" - {change['date']}"
        else:
            report += "\nNo recent changes detected.\n"
        
        return report
