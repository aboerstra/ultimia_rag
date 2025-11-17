# Salesforce Integration Assessment

**Question:** Should we add Salesforce CLI/API access before building the web UI?

**Short Answer:** **YES** - High value, relatively simple to add, perfect timing.

---

## Why Salesforce Integration Would Be Valuable

### Current QBR Gaps

**What you have now:**
- ✅ Meeting discussions (transcripts)
- ✅ Technical delivery (Jira)
- ✅ Resource utilization (Clockify)
- ❌ **Business impact** - Missing!

**What Salesforce adds:**
- Revenue impact (deals won/lost)
- Customer outcomes (cases, satisfaction)
- Pipeline health (opportunities)
- Business metrics Michael cares about

### QBR Enhancement Example

**Without Salesforce:**
> "Completed data model integration (23 story points)"

**With Salesforce:**
> "Completed data model integration (23 story points)
> - **Business Impact:** Enabled 5 new deals ($127K pipeline)
> - Reduced case resolution time by 40%
> - Improved data quality score from 72% to 94%"

**This is EXACTLY what Michael wants to see!**

---

## What Salesforce Data to Collect

### High Priority (Include in QBR)

1. **Opportunities/Pipeline**
   - Deals won/lost
   - Pipeline value
   - Close dates
   - Deal stages
   - **QBR Use:** "Project enabled $X in new revenue"

2. **Cases (Support Tickets)**
   - Case volume
   - Resolution time
   - Customer satisfaction
   - Case categories
   - **QBR Use:** "Reduced support burden by X%"

3. **Accounts/Contacts**
   - Customer health scores
   - Engagement metrics
   - Account growth
   - **QBR Use:** "Improved customer satisfaction by X%"

4. **Custom Objects** (if relevant)
   - Integration-specific data
   - Performance metrics
   - Business KPIs
   - **QBR Use:** Project-specific business outcomes

### Medium Priority (Nice to Have)

5. **Reports/Dashboards**
   - Pre-built metrics
   - Executive dashboards
   - **QBR Use:** Pull existing business metrics

6. **Activities**
   - Calls, meetings, emails
   - Customer touchpoints
   - **QBR Use:** Show engagement trends

---

## Implementation Complexity

### Option A: Simple-Salesforce Library (Recommended)

**Effort:** 2-3 hours  
**Complexity:** Low  
**Maintenance:** Minimal

```python
# Install
pip install simple-salesforce

# Usage - fits existing pattern
from simple_salesforce import Salesforce

class SalesforceClient:
    def __init__(self):
        self.sf = Salesforce(
            username=Config.SF_USERNAME,
            password=Config.SF_PASSWORD,
            security_token=Config.SF_SECURITY_TOKEN
        )
    
    def get_opportunities(self, months_back=6):
        """Get opportunities - similar to Jira/Clockify"""
        query = f"""
            SELECT Id, Name, Amount, StageName, CloseDate, 
                   CreatedDate, Owner.Name
            FROM Opportunity 
            WHERE CreatedDate >= LAST_N_MONTHS:{months_back}
        """
        return self.sf.query(query)
```

**Fits perfectly with existing architecture!**

### Option B: Salesforce CLI

**Effort:** 1-2 hours  
**Complexity:** Very Low  
**Limitations:** Less flexible

```bash
# Install
sf plugins install @salesforce/plugin-data

# Usage
sf data query --query "SELECT Id, Name FROM Opportunity" --json
```

**Recommendation: Use Option A (simple-salesforce)**
- More flexible
- Better error handling
- Consistent with Jira/Clockify approach
- Easier to extend

---

## When to Add It

### Recommendation: **Add NOW (Before Web UI)**

**Why now is perfect:**

1. **Same Pattern**
   - Follows Jira/Clockify structure
   - Minimal architectural changes
   - Fits existing data collection phase

2. **Clean Integration**
   - Add connector: `scripts/connectors/salesforce_client.py`
   - Add collection: In `main.py` step 4.5 (between Jira and Clockify)
   - Add synthesis: Claude already handles multi-source

3. **Avoid Rework**
   - If added after web UI, would need to:
     - Update API endpoints
     - Update frontend components
     - Re-test everything
   - Adding now = build web UI once, correctly

4. **Immediate Value**
   - Next QBR has business impact data
   - Validates integration before web UI investment

---

## Implementation Plan

### Phase 0: Salesforce Integration (3-4 hours)

**Task 0.1: Add Salesforce credentials to .env**
```bash
# Add to .env
SF_USERNAME=your.email@domain.com
SF_PASSWORD=yourpassword
SF_SECURITY_TOKEN=yoursecuritytoken
SF_DOMAIN=login  # or test for sandbox
```

**Task 0.2: Install dependency**
```bash
pip install simple-salesforce==1.12.5
```

**Task 0.3: Create Salesforce client** 

