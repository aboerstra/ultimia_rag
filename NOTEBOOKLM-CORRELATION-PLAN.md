# NotebookLM-Assisted Portfolio Correlation

## Overview

This document outlines the new **simplified and fast** portfolio correlation approach using NotebookLM to generate mapping files, eliminating the slow AI-based Stage 2 correlation.

## Problem Statement

The original 3-stage correlator was too slow:
- **Stage 1 (Jira Direct):** Fast ✓
- **Stage 2 (AI Semantic):** Very slow ❌ (100+ API calls, 5-10 minutes)
- **Stage 3 (Proportional):** Fast ✓

Stage 2 made individual AI calls for each unmapped time entry, causing severe performance bottlenecks.

## New Approach: NotebookLM-Generated Mappings

### Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Export Data to NotebookLM Format (DONE)                 │
│     - Portfolio projects                                     │
│     - Jira issues                                            │
│     - Clockify time entries                                  │
│     - Documentation                                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Upload to NotebookLM (USER ACTION NEEDED)               │
│     - Upload all 33 files from data-sources/notebooklm/     │
│     - Follow queries in 00-NOTEBOOKLM-QUERY-GUIDE.md        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. NotebookLM Generates Correlations                       │
│     - Clockify Project → Jira Project mappings              │
│     - Jira Project → Portfolio Project mappings             │
│     - Keywords → Portfolio Project mappings                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Save Mappings to JSON File                              │
│     - Copy NotebookLM output to:                            │
│       data-sources/custom-context/time-entry-mappings.json  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Use Simplified Correlator                               │
│     - Stage 1: Apply mappings (instant, deterministic)      │
│     - Stage 3: Proportional distribution (if needed)        │
│     - NO Stage 2! (eliminated entirely)                     │
└─────────────────────────────────────────────────────────────┘
```

## Files Exported (33 total)

### Location: `data-sources/notebooklm/`

```
notebooklm/
├── 00-EXPORT-SUMMARY.md               # Overview of export
├── 00-NOTEBOOKLM-QUERY-GUIDE.md       # How to query NotebookLM
├── time-entry-mappings-TEMPLATE.json  # Template for final mappings
├── portfolio/
│   └── faye-portfolio-Laura 1 agressive.md  (27 projects)
├── jira/
│   └── jira-UNKNOWN.md  (1,831 issues)
├── clockify/
│   ├── clockify-MAXCOM-021...md  (162 entries, 111.0h)
│   ├── clockify-MAXCOM-020...md  (210 entries, 135.2h)
│   ├── clockify-MAXCOM-023...md  (52 entries, 101.0h)
│   ├── clockify-MAXCOM-022...md  (51 entries, 114.2h)
│   └── clockify-no-project.md  (4 entries)
├── documentation/
│   └── system-context.md
└── transcripts/
    └── [23 transcript analysis files]
```

## NotebookLM Queries

Once you've uploaded all files to NotebookLM, ask it these questions:

### Query 1: Clockify to Jira Mapping
```
Analyze the Clockify time entries and Jira issues. Create a mapping between 
Clockify project names and Jira project keys. Return as JSON:

{
  "Clockify Project Name": "JIRA_PROJECT_KEY",
  ...
}
```

### Query 2: Jira to Portfolio Mapping
```
Analyze the Jira issues and portfolio projects. Map each Jira project key 
to the most relevant portfolio project ID based on semantic similarity, 
timeline alignment, and business domain. Return as JSON:

{
  "JIRA_PROJECT_KEY": "portfolio_project_id",
  ...
}
```

### Query 3: Keyword Mapping
```
Analyze common keywords/phrases in Clockify time entry descriptions and 
map them to portfolio projects. Look for abbreviations, feature names, 
and business process terms. Return as JSON:

{
  "keyword_or_phrase": "portfolio_project_id",
  ...
}
```

## Mapping File Format

Save NotebookLM's output to: `data-sources/custom-context/time-entry-mappings.json`

```json
{
  "clockify_to_jira": {
    "MAXCOM-021 | 30Monthly | FTE Services Bundle – Sr Consultant": "MAXCOM",
    "MAXCOM-020 | 360AS | Axia Platinum": "MAXCOM"
  },
  "jira_to_portfolio": {
    "MAXCOM": "proj_application_intake_optimization"
  },
  "description_keywords": {
    "AIO": "proj_application_intake_optimization",
    "application intake": "proj_application_intake_optimization",
    "booking": "proj_booking_optimization"
  }
}
```

## Simplified Correlator Design

### New Stage 1 (Enhanced with Mappings)
```python
def _stage1_mapping_correlation(clockify_entries, mappings, portfolio_projects):
    """Enhanced Stage 1 using NotebookLM-generated mappings"""
    
    correlated = []
    remaining = []
    
    for entry in clockify_entries:
        project_id = None
        method = None
        
        # Try 1: Jira key in description
        jira_key = extract_jira_key(entry['description'])
        if jira_key and jira_key in jira_issues:
            jira_project = jira_issues[jira_key]['project_key']
            if jira_project in mappings['jira_to_portfolio']:
                project_id = mappings['jira_to_portfolio'][jira_project]
                method = 'jira_key_mapping'
        
        # Try 2: Clockify project name
        if not project_id:
            clockify_project = entry.get('project_name')
            if clockify_project in mappings['clockify_to_jira']:
                jira_project = mappings['clockify_to_jira'][clockify_project]
                if jira_project in mappings['jira_to_portfolio']:
                    project_id = mappings['jira_to_portfolio'][jira_project]
                    method = 'clockify_project_mapping'
        
        # Try 3: Keywords in description
        if not project_id:
            description = entry.get('description', '').lower()
            for keyword, proj_id in mappings['description_keywords'].items():
                if keyword.lower() in description:
                    project_id = proj_id
                    method = 'keyword_mapping'
                    break
        
        if project_id:
            correlated.append({
                'entry': entry,
                'project_id': project_id,
                'method': method,
                'confidence': 1.0
            })
        else:
            remaining.append(entry)
    
    return correlated, remaining
```

### Stage 2: ELIMINATED ✓

### Stage 3: Unchanged (Proportional Distribution)
Handles any remaining unmapped entries by distributing them proportionally.

## Performance Comparison

| Metric | Old (3-Stage with AI) | New (Mapping-Based) |
|--------|----------------------|---------------------|
| Processing Time | 5-10 minutes | 5-10 seconds |
| API Calls | 100-200+ | 0 |
| Cost per Run | High | Zero |
| Deterministic | No (AI varies) | Yes |
| Auditable | Difficult | Easy |
| Updatable | Re-run AI | Edit JSON file |

## Benefits

✅ **100x faster** - No AI calls during correlation  
✅ **Zero runtime cost** - Mappings are pre-generated  
✅ **Deterministic** - Same input always produces same output  
✅ **Transparent** - You can see exactly why each mapping was made  
✅ **Editable** - Update mappings as your understanding improves  
✅ **One-time AI cost** - Use NotebookLM once to generate mappings  

## Next Steps

### Immediate (User Action Required)

1. **Upload to NotebookLM**
   - Go to https://notebooklm.google.com
   - Create a new notebook
   - Upload all 33 files from `data-sources/notebooklm/`

2. **Query NotebookLM**
   - Follow the queries in `00-NOTEBOOKLM-QUERY-GUIDE.md`
   - Have NotebookLM generate the three mapping objects

3. **Save Mappings**
   - Copy NotebookLM's JSON output
   - Save to `data-sources/custom-context/time-entry-mappings.json`

### Development (Next Implementation Phase)

1. **Create simplified correlator**
   - Implement mapping-based Stage 1
   - Remove Stage 2 entirely
   - Keep Stage 3 for proportional distribution

2. **Test with real data**
   - Run correlation with NotebookLM-generated mappings
   - Verify accuracy and coverage

3. **Iterate**
   - Review any unmapped entries
   - Update mappings as needed
   - Re-run (instant with mappings!)

## Future Enhancements

- **Periodic Updates**: Re-run NotebookLM analysis quarterly as projects evolve
- **Hybrid Approach**: Optional lightweight AI for truly ambiguous cases
- **Auto-Learning**: Suggest new mappings based on patterns in unmapped entries
- **Visualization**: Show mapping coverage and confidence levels

## Summary

This NotebookLM-assisted approach eliminates the performance bottleneck while maintaining accuracy. By generating mappings once and reusing them, we achieve both speed and reliability. The user maintains full control and can update mappings as their understanding of the data improves.

---

**Status:** ✅ Export complete (33 files ready)  
**Next:** Upload to NotebookLM and generate mappings  
**When Complete:** Implement simplified correlator using mappings
