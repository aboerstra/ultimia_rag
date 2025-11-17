"""Cross-validate transcripts, Jira, and Salesforce data."""
from typing import Dict, List
import re
import json


class CrossValidator:
    """Validate delivery across multiple data sources."""
    
    def __init__(self, transcripts: List[Dict], jira_issues: List[Dict], sf_data: Dict):
        """
        Initialize cross-validator.
        
        Args:
            transcripts: List of transcript analysis data
            jira_issues: List of Jira issues
            sf_data: Salesforce metadata dict
        """
        self.transcripts = transcripts
        self.jira = jira_issues
        self.sf = sf_data
    
    def validate_commitments(self) -> List[Dict]:
        """
        Match what was discussed → planned → built.
        
        Returns:
            List of validation results
        """
        validations = []
        
        # Extract SF object names
        sf_objects = {obj['name']: obj for obj in self.sf.get('custom_objects', [])}
        sf_apex = {cls['Name']: cls for cls in self.sf.get('apex_classes', [])}
        sf_flows = {flow['MasterLabel']: flow for flow in self.sf.get('flows', [])}
        
        # Look for mentions in transcripts
        for transcript in self.transcripts:
            if 'error' in transcript:
                continue
                
            # Get text from different possible locations
            text = ""
            if isinstance(transcript.get('text'), str):
                text = transcript['text']
            elif isinstance(transcript.get('analysis'), dict):
                text = json.dumps(transcript['analysis'])
            
            if not text:
                continue
            
            # Look for object-like mentions
            potential_objects = self._extract_object_mentions(text)
            
            for mention in potential_objects:
                # Check if it was built in Salesforce
                sf_match = self._find_matching_component(mention, sf_objects, sf_apex, sf_flows)
                
                # Check if it was planned in Jira
                jira_ticket = self._find_jira_ticket(mention, self.jira)
                
                validations.append({
                    'mention': mention,
                    'transcript': transcript.get('filename', 'Unknown'),
                    'jira_ticket': jira_ticket,
                    'salesforce_component': sf_match,
                    'status': 'complete' if sf_match else ('planned' if jira_ticket else 'discussed_only')
                })
        
        return validations
    
    def _extract_object_mentions(self, text: str) -> List[str]:
        """Extract potential object/feature names from text."""
        mentions = set()
        
        # Look for capitalized phrases that might be objects/features
        patterns = [
            r'([A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+(?:object|custom object|feature|component)',
            r'(?:build|create|develop|implement)\s+(?:a |the )?([A-Z][a-z]+(?: [A-Z][a-z]+)*)',
            r'(?:new|custom)\s+([A-Z][a-z]+(?: [A-Z][a-z]+)*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            mentions.update([m if isinstance(m, str) else m[0] for m in matches])
        
        # Filter out common words that aren't likely to be features
        common_words = {'New', 'Custom', 'The', 'This', 'That', 'Work', 'Build', 'Create'}
        mentions = {m for m in mentions if m not in common_words and len(m) > 3}
        
        return list(mentions)[:20]  # Limit to top 20 to avoid noise
    
    def _find_matching_component(self, mention: str, sf_objects: Dict, sf_apex: Dict, sf_flows: Dict) -> Dict:
        """Find matching Salesforce component."""
        mention_lower = mention.lower()
        
        # Try exact match with API name variations
        api_variations = [
            mention.replace(' ', '_') + '__c',  # Loan Application -> Loan_Application__c
            mention.replace(' ', '') + '__c',   # LoanApplication__c
            mention + '__c'
        ]
        
        for api_name in api_variations:
            if api_name in sf_objects:
                return {
                    'type': 'Custom Object',
                    'name': api_name,
                    'label': sf_objects[api_name].get('label', api_name)
                }
        
        # Try fuzzy match on Apex classes
        for apex_name, apex_data in sf_apex.items():
            if mention_lower in apex_name.lower() or apex_name.lower() in mention_lower:
                return {
                    'type': 'Apex Class',
                    'name': apex_name,
                    'lines': apex_data.get('LengthWithoutComments', 0)
                }
        
        # Try fuzzy match on Flows
        for flow_label, flow_data in sf_flows.items():
            if mention_lower in flow_label.lower() or flow_label.lower() in mention_lower:
                return {
                    'type': 'Flow',
                    'name': flow_label,
                    'status': flow_data.get('Status', 'Unknown')
                }
        
        # Try partial match on custom objects
        for obj_name, obj_data in sf_objects.items():
            obj_label = obj_data.get('label', '').lower()
            if mention_lower in obj_label or mention_lower in obj_name.lower():
                return {
                    'type': 'Custom Object',
                    'name': obj_name,
                    'label': obj_data.get('label', obj_name)
                }
        
        return None
    
    def _find_jira_ticket(self, mention: str, jira_issues: List[Dict]) -> str:
        """Find related Jira ticket."""
        mention_lower = mention.lower()
        
        for issue in jira_issues:
            summary = issue.get('summary', '').lower()
            description = issue.get('description', '').lower()
            
            if mention_lower in summary or mention_lower in description:
                return issue.get('key', 'Unknown')
        
        return None
    
    def generate_gap_report(self) -> str:
        """Generate markdown gap analysis report."""
        validations = self.validate_commitments()
        
        complete = [v for v in validations if v['status'] == 'complete']
        planned = [v for v in validations if v['status'] == 'planned']
        discussed = [v for v in validations if v['status'] == 'discussed_only']
        
        report = f"""# Gap Analysis: Discussion → Plan → Build

## Summary
- ✅ **Complete:** {len(complete)} features (discussed → planned → built)
- 📋 **Planned:** {len(planned)} features (discussed → planned, awaiting build)
- 💭 **Discussed Only:** {len(discussed)} features (no plan or build)

## Complete Features (Discussion → Plan → Build)
"""
        
        if complete:
            for v in complete:
                component = v['salesforce_component']
                report += f"\n### ✅ {v['mention']}\n"
                report += f"- 📄 **Mentioned in:** {v['transcript']}\n"
                report += f"- 🎯 **Jira:** {v['jira_ticket'] or 'N/A'}\n"
                report += f"- ✅ **Salesforce:** {component['type']} - {component['name']}\n"
        else:
            report += "\nNo complete features tracked in this analysis.\n"
        
        report += "\n## Planned Features (Awaiting Build)\n"
        
        if planned:
            for v in planned:
                report += f"\n### 📋 {v['mention']}\n"
                report += f"- 📄 **Mentioned in:** {v['transcript']}\n"
                report += f"- 🎯 **Jira:** {v['jira_ticket']}\n"
                report += f"- ⏳ **Status:** Planned but not yet deployed to Salesforce\n"
        else:
            report += "\nNo planned features pending deployment.\n"
        
        report += "\n## Discussed Features (Not Yet Planned)\n"
        
        if discussed:
            for v in discussed:
                report += f"\n### 💭 {v['mention']}\n"
                report += f"- 📄 **Mentioned in:** {v['transcript']}\n"
                report += f"- ⚠️ **Gap:** Discussed but no Jira ticket or Salesforce deployment found\n"
        else:
            report += "\nAll discussed features have been planned or built.\n"
        
        report += f"\n---\n\n**Analysis Date:** {json.dumps(self._get_current_date())}\n"
        report += f"**Data Sources:** {len(self.transcripts)} transcripts, {len(self.jira)} Jira issues, {len(self.sf.get('custom_objects', []))} SF objects\n"
        
        return report
    
    def _get_current_date(self) -> str:
        """Get current date as string."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for the gap analysis."""
        validations = self.validate_commitments()
        
        return {
            'total_mentions': len(validations),
            'complete': len([v for v in validations if v['status'] == 'complete']),
            'planned': len([v for v in validations if v['status'] == 'planned']),
            'discussed_only': len([v for v in validations if v['status'] == 'discussed_only']),
            'completion_rate': len([v for v in validations if v['status'] == 'complete']) / len(validations) * 100 if validations else 0
        }
