# Portfolio Snapshot Management System

## Overview

The Portfolio Snapshot Manager enables temporal tracking of your project roadmap by maintaining multiple portfolio versions representing different points in time. This allows you to:

- Track how your roadmap evolves over time
- Compare planned vs actual project states
- Maintain historical context for strategic planning
- Update existing snapshots or add new future-state versions

## How It Works

### Filename Convention

Portfolio files **must** include a date in the filename to be recognized as snapshots:

**Supported Formats:**
```
faye-portfolio-2025-11-11.json     # Date format: YYYY-MM-DD
portfolio-2025-11-11.json          # Prefix doesn't matter
portfolio-2026-Q1.json             # Quarter format: YYYY-QX
roadmap-2025-12-15.json            # Any prefix works
```

**Not Recognized as Snapshots:**
```
portfolio.json                      # No date
my-projects.json                    # No date
```

### Automatic Snapshot Management

When you upload a portfolio file:

1. **Date Extraction**: System extracts the date from filename
2. **Duplicate Detection**: Checks if a snapshot with this date already exists
3. **Smart Replacement**: 
   - If date exists → Old snapshot is deleted, new one replaces it
   - If date is new → Both snapshots coexist
4. **Automatic Indexing**: File is immediately indexed and searchable in AI Chat

### Example Workflow

#### Scenario 1: Update Existing Snapshot

```
1. Current state: faye-portfolio-2025-11-11.json (uploaded Nov 11)

2. You make updates to the November roadmap

3. Delete old file via UI

4. Upload: faye-portfolio-2025-11-11.json (updated version)
   → System detects matching date "2025-11-11"
   → Deletes old snapshot documents
   → Indexes new version
   → Result: Nov 11 snapshot is refreshed
```

#### Scenario 2: Add New Future Snapshot

```
1. Current state: faye-portfolio-2025-11-11.json

2. You create a Q1 2026 planning snapshot

3. Upload: faye-portfolio-2026-Q1.json
   → System detects new date "2026-Q1"
   → No cleanup needed (different date)
   → Indexes alongside existing snapshot
   → Result: Both snapshots coexist
```

## AI Chat Integration

Portfolio snapshots are automatically searchable in AI Chat with temporal context:

### Query Examples

**Compare snapshots:**
```
"What changed in the API Gateway project between Nov and Q1?"
"Show me all projects in the November snapshot"
"Which projects were planned for 2026-Q1?"
```

**Temporal filtering:**
```
"What was the status of the Credit System in November?"
"Show me the 2026-Q1 roadmap"
```

### Search Results Format

AI Chat results automatically include snapshot dates:

```
--- PORTFOLIO: API Gateway | Value Stream: Innovation | Snapshot: 2025-11-11 ---
Project: API Gateway
Value Stream: Product & Program Innovation
Snapshot Date: 2025-11-11
Status: in-progress
Priority: high
Progress: 45%
...
```

## Technical Details

### Document IDs

Each project in a snapshot gets a unique ID incorporating the snapshot date:

```
portfolio_2025-11-11_proj_asana-1210391095918640
portfolio_2026-Q1_proj_asana-1210391095918640
```

This ensures the same project can exist in multiple snapshots without conflicts.

### Metadata Structure

Each indexed project includes:

```json
{
  "source": "portfolio-snapshot",
  "file": "faye-portfolio-2025-11-11.json",
  "snapshot_date": "2025-11-11",
  "project_name": "API Gateway",
  "value_stream": "Product & Program Innovation",
  "status": "in-progress",
  "type": "project"
}
```

### Cleanup Logic

When a file with matching snapshot date is uploaded:

```python
# Extract date from filename
snapshot_date = extract_snapshot_date("faye-portfolio-2025-11-13.json")
# → "2025-11-13"

# Find and delete existing documents with this date
delete_portfolio_snapshot(snapshot_date)
# → Deletes all documents where metadata.snapshot_date == "2025-11-13"

# Index new file
index_portfolio(file, snapshot_date)
# → Creates new documents with snapshot_date = "2025-11-13"
```

## Best Practices

### Naming Conventions

**✅ Recommended:**
- Use consistent prefixes: `faye-portfolio-YYYY-MM-DD.json`
- Include client name for clarity
- Use dates for specific snapshots: `2025-11-11`
- Use quarters for planning periods: `2026-Q1`

**❌ Avoid:**
- Generic names without dates: `portfolio.json`
- Ambiguous dates: `portfolio-nov.json`
- Special characters: `portfolio_11/11/2025.json`

