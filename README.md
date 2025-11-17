# Maxim QBR Knowledge Base

## Purpose
This repository organizes all data sources for creating comprehensive Quarterly Business Reviews (QBRs) for Michael Kianmahd at Maxim.

## Structure

### `/data-sources/`
Raw and processed data from multiple sources:

- **`transcripts/`** - Meeting transcripts (23 PDFs, chronologically numbered)
  - `raw/` - Original PDF transcripts
  - `extracted/` - Extracted insights and themes
  
- **`jira/`** - Project management data
  - `raw/` - Jira exports (CSV/JSON)
  - Analysis documents
  
- **`confluence/`** - Technical documentation
  - `raw/` - Confluence exports
  - Structured summaries
  
- **`clockify/`** - Time tracking data
  - `raw/` - Clockify exports
  - Budget analysis
  
- **`synthesis/`** - Cross-source analysis
  - Reality checks (planned vs. actual)
  - Gap analysis
  - Risk assessments

### `/qbr-output/`
Final QBR presentation materials:

- `executive-summary.md` - One-page overview
- `progress-dashboard.md` - Metrics and status
- `financial-summary.md` - Budget vs. actual
- `workstreams/` - Details per value stream
- `appendix/` - Supporting data

## Key Attendees (from transcripts)
- **MK** = Michael Kianmahd (Client)
- **LD** = Laura Dolphin (Faye - Lead Consultant)
- **AB** = Adrian Boerstra (Faye - Technical)
- **LE** = Lyndon Elam (Maxim)
- **KD** = Kaleb Dague (Faye)
- **DK** = Dave Kaplan (Faye)

## Workflow

1. **Gather** - Import data from all sources
2. **Extract** - Pull key insights from each source
3. **Synthesize** - Cross-reference and analyze
4. **Present** - Build QBR narrative

## Next Steps

1. Extract insights from transcripts → `data-sources/transcripts/extracted/`
2. Import Jira data → `data-sources/jira/raw/`
3. Import Confluence docs → `data-sources/confluence/raw/`
4. Import Clockify logs → `data-sources/clockify/raw/`
5. Create synthesis documents
6. Build QBR presentation
