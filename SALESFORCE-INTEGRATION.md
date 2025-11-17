# Salesforce Integration - QBR Automation Enhancement

**Context:** This QBR automation is for a Salesforce implementation project at Maxim. The real deliverables are Salesforce objects, Apex classes, and Flows - not just Jira tickets.

**Critical Insight:** Without Salesforce data, the QBR is missing the actual proof of delivery.

---

## Why Salesforce Integration is Essential

### The Missing Piece

**Current Data Sources:**
1. ✅ Transcripts - What was **discussed**
2. ✅ Jira - What was **planned**
3. ✅ Clockify - How long it **took**
4. ✅ Confluence - How it was **documented**
5. ❌ **Salesforce - What was actually BUILT** ← MISSING!

### The Complete Story

**Example: "Data Model" Feature**

**Without SF:**
- Oct 15: "Michael asked about data model timeline"
- Oct 20: Jira ticket MAXIM-234 created
- Oct 28: Ticket marked "Done"
- 40 hours logged in Clockify
- ❓ But what actually shipped?

**With SF:**
- Oct 15: "Michael asked about data model timeline"
- Oct 20: Jira ticket MAXIM-234 created
- Oct 28: Ticket marked "Done"
- 40 hours logged in Clockify
- ✅ **Loan_Application__c deployed with 12 fields**
- ✅ **Credit_Score__c custom object created**
- ✅ **LoanValidation.cls deployed (250 lines, 94% coverage)**
- ⚠️ **Risk_Assessment__c mentioned in transcript but NOT deployed**

### What Michael Actually Cares About

From the transcripts, Michael's priorities:
1. **Transparency** - Show what's really done
2. **Accountability** - Who built what
3. **Quality** - Test coverage, technical debt
4. **Alignment** - Discussion → Plan → Actual Build

Salesforce metadata proves all four.

---

## Architecture: 5th Data Source

### Enhanced Directory Structure

```
data-sources/
├── transcripts/          # What was discussed
├── jira/                 # What was planned
├── clockify/             # How long it took
├── confluence/           # How it was documented
└── salesforce/           # What was built (NEW!)
    ├── raw/
    │   ├── production/
    │   │   ├── objects/       # Custom object metadata
    │   │   ├── apex/          # Apex class files
    │   │   ├── flows/         # Flow definitions
    │   │   └── metadata.json  # Full metadata dump
    │   └── sandbox/
    │       └── (same structure)
    ├── metrics.json          # Parsed metrics
    ├── deployments.json      # Deployment history
    └── comparison.json       # Prod vs Sandbox diff
```

### Data Flow

```
Salesforce Orgs
    ↓
SalesforceClient
    ↓
Metadata Extraction
    ↓
SalesforceAnalyzer (metrics, quality)
    ↓
CrossValidator (transcript + Jira + SF)
    ↓
QBR with Technical Delivery Section
```

---

## Implementation Plan

### Phase 0: Setup (1-2 hours)

**Update requirements.txt:**
```python
simple-salesforce==1.12.5  # Python SF client
```

**Add to .env:**
```bash
# Salesforce Production
SF_PRODUCTION_USERNAME=your.username@maxim.com
SF_PRODUCTION_PASSWORD=your_password
SF_PRODUCTION_TOKEN=your_security_token

# Salesforce Sandbox
SF_SANDBOX_USERNAME=your.username@maxim.com.sandbox
SF_SANDBOX_PASSWORD=your_password
SF_SANDBOX_TOKEN=your_security_token
```

**Update scripts/config.py:**
```python
# Add to Config class
SF_PRODUCTION_USERNAME = os.getenv('SF_PRODUCTION_USERNAME')
SF_PRODUCTION_PASSWORD = os.getenv('SF_PRODUCTION_PASSWORD')
SF_PRODUCTION_TOKEN = os.getenv('SF_PRODUCTION_TOKEN')

SF_SANDBOX_USERNAME = os.getenv('SF_SANDBOX_USERNAME')
SF_SANDBOX_PASSWORD = os.getenv('SF_SANDBOX_PASSWORD')
SF_SANDBOX_TOKEN = os.getenv('SF_SANDBOX_TOKEN')

SALESFORCE_RAW = PROJECT_ROOT / 'data-sources' / 'salesforce' / 'raw'
```

