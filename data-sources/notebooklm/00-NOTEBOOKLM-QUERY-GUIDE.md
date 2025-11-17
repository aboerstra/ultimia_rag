# NotebookLM Correlation Query Guide

## Purpose
Use NotebookLM to analyze all data sources and generate correlation mappings between:
- Clockify time entries → Jira projects
- Jira projects → Portfolio projects
- Time entry description keywords → Portfolio projects

## Files Uploaded
- **Portfolio:** All portfolio projects with estimates, timelines, descriptions
- **Jira:** All Jira issues organized by project
- **Clockify:** All time tracking entries organized by Clockify project
- **Documentation:** Business process docs, system context, transcripts

## Recommended Queries

### Query 1: Clockify Project to Jira Project Mapping
```
Analyze the Clockify time entries and Jira issues. Create a mapping between 
Clockify project names and Jira project keys. Return as a JSON object:

{
  "Clockify Project Name": "JIRA_PROJECT_KEY",
  ...
}
```

### Query 2: Jira Project to Portfolio Project Mapping
```
Analyze the Jira issues and portfolio projects. Map each Jira project key 
to the most relevant portfolio project ID based on:
- Semantic similarity of descriptions
- Timeline alignment
- Business domain/area

Return as JSON:

{
  "JIRA_PROJECT_KEY": "portfolio_project_id",
  ...
}
```

### Query 3: Time Entry Keywords to Portfolio Projects
```
Analyze common keywords/phrases in Clockify time entry descriptions and 
map them to portfolio projects. Look for:
- Project abbreviations (e.g., "AIO", "booking")
- Feature names
- Business process terms

Return as JSON:

{
  "keyword_or_phrase": "portfolio_project_id",
  ...
}
```

### Query 4: Comprehensive Correlation Analysis
```
Create a comprehensive correlation between all time entries and portfolio 
projects. For each Clockify time entry description pattern, identify:
1. Which portfolio project it likely corresponds to
2. Confidence level (high/medium/low)
3. Reasoning

Group similar time entry descriptions together.
```

### Query 5: Unmapped Entry Analysis
```
Identify Clockify time entries that don't clearly map to any portfolio 
project. These likely represent:
- Internal overhead
- Administrative work
- Untracked initiatives

List common patterns in these unmapped entries.
```

## Output Format

Once NotebookLM provides the mappings, convert them to the format needed by
our correlator system. See `time-entry-mappings-TEMPLATE.json` for structure.

## Tips

- Ask follow-up questions to clarify ambiguous mappings
- Request explanations for why certain mappings were made
- Use NotebookLM to identify gaps in portfolio projects (work being done 
  that doesn't match any portfolio project)
- Have NotebookLM flag low-confidence mappings for manual review

