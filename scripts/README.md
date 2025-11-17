# QBR Automation Scripts

Automated pipeline for collecting and analyzing data from multiple sources to generate Quarterly Business Review (QBR) presentations.

## Quick Start

### 1. Install Dependencies

```bash
# From project root
pip install -r requirements.txt
```

### 2. Run Complete Pipeline

```bash
# From project root
python scripts/main.py
```

This will:
1. Extract text from 23 PDF transcripts
2. Analyze each with Claude (AI insights)
3. Synthesize cross-transcript patterns
4. Collect Jira project data
5. Collect Clockify time tracking data
6. Generate complete QBR draft

**Expected runtime:** 5-15 minutes (depending on API response times)

**Cost:** ~$1-2 in OpenRouter/Claude API calls

## What It Does

### Step 1: Transcript Extraction
- Reads all PDFs from `data-sources/transcripts/raw/`
- Extracts text using pdfplumber
- Saves markdown versions to `data-sources/transcripts/extracted/`

### Step 2: AI Analysis
- Sends each transcript to Claude for analysis
- Extracts: decisions, action items, concerns, Michael's priorities
- Saves individual analyses as JSON

### Step 3: Synthesis
- Claude analyzes all transcripts together
- Identifies patterns, recurring themes, evolution over time
- Saves comprehensive synthesis to `data-sources/synthesis/`

### Step 4: Jira Data
- Fetches all projects
- Pulls 6 months of issues
- Calculates velocity, status distribution
- Saves to `data-sources/jira/raw/`

### Step 5: Clockify Data
- Fetches all projects
- Pulls 6 months of time entries
- Calculates hours by project, billable vs non-billable
- Saves to `data-sources/clockify/raw/`

### Step 6: QBR Generation
- Combines all data sources
- Claude generates comprehensive QBR draft
- Saves to `qbr-output/qbr-draft.md`

## Architecture

```
scripts/
├── main.py                   # Main orchestrator
├── config.py                 # Configuration management
├── connectors/              # API clients
│   ├── llm_client.py        # OpenRouter/Claude
│   ├── jira_client.py       # Jira API
│   └── clockify_client.py   # Clockify API
├── collectors/              # Data processors
│   └── pdf_processor.py     # PDF text extraction
├── analyzers/               # Analysis modules (future)
└── generators/              # Output generators (future)
```

## Configuration

All configuration is in `.env` file (already set up):

- OpenRouter API key (Claude access)
- Jira credentials
- Clockify API key
- Date range (6 months)

## Output Files

After running, you'll have:

### Extracted Transcripts
`data-sources/transcripts/extracted/`
- `01-MK-LD-LE.md` through `23-MK-LD.md`
- `01-MK-LD-LE_analysis.json` (AI analysis for each)

### Synthesis
`data-sources/synthesis/`
- `transcript-synthesis.md` (comprehensive cross-analysis)

### Jira Data
`data-sources/jira/raw/`
- `projects.json`
- `issues.json`
- `boards.json`

### Clockify Data
`data-sources/clockify/raw/`
- `projects.json`
- `time_entries.json`
- `project_summary.json`

### Final QBR
`qbr-output/`
- `qbr-draft.md` (complete QBR presentation)

## Customization

### Analyzing Specific Projects

Edit `scripts/main.py`, in `step4_collect_jira_data()`:

```python
# Instead of all projects:
issues = self.jira.get_issues(months_back=Config.DATE_RANGE_MONTHS)

# Use specific projects:
issues = self.jira.get_issues(
    project_keys=['MAX', 'FAYE'],  # Your project keys
    months_back=6
)
```

### Changing Date Range

Edit `.env`:
```
DATE_RANGE_MONTHS=3  # Last 3 months instead of 6
```

### Running Individual Steps

You can run steps individually by modifying `main.py`:

```python
if __name__ == '__main__':
    orchestrator = QBROrchestrator()
    
    # Run only transcript analysis
    transcripts = orchestrator.step1_extract_transcripts()
    analyses = orchestrator.step2_analyze_transcripts(transcripts)
    orchestrator.step3_synthesize_insights(analyses)
```

## Troubleshooting

### Import Errors
```bash
# Make sure you're in project root when running
cd /Users/adrianboerstra/projects/maximQBR
python scripts/main.py
```

### API Errors
- Check `.env` credentials are correct
- Verify API keys are active
- Check internet connection

### PDF Extraction Issues
- Ensure PDFs are in `data-sources/transcripts/raw/`
- PDFs should be readable (not scanned images)

## Next Steps

After running the pipeline:

1. Review `qbr-output/qbr-draft.md`
2. Refine with additional context
3. Add visualizations if needed
4. Present to Michael!

## Future Enhancements

Potential additions:
- Confluence documentation integration
- Automated visualization generation
- Trend analysis over multiple QBRs
- RAG system for interactive Q&A
- Slack integration for updates