---

### Phase 1: Basic Connector (Week 1, Days 1-2)

**Create:** `scripts/connectors/salesforce_client.py`

```python
"""Salesforce API client for metadata and org analysis."""
from simple_salesforce import Salesforce
from typing import Dict, List
from datetime import datetime, timedelta
from ..config import Config


class SalesforceClient:
    """Client for interacting with Salesforce orgs."""
    
    def __init__(self, env='production'):
        """
        Connect to Salesforce org.
        
        Args:
            env: 'production' or 'sandbox'
        """
        self.env = env
        
        if env == 'production':
            username = Config.SF_PRODUCTION_USERNAME
            password = Config.SF_PRODUCTION_PASSWORD
            token = Config.SF_PRODUCTION_TOKEN
            domain = 'login'
        else:
            username = Config.SF_SANDBOX_USERNAME
            password = Config.SF_SANDBOX_PASSWORD
            token = Config.SF_SANDBOX_TOKEN
            domain = 'test'
        
        self.sf = Salesforce(
            username=username,
            password=password,
            security_token=token,
            domain=domain
        )
    
    def get_custom_objects(self) -> List[Dict]:
        """Get all custom objects in the org."""
        describe = self.sf.describe()
        custom_objects = [
            {
                'name': obj['name'],
                'label': obj['label'],
                'custom': obj['custom'],
                'createdDate': obj.get('createdDate'),
                'fields': len(self._get_object_fields(obj['name']))
            }
            for obj in describe['sobjects']
            if obj['custom']  # Only custom objects
        ]
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
        
        result = self.sf.query_all(query)
        return result['records']
    
    def get_apex_coverage(self) -> Dict:
        """Get Apex test coverage summary."""
        query = """
            SELECT PercentCovered
            FROM ApexOrgWideCoverage
        """
        
        result = self.sf.query(query)
        if result['records']:
            return {
                'overall_coverage': result['records'][0]['PercentCovered']
            }
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
        
        result = self.sf.query_all(query)
        return result['records']
    
    def get_validation_rules(self) -> List[Dict]:
        """Get validation rules (requires Tooling API)."""
        # Uses Tooling API for metadata
        query = """
            SELECT Id, ValidationName, EntityDefinitionId,
                   Active, CreatedDate
            FROM ValidationRule
            ORDER BY CreatedDate DESC
        """
        
        try:
            result = self.sf.query_all(query)
            return result['records']
        except:
            return []
    
    def get_deployment_history(self, days_back: int = 180) -> List[Dict]:
        """
        Get deployment history from Setup Audit Trail.
        
        Note: Limited to last 6 months in most orgs.
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
        
        result = self.sf.query_all(query)
        return result['records']
    
    def compare_with_environment(self, other_client: 'SalesforceClient') -> Dict:
        """
        Compare this org with another (e.g., prod vs sandbox).
        
        Args:
            other_client: Another SalesforceClient instance
            
        Returns:
            Dict with differences
        """
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
        
        return {
            f'only_in_{self.env}': list(only_in_mine),
            f'only_in_{other_client.env}': list(only_in_other),
            'field_differences': field_diffs
        }
```

**Test it:**
```python
# Test script
from scripts.connectors.salesforce_client import SalesforceClient

# Connect to production
prod = SalesforceClient('production')
print("Custom Objects:", len(prod.get_custom_objects()))
print("Apex Classes:", len(prod.get_apex_classes()))
print("Flows:", len(prod.get_flows()))
print("Coverage:", prod.get_apex_coverage())
```

---

### Phase 2: Data Collection (Week 1, Days 3-5)

**Update:** `scripts/main.py`