Create `scripts/connectors/salesforce_client.py`:

```python
"""Salesforce API client for business metrics."""
from datetime import datetime, timedelta
from typing import Dict, List
from simple_salesforce import Salesforce
from ..config import Config


class SalesforceClient:
    """Client for interacting with Salesforce API."""
    
    def __init__(self):
        self.sf = Salesforce(
            username=Config.SF_USERNAME,
            password=Config.SF_PASSWORD,
            security_token=Config.SF_SECURITY_TOKEN,
            domain=Config.SF_DOMAIN
        )
    
    def get_opportunities(self, months_back: int = 6) -> List[Dict]:
        """Get opportunities for date range."""
        query = f"""
            SELECT Id, Name, Amount, StageName, CloseDate, 
                   CreatedDate, Owner.Name, Type, LeadSource
            FROM Opportunity 
            WHERE CreatedDate >= LAST_N_MONTHS:{months_back}
            ORDER BY CreatedDate DESC
        """
        
        result = self.sf.query(query)
        return [self._process_opportunity(opp) for opp in result['records']]
    
    def _process_opportunity(self, opp: Dict) -> Dict:
        """Process raw opportunity into structured data."""
        return {
            'id': opp['Id'],
            'name': opp['Name'],
            'amount': opp.get('Amount', 0),
            'stage': opp['StageName'],
            'close_date': opp.get('CloseDate'),
            'created_date': opp['CreatedDate'],
            'owner': opp.get('Owner', {}).get('Name'),
            'type': opp.get('Type'),
            'source': opp.get('LeadSource')
        }
    
    def get_cases(self, months_back: int = 6) -> List[Dict]:
        """Get support cases for date range."""
        query = f"""
            SELECT Id, CaseNumber, Subject, Status, Priority,
                   CreatedDate, ClosedDate, Origin, Type
            FROM Case
            WHERE CreatedDate >= LAST_N_MONTHS:{months_back}
            ORDER BY CreatedDate DESC
        """
        
        result = self.sf.query(query)
        return [self._process_case(case) for case in result['records']]
    
    def _process_case(self, case: Dict) -> Dict:
        """Process raw case into structured data."""
        # Calculate resolution time if closed
        resolution_time = None
        if case.get('ClosedDate'):
            created = datetime.fromisoformat(case['CreatedDate'].replace('Z', '+00:00'))
            closed = datetime.fromisoformat(case['ClosedDate'].replace('Z', '+00:00'))
            resolution_time = (closed - created).total_seconds() / 3600  # hours
        
        return {
            'id': case['Id'],
            'number': case['CaseNumber'],
            'subject': case['Subject'],
            'status': case['Status'],
            'priority': case.get('Priority'),
            'created_date': case['CreatedDate'],
            'closed_date': case.get('ClosedDate'),
            'resolution_hours': resolution_time,
            'origin': case.get('Origin'),
            'type': case.get('Type')
        }
    
    def get_business_metrics(self) -> Dict:
        """Calculate high-level business metrics."""
        opps = self.get_opportunities()
        cases = self.get_cases()
        
        # Opportunity metrics
        total_pipeline = sum(o['amount'] or 0 for o in opps)
        won_deals = [o for o in opps if o['stage'] == 'Closed Won']
        total_won = sum(o['amount'] or 0 for o in won_deals)
        
        # Case metrics
        closed_cases = [c for c in cases if c['closed_date']]
        avg_resolution = sum(c['resolution_hours'] or 0 for c in closed_cases) / len(closed_cases) if closed_cases else 0
        
        return {
            'opportunities': {
                'total_count': len(opps),
                'total_pipeline': total_pipeline,
                'won_count': len(won_deals),
                'total_won': total_won,
                'win_rate': len(won_deals) / len(opps) if opps else 0
            },
            'cases': {
                'total_count': len(cases),
                'closed_count': len(closed_cases),
                'avg_resolution_hours': avg_resolution,
                'open_count': len(cases) - len(closed_cases)
            }
        }
```

**Task 0.4: Update Config** (`scripts/config.py`)

```python
# Add to Config class
SF_USERNAME = os.getenv('SF_USERNAME')
SF_PASSWORD = os.getenv('SF_PASSWORD')
SF_SECURITY_TOKEN = os.getenv('SF_SECURITY_TOKEN')
SF_DOMAIN = os.getenv('SF_DOMAIN', 'login')
```

**Task 0.5: Add to orchestrator** (`scripts/main.py`)

```python
# Add import
from connectors.salesforce_client import SalesforceClient

# In __init__
self.salesforce = SalesforceClient()

# Add new step (between 4 and 5)
def step4_5_collect_salesforce_data(self):
    """Step 4.5: Collect data from Salesforce."""
    print("\n" + "="*60)
    print("STEP 4.5: Collecting Salesforce data")