### Snapshot Strategy

**Monthly Snapshots:**
```
portfolio-2025-11-01.json   # Start of month baseline
portfolio-2025-12-01.json   # Next month
portfolio-2026-01-01.json   # New year
```

**Quarterly Planning:**
```
portfolio-2025-Q4.json      # Q4 plan
portfolio-2026-Q1.json      # Q1 plan
portfolio-2026-Q2.json      # Q2 plan
```

**Ad-hoc Updates:**
```
portfolio-2025-11-11.json   # Initial
portfolio-2025-11-15.json   # Mid-month update
```

## Workflow Integration

### 1. Upload New Snapshot

**Via UI:**
1. Go to **Context Files** tab
2. Click **Choose File**
3. Select your portfolio JSON (with date in filename)
4. Upload automatically:
   - Detects if portfolio file
   - Extracts snapshot date
   - Cleans up old version if date exists
   - Indexes new version
5. No manual re-indexing needed!

### 2. Update Existing Snapshot

**To update without changing date:**
1. Delete old file from Context Files list
2. Upload new file with **same filename**
3. System automatically replaces old snapshot

### 3. Query Snapshots

**In AI Chat:**
```
"Show me the November roadmap"
"Compare API Gateway between Nov and Q1"
"What projects are in-progress in the latest snapshot?"
```

## Migration Guide

### Existing Portfolio Files

If you have an existing `portfolio.json` without a date:

**Option 1: Add Date to Filename**
1. Download existing file
2. Rename to include date: `portfolio-2025-11-11.json`
3. Delete old file
4. Upload renamed file
5. System will recognize as snapshot

**Option 2: Keep Generic Name**
- File will be indexed as generic custom context
- Won't have snapshot features
- Won't auto-cleanup on updates

## Troubleshooting

### "Old snapshot not being replaced"

**Possible causes:**
1. Date format not recognized
   - ✅ Solution: Use `YYYY-MM-DD` or `YYYY-QX` format
2. Date in different part of filename
   - ✅ Solution: Ensure date is clearly visible in filename

### "Can't find my snapshot in AI Chat"

**Check:**
1. Was file indexed? (Upload should show "Indexing..." message)
2. Is it a portfolio file? (Must have `projects` and `valueStreams` keys)
3. Try re-uploading and manually click "Index Knowledge Base"

### "Multiple versions of same project showing up"

**This is normal!** If you have:
- `portfolio-2025-11-11.json`
- `portfolio-2026-Q1.json`

Both contain the same project → AI will show both versions with their snapshot dates

To see only one version, be specific in your query:
- "Show November snapshot" (filters to 2025-11-11)
- "Show latest snapshot" (AI will use most recent date)

## API Reference

### Upload Endpoint

```http
POST /api/custom-context/upload
Content-Type: multipart/form-data

Response (for portfolio file):
{
  "filename": "faye-portfolio-2025-11-11.json",
  "status": "uploaded",
  "snapshot_date": "2025-11-11",
  "is_portfolio": true,
  "message": "Portfolio snapshot (2025-11-11) uploaded. Old snapshot replaced. Indexing..."
}
```

### RAGManager Methods

```python
from scripts.connectors.rag_manager import RAGManager

rag = RAGManager()

# Check if file is a portfolio
is_portfolio = rag.is_portfolio_file(json_data)

# Extract snapshot date from filename
date = rag.extract_snapshot_date("faye-portfolio-2025-11-11.json")
# Returns: "2025-11-11"

# Delete a specific snapshot
rag.delete_portfolio_snapshot("2025-11-11")
```

## Future Enhancements

Potential features for future versions:

1. **Snapshot Comparison UI**: Side-by-side comparison view
2. **Snapshot Timeline**: Visual timeline of all snapshots
3. **Snapshot Diff**: Highlight what changed between versions
4. **Snapshot Export**: Export specific snapshot or comparison
5. **Snapshot Metadata**: Add custom tags, notes to snapshots

## Summary

The Portfolio Snapshot Manager gives you temporal superpowers:

✅ **Automatic**: Upload with date in filename, system handles the rest
✅ **Intelligent**: Same date = replace, different date = coexist
✅ **Searchable**: Query by date, compare versions, track evolution
✅ **Flexible**: Monthly, quarterly, or ad-hoc snapshots
✅ **Clean**: No manual cleanup, no duplicate data

Just use clear dates in your filenames and let the system manage the rest!