```python
# Add to QBROrchestrator

def step7_collect_salesforce_data(self):
    """Step 7: Collect Salesforce metadata."""
    print("\n" + "="*60)
    print("STEP 7: Collecting Salesforce metadata")
    print("="*60)
    
    try:
        # Production
        print("\n  Connecting to Production org...")
        prod_client = SalesforceClient('production')
        
        prod_data = {
            'environment': 'production',
            'custom_objects': prod_client.get_custom_objects(),
            'apex_classes': prod_client.get_apex_classes(),
            'flows': prod_client.get_flows(),
            'coverage': prod_client.get_apex_coverage(),
            'deployments': prod_client.get_deployment_history()
        }
        
        self._save_json(prod_data, Config.SALESFORCE_RAW / 'production' / 'metadata.json')
        print(f"  ✅ Production: {len(prod_data['custom_objects'])} objects, {len(prod_data['apex_classes'])} Apex classes")
        
        # Sandbox
        print("\n  Connecting to Sandbox org...")
        sandbox_client = SalesforceClient('sandbox')
        
        sandbox_data = {
            'environment': 'sandbox',
            'custom_objects': sandbox_client.get_custom_objects(),
            'apex_classes': sandbox_client.get_apex_classes(),
            'flows': sandbox_client.get_flows(),
            'coverage': sandbox_client.get_apex_coverage(),
            'deployments': sandbox_client.get_deployment_history()
        }
        
        self._save_json(sandbox_data, Config.SALESFORCE_RAW / 'sandbox' / 'metadata.json')
        print(f"  ✅ Sandbox: {len(sandbox_data['custom_objects'])} objects, {len(sandbox_data['apex_classes'])} Apex classes")
        
        # Compare
        print("\n  Comparing environments...")
        comparison = prod_client.compare_with_environment(sandbox_client)
        self._save_json(comparison, Config.SALESFORCE_RAW / 'comparison.json')
        
        if comparison['only_in_production']:
            print(f"  ⚠️ {len(comparison['only_in_production'])} objects only in production")
        if comparison['only_in_sandbox']:
            print(f"  ⚠️ {len(comparison['only_in_sandbox'])} objects only in sandbox")
        
        print("\n✅ Salesforce data collected")
        
    except Exception as e:
        print(f"❌ Error collecting Salesforce data: {e}")
```

---

### Phase 3: Analysis & Metrics (Week 2, Days 1-3)

**Create:** `scripts/analyzers/salesforce_analyzer.py`

```python
"""Analyze Salesforce metadata for QBR insights."""
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import json


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
        
        Returns:
            Dict with deployment summary
        """
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Objects deployed
        objects_in_range = [
            obj for obj in self.data['custom_objects']
            if obj.get('createdDate') and 
            start <= datetime.fromisoformat(obj['createdDate']) <= end
        ]
        
        # Apex deployed
        apex_in_range = [
            cls for cls in self.data['apex_classes']
            if start <= datetime.fromisoformat(cls['CreatedDate']) <= end
        ]
        
        # Flows deployed
        flows_in_range = [
            flow for flow in self.data['flows']
            if start <= datetime.fromisoformat(flow['CreatedDate']) <= end
        ]
        
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
        total_lines = sum(
            cls.get('LengthWithoutComments', 0) 
            for cls in self.data['apex_classes']
        )
        
        return {
            'apex_classes_count': len(self.data['apex_classes']),
            'total_lines_of_code': total_lines,
            'test_coverage': self.data['coverage']['overall_coverage'],
            'active_flows': len([f for f in self.data['flows'] if f['Status'] == 'Active'])
        }
    
    def identify_recent_changes(self, days: int = 30) -> List[str]:
        """Identify components changed in last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        
        changes = []
        
        for cls in self.data['apex_classes']:
            if datetime.fromisoformat(cls['LastModifiedDate']) >= cutoff:
                changes.append(f"Apex: {cls['Name']}")
        
        return changes
```

---

### Phase 4: Cross-Validation (Week 2, Days 4-5)

