# Quick Start Guide - Maxim QBR Automation

## What You Have

A complete automated pipeline that will:
1. ✅ Extract and analyze all 23 meeting transcripts with AI
2. ✅ Pull data from Jira (issues, projects, velocity)
3. ✅ Pull data from Clockify (time tracking, budget)
4. ✅ Generate a comprehensive QBR presentation draft

## Run It Now!

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run the Pipeline

```bash
python scripts/main.py
```

That's it! The pipeline will run for 5-15 minutes and generate everything you need.

## What You'll Get

### Immediate Outputs

**QBR Draft** → `qbr-output/qbr-draft.md`
- Executive summary
- Progress dashboard
- Value stream updates
- Business impact analysis
- 30/60/90 day roadmap

**Transcript Insights** → `data-sources/synthesis/transcript-synthesis.md`
- Timeline of key events
- Recurring themes
- Michael's priorities
- Commitments vs delivery
- Unresolved issues

**Raw Data**
- Jira: `data-sources/jira/raw/*.json`
- Clockify: `data-sources/clockify/raw/*.json`
- Transcripts: `data-sources/transcripts/extracted/*.md`

## Understanding the Output

The QBR draft will be tailored to what Michael Kianmahd cares about (based on transcript analysis):

✅ **Transparency** - Clear visibility into progress and blockers  
✅ **Accountability** - Who did what, why milestones were/weren't hit  
✅ **Realistic timelines** - Conservative estimates with confidence levels  
✅ **Business impact** - How work ties to revenue, efficiency, scalability  
✅ **Visual roadmaps** - What's done, in-progress, blocked, backlog  

## Next Steps

1. **Review the QBR draft** - It's AI-generated, so you'll want to refine it
2. **Add context** - Include any recent developments not in the data
3. **Verify metrics** - Double-check that Jira/Clockify data looks right
4. **Customize** - Adjust emphasis based on what you want to highlight
5. **Add visuals** - Consider charts/graphs for the dashboard section

## Customization

### Focus on Specific Projects

Edit `scripts/main.py`, line ~129:

```python
# Change this:
issues = self.jira.get_issues(months_back=Config.DATE_RANGE_MONTHS)

# To something like:
issues = self.jira.get_issues(
    project_keys=['MAXIM', 'INT'],  # Your project keys
    months_back=6
)
```

### Change Time Range

Edit `.env`:
```
DATE_RANGE_MONTHS=3  # For last 3 months
```

## Costs

- **OpenRouter/Claude API**: ~$1-2 total
- **Free**: Jira API, Clockify API

## Troubleshooting

**"Module not found" error**
```bash
# Make sure you're in project root
cd /Users/adrianboerstra/projects/maximQBR
pip install -r requirements.txt
```

**API authentication errors**
- Check `.env` file has correct credentials
- Verify API keys are still active

**No transcripts found**
- Transcripts should already be in `data-sources/transcripts/raw/`
- You have 23 PDFs there already (01-MK-LD-LE.pdf through 23-MK-LD.pdf)

## Support

See `scripts/README.md` for detailed documentation.

## What Makes This Special

This isn't just a data dump - Claude analyzes:
- **What Michael repeatedly asks about** (his real priorities)
- **Promises made vs delivered** (gaps to address)
- **Evolution of issues** (what's getting better/worse)
- **Cross-source validation** (transcript discussions vs Jira reality)

The result is a QBR that tells a compelling, data-backed story.

---

## Ready?

```bash
pip install -r requirements.txt
python scripts/main.py
```

Then review `qbr-output/qbr-draft.md` and refine from there!
