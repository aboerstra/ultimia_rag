# Portfolio Correlation - Persistence & Conversational Access

## The Problem You Identified

**Question**: "Once it does this analysis, how does it get referenced after? How does it become relevant during a conversation? Is this analysis persistent?"

**Answer**: Great question! The initial implementation ran correlations on-demand but didn't save them. Now we've added a **persistence layer** that:

1. ✅ **Saves** correlations to disk
2. ✅ **Indexes** them in RAG for semantic search  
3. ✅ **Makes them conversationally accessible** to the AI

## How It Works

### 1. Run Correlation & Auto-Save

```python
from scripts.analyzers.portfolio_correlator import PortfolioCorrelator
from scripts.analyzers.correlation_persistence import CorrelationPersistence, correlate_and_save
from scripts.connectors.gemini_client import GeminiClient
from scripts.connectors.rag_manager import RAGManager

# Initialize
gemini = GeminiClient(api_key=api_key)
rag = RAGManager()
correlator = PortfolioCorrelator(gemini_client=gemini, rag_manager=rag)
persistence = CorrelationPersistence(rag_manager=rag)

# Correlate AND automatically save/index
result = correlate_and_save(
    portfolio_correlator=correlator,
    persistence_manager=persistence,
    portfolio_project=project,
    jira_issues=jira_issues,
    clockify_entries=clockify_entries
)
```

### 2. Where Correlations Are Saved

**File Storage**: `data-sources/custom-context/portfolio-correlations.json`
```json
{
  "AI Based Application Intake": {
    "project_name": "AI Based Application Intake",
    "analyzed_at": "2025-11-13T19:00:00",
    "matched_jira_keys": ["MAXCOM-92", "MAXCOM-134", ...],
    "matched_jira_count": 7,
    "clockify_hours": 59.8,
    "confidence_score": 0.90,
    "variance": {
      "estimated_hours": 150,
      "actual_hours": 59.8,
      "delta_hours": -90.2,
      "delta_percent": -60.1,
      "status": "under_budget"
    },
    "reasoning": "AI explanation..."
  }
}
```

**RAG Index**: Correlation is indexed as a searchable document:

```markdown
PORTFOLIO CORRELATION: AI Based Application Intake

**Analysis Date**: 2025-11-13

**Estimated Hours**: 150.0h  
**Actual Hours Logged**: 59.8h  
**Variance**: -90.2h (-60.1%)  
**Status**: UNDER BUDGET

**Matched Jira Issues** (7):
MAXCOM-92, MAXCOM-134, MAXCOM-149, ...

**Clockify Time Tracking**: 59.8h across 0 entries

**Confidence**: 90%

**AI Analysis**: The correlation is based on strong evidence...
```

## Conversational Access - How It Works

Once indexed in RAG, the correlation becomes **searchable and conversationally relevant**.

### Example Conversation:

**User**: "How many hours did we spend on AI Based Application Intake?"

**System**:
1. Queries RAG with the question
2. RAG returns the indexed correlation summary
3. AI reads: "Actual Hours Logged: 59.8h"
4. AI responds: "We spent 59.8 hours on AI Based Application Intake. This was under budget - we estimated 150 hours but only used 59.8 hours."

**User**: "Which Jira issues were part of that project?"

**System**:
1. RAG search finds the same correlation
2. AI reads: "Matched Jira Issues: MAXCOM-92, MAXCOM-134, MAXCOM-149..."
3. AI responds: "The AI Based Application Intake project included 7 Jira issues: MAXCOM-92 (AIO Integration Phase 1), MAXCOM-134 (Address & Phone cleanup for AIO)..."

**User**: "Are we over or under budget on our portfolio?"

**System**:
1. RAG finds ALL indexed correlations
2. AI analyzes variance across projects
3. AI responds: "Looking at analyzed projects, AI Based Application Intake is 60% under budget (-90h), while [other project] is 20% over budget (+15h)..."