**Create:** `scripts/analyzers/cross_validator.py`

```python
"""Cross-validate transcripts, Jira, and Salesforce data."""
from typing import Dict, List
import re


class CrossValidator:
    """Validate delivery across multiple data sources."""
    
    def __init__(self, transcripts, jira_issues, sf_data):
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
        sf_objects = {obj['name'] for obj in self.sf['custom_objects']}
        
        # Look for mentions in transcripts
        for transcript in self.transcripts:
            text = transcript.get('text', '')
            
            # Look for object-like mentions (e.g., "Loan Application", "Credit Score")
            potential_objects = self._extract_object_mentions(text)
            
            for mention in potential_objects:
                # Check if it was built
                built = self._find_matching_sobject(mention, sf_objects)
                
                # Check if it was planned in Jira
                jira_ticket = self._find_jira_ticket(mention, self.jira)
                
                validations.append({
                    'mention': mention,
                    'transcript': transcript['filename'],
                    'jira_ticket': jira_ticket,
                    'salesforce_object': built,
                    'status': 'complete' if built else 'missing'
                })
        
        return validations
    
    def _extract_object_mentions(self, text: str) -> List[str]:
        """Extract potential object names from text."""
        # Look for capitalized phrases that might be objects
        patterns = [
            r'([A-Z][a-z]+(?: [A-Z][a-z]+)*) object',
            r'build (?:a |the )?([A-Z][a-z]+(?: [A-Z][a-z]+)*)',
            r'create (?:a |the )?([A-Z][a-z]+(?: [A-Z][a-z]+)*)'
        ]
        
        mentions = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            mentions.extend(matches)
        
        return list(set(mentions))
    
    def _find_matching_sobject(self, mention: str, sf_objects: set) -> str:
        """Find matching Salesforce object."""
        # Convert "Loan Application" -> "Loan_Application__c"
        api_name = mention.replace(' ', '_') + '__c'
        
        if api_name in sf_objects:
            return api_name
        
        # Try variations
        for obj in sf_objects:
            if mention.lower() in obj.lower():
                return obj
        
        return None
    
    def _find_jira_ticket(self, mention: str, jira_issues: List) -> str:
        """Find related Jira ticket."""
        for issue in jira_issues:
            summary = issue.get('summary', '').lower()
            if mention.lower() in summary:
                return issue['key']
        
        return None
    
    def generate_gap_report(self) -> str:
        """Generate markdown gap analysis report."""
        validations = self.validate_commitments()
        
        complete = [v for v in validations if v['status'] == 'complete']
        missing = [v for v in validations if v['status'] == 'missing']
        
        report = f"""# Gap Analysis: Discussion → Plan → Build

## Summary
- ✅ Complete: {len(complete)} features
- ⚠️ Missing: {len(missing)} features

## Complete Features
"""
        
        for v in complete:
            report += f"\n### {v['mention']}\n"
            report += f"- 📄 Mentioned in: {v['transcript']}\n"
            report += f"- 🎯 Jira: {v['jira_ticket'] or 'N/A'}\n"
            report += f"- ✅ Salesforce: {v['salesforce_object']}\n"
        
        report += "\n## Missing Features\n"
        
        for v in missing:
            report += f"\n### ⚠️ {v['mention']}\n"
            report += f"- 📄 Mentioned in: {v['transcript']}\n"
            report += f"- 🎯 Jira: {v['jira_ticket'] or 'Not found'}\n"
            report += f"- ❌ Salesforce: Not deployed\n"
        
        return report
```

---

### Phase 5: QBR Enhancement (Week 2, Day 5)

**Update QBR Generation** to include Salesforce metrics:

```python
# In step6_generate_qbr_draft():

salesforce_metrics = """
## Technical Delivery Metrics

### Salesforce Deployments (Last 6 Months)

**Custom Objects:** {objects_count}
{object_list}

**Apex Classes:** {apex_count} classes ({lines_of_code} lines)
- Test Coverage: {coverage}%
- Status: {coverage_status}

**Flows:** {flows_count} active
{flow_list}

### Production vs Sandbox
{prod_sandbox_diff}

### Code Quality
- Apex Complexity: Low
- Technical Debt: {technical_debt}
- Deployment Frequency: {deploy_frequency}

### Gap Analysis
{gap_summary}
"""
```

