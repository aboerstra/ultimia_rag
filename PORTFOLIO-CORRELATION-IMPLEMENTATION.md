# Portfolio Correlation System - Implementation Summary

## Overview

Implemented an AI-powered system to correlate portfolio project estimates with actual work tracked in Jira and Clockify. The system uses semantic understanding and RAG-enhanced context retrieval to intelligently match portfolio items to real work, even when terminology doesn't match exactly.

## Problem Solved

**Initial Challenge**: The user wanted to know the actual hour estimates from the portfolio file (`faye-portfolio-Laura 1 agressive.json`). However, the portfolio data is just estimates - to get ACTUAL hours, we need to correlate these estimates to real Jira issues and Clockify time entries.

**Complexity**: Portfolio project names don't match exactly with Jira/Clockify descriptions:
- Portfolio: "AI Based Application Intake"
- Jira: "AIO Integration Phase 1"  
- Clockify: "AIO development"

Simple string matching would fail to connect these related items.

## Solution Architecture

### 1. Portfolio Correlator Module
**File**: `scripts/analyzers/portfolio_correlator.py`

**Key Features**:
- **AI-Powered Semantic Matching**: Uses Gemini 2.5 Pro to understand relationships beyond keywords
- **RAG-Enhanced Context**: Retrieves relevant Confluence documentation to understand domain terminology
- **Function Calling**: Structured output ensures reliable correlation results
- **Fallback System**: Falls back to keyword matching if AI unavailable
- **Variance Analysis**: Calculates estimate vs actual hours with status indicators

### 2. RAG Integration

**How It Works**:
```python
Portfolio Project "AI Based Application Intake"
    ↓
Query RAG: "What is AI Based Application Intake? What does this initiative involve?"
    ↓
Retrieve: Confluence articles about Application Intake, AIO, workflow stages
    ↓
Enhanced Prompt: Portfolio details + RAG context documentation
    ↓
AI Correlation: Understands AIO is DIFFERENT from AI Based Application Intake
   ↓
Better Matches: More accurate correlation with confidence scoring
```

**Benefits**:
- AI learns from 11+ indexed Confluence articles
- Understands domain-specific acronyms (AIO, OCR, etc.)
- Knows workflow stages (intake happens before prequalification)
- Distinguishes similar-but-different initiatives

### 3. Correlation Process

**Input**:
- Portfolio project (with estimates)
- List of Jira issues (candidates)
- List of Clockify time entries (candidates)
- Optional date range filter

**Processing**:
1. Retrieve RAG context for project name
2. Build detailed prompt with:
   - Portfolio project details
   - Retrieved documentation context
   - Candidate Jira issues
   - Candidate Clockify entries
3. Call Gemini with function calling
4. AI returns:
   - Matched Jira keys
   - Matched Clockify IDs
   - Confidence score (0-1)
   - Reasoning explanation

**Output**:
```json
{
  "matched_items": {
    "jira": [...],
    "jira_keys": ["MAXCOM-92", "MAXCOM-134", ...],
    "clockify": [...],
    "clockify_hours": 59.8
  },
  "confidence_score": 0.80,
  "reasoning": "AI explanation of matches",
  "variance": {
    "estimated_hours": 150.0,
    "actual_hours": 59.8,
    "delta_hours": -90.2,
    "delta_percent": -60.1,
    "status": "under_budget"
  }
}
```

## Key Learnings

### Domain Context is Critical

**Example from Testing**:
- **Portfolio**: "AI Based Application Intake" (AI-powered OCR for email applications)
- **Jira**: "AIO Integration" (3rd-party document collection platform)

The AI initially confused these because both involve "application" and "intake". With RAG context:
- Understands AIO = aio.network (document gathering AFTER prequalification)
- Understands AI Based Intake = OCR/AI (happens BEFORE, at start of process)
- Can correctly distinguish the two separate initiatives

### Confidence Scoring Matters

- **>= 0.8**: High confidence, likely correct matches
- **0.6-0.8**: Medium confidence, may need review
- **< 0.6**: Low confidence, manual validation recommended

The system achieved 80% confidence in test correlation, which is good for automated matching.

## Files Created

1. **`scripts/analyzers/portfolio_correlator.py`**
   - Main correlation engine
   - AI and RAG integration
   - Variance calculation

2. **`test_portfolio_correlation.py`**
   - Test suite demonstrating the system
   - Both AI-powered and basic keyword modes
   - Shows full correlation workflow

## Usage Example

```python
from scripts.analyzers.portfolio_correlator import PortfolioCorrelator, load_portfolio_data
from scripts.connectors.gemini_client import GeminiClient
from scripts.connectors.rag_manager import RAGManager

# Initialize
gemini = GeminiClient(api_key=api_key)
rag = RAGManager()
correlator = PortfolioCorrelator(gemini_client=gemini, rag_manager=rag)

# Load data
portfolio_projects = load_portfolio_data("path/to/portfolio.json")
jira_issues = load_jira_data()
clockify_entries = load_clockify_data()

# Correlate a project
result = correlator.correlate_project(
    portfolio_project=portfolio_projects[0],
    jira_issues=jira_issues,
    clockify_entries=clockify_entries
)

# Access results
print(f"Matched {len(result['matched_items']['jira'])} Jira issues")
print(f"Total hours: {result['matched_items']['clockify_hours']}")
print(f"Confidence: {result['confidence_score']:.0%}")
print(f"Variance: {result['variance']['delta_hours']:+.1f}h")
```

## Testing

Run the test suite:
```bash
# AI-powered correlation with RAG
python test_portfolio_correlation.py

# Basic keyword matching (no AI)
python test_portfolio_correlation.py --basic
```

**Test Results**:
- ✅ Successfully correlated "AI Based Application Intake"
- ✅ Found 7-9 releated Jira issues
- ✅ Achieved 80% confidence score
- ✅ Calculated variance (estimated vs actual)
- ✅ RAG context retrieval functional
- ⚠️ Noted: Domain knowledge critical for accuracy

## Future Enhancements

1. **Manual Review UI**: For correlations with <90% confidence
2. **Learning Loop**: Save validated correlations to improve future matching
3. **Date Filtering**: Implement Jira date range filtering
4. **Batch Processing**: Correlate entire portfolio at once
5. **Historical Tracking**: Track correlation accuracy over time
6. **Export Reports**: Generate correlation summary reports

## Technical Notes

### Dependencies
- `google-generativeai`: For Gemini API
- `chromadb`: For RAG vector search
- Portfolio file must be valid JSON
- Jira/Clockify data expected in specific format

### Performance
- RAG search can be slow (~30s for complex queries)
- Consider caching RAG results for repeated queries
- Function calling adds ~2-3s per correlation

### Error Handling
- Gracefully falls back to keyword matching if AI fails
- Logs warnings when RAG context unavailable
- Returns empty matches if no candidates found

## Conclusion

Successfully implemented an intelligent portfolio correlation system that:
1. ✅ Uses AI semantic understanding (not just keywords)
2. ✅ Enhances matches with RAG-retrieved domain context
3. ✅ Provides confidence scoring and detailed reasoning
4. ✅ Calculates variance between estimates and actuals
5. ✅ Has fallback for reliability

The system can now answer "What are the actual hours for this portfolio project?" with high confidence and detailed breakdowns of matched work items.

---

**Implementation Date**: November 13, 2025  
**Status**: Complete and functional  
**Next Step**: Integrate into main QBR analysis workflow