## Key Benefits

### 1. Persistent Analysis
- Correlations are saved permanently
- No need to re-run expensive AI correlations
- Historical tracking of portfolio performance

### 2. Conversational Intelligence
- AI can reference correlation data naturally
- Answers questions about estimates vs actuals
- Provides context-aware responses

### 3. Cross-Reference Capability
- Correlations link portfolio → Jira → Clockify
- AI understands relationships between systems
- Can trace work from estimate to completion

### 4. Reporting & Analytics
```python
# Generate summary report
report = persistence.get_summary_report()
print(report)
```

Output:
```markdown
# Portfolio Correlation Summary

Total Projects Analyzed: 3

## ✅ AI Based Application Intake
- **Estimated**: 150.0h
- **Actual**: 59.8h
- **Variance**: -90.2h (-60.1%)
- **Confidence**: 90%
- **Jira Issues**: 7
- **Analyzed**: 2025-11-13

## ⚠️ Deal Intake Automation
- **Estimated**: 100.0h
- **Actual**: 120.5h
- **Variance**: +20.5h (+20.5%)
- **Confidence**: 85%
- **Jira Issues**: 12
- **Analyzed**: 2025-11-13
```

## Integration with Chat System

When the chat system (frontend) asks a question:

```
User: "What's the status of AI Based Application Intake?"

Backend Flow:
1. api/main.py receives chat message
2. RAGManager.search("status of AI Based Application Intake") 
3. Returns: Indexed correlation summary
4. Gemini reads context and generates response
5. Response: "AI Based Application Intake is 60% under budget..."
```

The correlation data is now **part of the AI's knowledge base**, just like Confluence articles and meeting transcripts.

## Workflow Summary

```
Step 1: Run Correlation
   ↓
Step 2: Save to JSON file (persistence)
   ↓
Step 3: Index in RAG (searchability)
   ↓
Step 4: User asks question in chat
   ↓
Step 5: RAG retrieves correlation
   ↓
Step 6: AI answers using correlation data
```

## Future Enhancements

1. **Auto-Refresh**: Re-correlate weekly to track ongoing work
2. **Delta Tracking**: Compare correlation over time to see progress
3. **Alerts**: Notify when variance exceeds thresholds
4. **Dashboard**: Visualize all correlations in UI
5. **Export**: Generate Excel/PDF reports from correlations

## Code Example: Batch Process & Index

```python
# Correlate ALL portfolio projects and index them
from scripts.analyzers.portfolio_correlator import load_portfolio_data

portfolio_projects = load_portfolio_data()
jira_issues = load_jira_data()
clockify_entries = load_clockify_data()

for project in portfolio_projects:
    result = correlate_and_save(
        portfolio_correlator=correlator,
        persistence_manager=persistence,
        portfolio_project=project,
        jira_issues=jira_issues,
        clockify_entries=clockify_entries
    )
    print(f"✅ Correlated {project['name']}: {result['confidence_score']:.0%} confidence")

# Now ALL projects are indexed and conversationally accessible!
print(persistence.get_summary_report())
```

## Answer to Your Question

**"How does this analysis become relevant during a conversation?"**

Once a correlation is run and indexed:

1. **It's searchable** - RAG can find it when relevant  
2. **It's contextual** - AI reads it to answer questions
3. **It's persistent** - Saved permanently, no re-computation needed
4. **It's integrated** - Part of the AI's knowledge base alongside all other data

When you ask "How many hours on Project X?", the AI doesn't just search Jira/Clock ify anymore - it finds the **CORRELATED** data that already connected estimates to actuals, providing instant, accurate answers.

---

**Status**: Persistence layer implemented  
**File**: `scripts/analyzers/correlation_persistence.py`  
**Storage**: `data-sources/custom-context/portfolio-correlations.json`  
**RAG Indexed**: Yes, automatic on save