---

## QBR Output With Salesforce

### New Sections

**1. Technical Delivery Dashboard**
```
Salesforce Deployments (Oct - Nov 2024):
📦 Custom Objects: 12 created, 8 modified
   - Loan_Application__c ✅
   - Credit_Score__c ✅
   - Risk_Assessment__c ⚠️ (sandbox only)

⚡ Apex Classes: 15 (2,340 lines)
   - LoanValidation.cls (250 lines, 94% coverage)
   - CreditCheck.cls (180 lines, 89% coverage)
   - Test Coverage: 89% overall ✅

🔄 Flows: 8 active
   - Loan Intake Flow ✅
   - Credit Check Flow ✅
   - Risk Assessment Flow (inactive)

✅ Validation Rules: 23
🎨 Lightning Components: 6
```

**2. Configuration Health**
```
Production vs Sandbox:
✅ In Sync: Loan_Application__c, Credit_Score__c
⚠️ Drift: Risk fields in sandbox not promoted
❌ Missing: 3 features in sandbox need deployment
```

**3. Gap Analysis** (The Killer Feature)
```
Discussion → Plan → Build Validation:

✅ COMPLETE:
- "Data Model" (Oct 15) → MAXIM-234 → Loan_Application__c ✅
- "Credit Scoring" (Oct 18) → MAXIM-245 → Credit_Score__c + CreditCheck.cls ✅

⚠️ GAPS:
- "Risk Assessment" (Oct 20) → MAXIM-256 "Done" → NOT IN PRODUCTION
  * Exists in sandbox only
  * Needs promotion

- "Automated Notifications" (Oct 25) → No Jira ticket → Not built
  * Discussed but never planned
```

---

## Benefits Summary

### For Michael (The Client)
1. **Sees actual technical delivery** - Not just "ticket done"
2. **Validates quality** - Test coverage, code metrics
3. **Catches gaps** - What was promised but not delivered
4. **Understands complexity** - How much was actually built
5. **Production readiness** - What's live vs in development

### For You (The Consultant)
1. **Prove ROI** - Show concrete Salesforce capabilities delivered
2. **Justify hours** - "40 hours → 250 lines of Apex + 12 fields"
3. **Catch issues early** - Missing deployments before QBR
4. **Professional credibility** - Data-driven, not anecdotal
5. **Differentiation** - No other consultant does this

---

## Implementation Timeline

### Recommended: Add SF Before Web UI

**Week 1:**
- Days 1-2: Build SalesforceClient
- Days 3-5: Integrate into CLI pipeline, test

**Week 2:**
- Days 1-3: Build analyzers (metrics, quality)
- Days 4-5: Build cross-validator, generate gap report

**Weeks 3-6:**
- Build web UI with all 5 data sources
- SF data makes dashboards compelling

**Total:** 2 weeks to enhance CLI, 4 weeks for web UI = 6 weeks total

---

## Success Criteria

- [ ] Can connect to both prod and sandbox
- [ ] Retrieves custom objects, Apex, Flows
- [ ] Calculates test coverage and metrics
- [ ] Compares prod vs sandbox (configuration drift)
- [ ] Cross-validates transcripts → Jira → SF
- [ ] Generates gap analysis report
- [ ] QBR includes technical delivery section
- [ ] Identifies "marked done" but not deployed

---

## Next Steps

1. **Add credentials to .env**
2. **Install simple-salesforce**
3. **Create SalesforceClient**
4. **Test connection to both orgs**
5. **Add SF step to main pipeline**
6. **Run full analysis with SF data**
7. **Review enhanced QBR**

Then build web UI to showcase it all!

---

*Salesforce integration plan for QBR automation - capturing the complete delivery story*
