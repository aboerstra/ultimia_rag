"""
Export Data Sources to NotebookLM Format

Converts all relevant data sources into NotebookLM-compatible formats
(markdown, txt) for correlation analysis.
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Paths
DATA_DIR = Path("data-sources")
OUTPUT_DIR = DATA_DIR / "notebooklm"
JIRA_DIR = DATA_DIR / "jira" / "raw"
CLOCKIFY_DIR = DATA_DIR / "clockify" / "raw"
CONFLUENCE_DIR = DATA_DIR / "confluence" / "raw"
CUSTOM_CONTEXT_DIR = DATA_DIR / "custom-context"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts" / "extracted"

# Specific Confluence pages to include
CONFLUENCE_PAGES_TO_INCLUDE = [
    "Client Documentation Guide",
    "Maxim Overview",
    "Section 1: Introduction to Maxim",
    "Section 2: Business Processes",
    "Section 3: Technology Overview",
    "New Lead/Applicant Qualification",
    "Application Intake Process (Dealers)",
    "Application Intake Process (Applicants)",
    "Application Intake",
    "Decision to Proceed with Application",
    "Credit Reports",
    "Calculate Scoring &amp; Pricing Tool",
    "Calculate Scoring & Pricing Tool",
    "Tvalue",
    "Documentation Process",
    "Document Merge / Conga",
    "Docusign (new)",
    "SEND DOCUSIGN",
    "Booking and Funding Process",
    "Customer Interview",
    "LeaseWorks Integration",
    "Collections, Repossession, and Asset Management",
    "Box",
    "Comparative Analysis: Trucking"
]


def create_output_structure():
    """Create NotebookLM export folder structure."""
    print("Creating output directory structure...")
    
    # Clean and create main directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    
    # Create subdirectories
    (OUTPUT_DIR / "portfolio").mkdir()
    (OUTPUT_DIR / "jira").mkdir()
    (OUTPUT_DIR / "clockify").mkdir()
    (OUTPUT_DIR / "confluence").mkdir()
    (OUTPUT_DIR / "documentation").mkdir()
    (OUTPUT_DIR / "transcripts").mkdir()
    
    print(f"✓ Created: {OUTPUT_DIR}")


def export_portfolio_data():
    """Export portfolio projects to markdown."""
    print("\nExporting portfolio data...")
    
    # Find portfolio JSON file
    portfolio_files = list(CUSTOM_CONTEXT_DIR.glob("*portfolio*.json"))
    
    if not portfolio_files:
        print("⚠ No portfolio files found")
        return
    
    for portfolio_file in portfolio_files:
        with open(portfolio_file, 'r') as f:
            data = json.load(f)
        
        # Handle different portfolio structures
        projects = []
        value_streams = []
        
        if isinstance(data, dict):
            projects = data.get('projects', [])
            value_streams = data.get('valueStreams', data.get('value_streams', []))
        elif isinstance(data, list):
            projects = data
        
        # Create comprehensive portfolio markdown
        output_path = OUTPUT_DIR / "portfolio" / f"{portfolio_file.stem}.md"
        
        with open(output_path, 'w') as f:
            f.write(f"# Portfolio Projects: {portfolio_file.stem}\n\n")
            f.write(f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
            
            # Value Streams
            if value_streams:
                f.write("## Value Streams\n\n")
                for vs in value_streams:
                    vs_id = vs.get('id', 'unknown')
                    vs_name = vs.get('name', 'Unknown')
                    vs_desc = vs.get('description', '')
                    f.write(f"### {vs_name} (`{vs_id}`)\n\n")
                    if vs_desc:
                        f.write(f"{vs_desc}\n\n")
            
            # Projects
            f.write("## Portfolio Projects\n\n")
            for i, proj in enumerate(projects, 1):
                proj_id = proj.get('id', f'proj_{i}')
                proj_name = proj.get('name', 'Unknown')
                proj_desc = proj.get('description', '')
                total_hours = proj.get('totalHours', proj.get('total_hours', 0))
                status = proj.get('status', 'unknown')
                start_date = proj.get('startDate', proj.get('start_date', ''))
                end_date = proj.get('endDate', proj.get('end_date', ''))
                vs_id = proj.get('valueStreamId', proj.get('value_stream_id', ''))
                
                f.write(f"### {proj_name}\n\n")
                f.write(f"- **ID:** `{proj_id}`\n")
                f.write(f"- **Status:** {status}\n")
                f.write(f"- **Estimated Hours:** {total_hours}h\n")
                if start_date:
                    f.write(f"- **Timeline:** {start_date} to {end_date}\n")
                if vs_id:
                    f.write(f"- **Value Stream:** {vs_id}\n")
                f.write(f"\n**Description:**\n{proj_desc}\n\n")
                f.write("---\n\n")
        
        print(f"✓ Exported: {output_path.name} ({len(projects)} projects)")


def export_jira_data():
    """Export Jira issues to markdown."""
    print("\nExporting Jira data...")
    
    if not JIRA_DIR.exists():
        print("⚠ No Jira data found")
        return
    
    jira_files = list(JIRA_DIR.glob("*.json"))
    all_issues = []
    
    # Load all Jira issues
    for jira_file in jira_files:
        try:
            with open(jira_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_issues.extend(data)
                elif isinstance(data, dict) and 'issues' in data:
                    all_issues.extend(data['issues'])
        except Exception as e:
            print(f"⚠ Error reading {jira_file.name}: {e}")
    
    if not all_issues:
        print("⚠ No Jira issues found")
        return
    
    # Group by project
    by_project = {}
    for issue in all_issues:
        # Handle simplified format where project is just a string
        project_key = issue.get('project', 'UNKNOWN')
        if isinstance(project_key, dict):
            project_key = project_key.get('key', 'UNKNOWN')
        
        if project_key not in by_project:
            by_project[project_key] = []
        by_project[project_key].append(issue)
    
    # Create per-project markdown files
    for project_key, issues in by_project.items():
        output_path = OUTPUT_DIR / "jira" / f"jira-{project_key}.md"
        
        with open(output_path, 'w') as f:
            f.write(f"# Jira Issues: {project_key}\n\n")
            f.write(f"*Total Issues: {len(issues)}*\n\n")
            
            for issue in issues:
                key = issue.get('key', '')
                summary = issue.get('summary', issue.get('fields', {}).get('summary', 'No summary'))
                description = issue.get('description', issue.get('fields', {}).get('description', ''))
                status = issue.get('status', issue.get('fields', {}).get('status', {}).get('name', 'Unknown'))
                issue_type = issue.get('issuetype', issue.get('fields', {}).get('issuetype', {}).get('name', 'Unknown'))
                
                f.write(f"### {key}: {summary}\n\n")
                f.write(f"- **Type:** {issue_type}\n")
                f.write(f"- **Status:** {status}\n")
                if description:
                    f.write(f"\n**Description:**\n{description}\n")
                f.write("\n---\n\n")
        
        print(f"✓ Exported: jira-{project_key}.md ({len(issues)} issues)")
    
    print(f"✓ Total Jira issues exported: {len(all_issues)}")


def export_clockify_data():
    """Export Clockify time entries to markdown."""
    print("\nExporting Clockify data...")
    
    if not CLOCKIFY_DIR.exists():
        print("⚠ No Clockify data found")
        return
    
    clockify_files = list(CLOCKIFY_DIR.glob("*.json"))
    all_entries = []
    
    # Load all time entries
    for clockify_file in clockify_files:
        try:
            with open(clockify_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_entries.extend(data)
        except Exception as e:
            print(f"⚠ Error reading {clockify_file.name}: {e}")
    
    if not all_entries:
        print("⚠ No Clockify entries found")
        return
    
    # Group by Clockify project
    by_project = {}
    no_project = []
    
    for entry in all_entries:
        project_name = entry.get('project_name', entry.get('project', {}).get('name', None))
        
        if project_name:
            if project_name not in by_project:
                by_project[project_name] = []
            by_project[project_name].append(entry)
        else:
            no_project.append(entry)
    
    # Create per-project markdown files
    for project_name, entries in by_project.items():
        safe_name = project_name.replace('/', '-').replace(' ', '-')
        output_path = OUTPUT_DIR / "clockify" / f"clockify-{safe_name}.md"
        
        total_hours = sum(float(e.get('hours', e.get('timeInterval', {}).get('duration', 0))) for e in entries)
        
        with open(output_path, 'w') as f:
            f.write(f"# Clockify Time Entries: {project_name}\n\n")
            f.write(f"*Total Entries: {len(entries)} | Total Hours: {total_hours:.1f}h*\n\n")
            
            # Sort by date
            sorted_entries = sorted(
                entries, 
                key=lambda x: x.get('start', x.get('timeInterval', {}).get('start', '')),
                reverse=True
            )
            
            for entry in sorted_entries[:100]:  # Limit to 100 most recent per project
                description = entry.get('description', 'No description')
                hours = entry.get('hours', 0)
                user = entry.get('user_name', entry.get('user', {}).get('name', 'Unknown'))
                date = entry.get('start', entry.get('timeInterval', {}).get('start', ''))[:10]
                
                f.write(f"### {date} - {description}\n\n")
                f.write(f"- **User:** {user}\n")
                f.write(f"- **Hours:** {hours}h\n")
                f.write(f"- **Project:** {project_name}\n")
                f.write("\n---\n\n")
        
        print(f"✓ Exported: clockify-{safe_name}.md ({len(entries)} entries, {total_hours:.1f}h)")
    
    # Export unassigned entries
    if no_project:
        output_path = OUTPUT_DIR / "clockify" / "clockify-no-project.md"
        with open(output_path, 'w') as f:
            f.write(f"# Clockify Time Entries: No Project Assigned\n\n")
            f.write(f"*Total Entries: {len(no_project)}*\n\n")
            
            for entry in no_project[:100]:
                description = entry.get('description', 'No description')
                hours = entry.get('hours', 0)
                user = entry.get('user_name', 'Unknown')
                date = entry.get('start', '')[:10]
                
                f.write(f"### {date} - {description}\n\n")
                f.write(f"- **User:** {user}\n")
                f.write(f"- **Hours:** {hours}h\n")
                f.write("\n---\n\n")
        
        print(f"✓ Exported: clockify-no-project.md ({len(no_project)} entries)")
    
    print(f"✓ Total Clockify entries exported: {len(all_entries)}")


def export_confluence_data():
    """Export selected Confluence pages to markdown."""
    print("\nExporting Confluence pages...")
    
    if not CONFLUENCE_DIR.exists():
        print("⚠ No Confluence data found")
        return
    
    confluence_file = CONFLUENCE_DIR / "MAXCOM_pages.json"
    if not confluence_file.exists():
        print("⚠ MAXCOM_pages.json not found")
        return
    
    try:
        with open(confluence_file, 'r') as f:
            all_pages = json.load(f)
        
        if not isinstance(all_pages, list):
            print("⚠ Unexpected Confluence data structure")
            return
        
        # Filter to only include specified pages
        exported_count = 0
        for page in all_pages:
            title = page.get('title', '')
            
            # Check if this page matches our filter list
            if any(filter_title.lower() in title.lower() for filter_title in CONFLUENCE_PAGES_TO_INCLUDE):
                # Create safe filename
                safe_title = title.replace('/', '-').replace(':', '-').replace('&amp;', 'and')
                safe_title = ''.join(c for c in safe_title if c.isalnum() or c in ['-', '_', ' '])[:100]
                output_path = OUTPUT_DIR / "confluence" / f"{safe_title}.md"
                
                # Extract content
                body = page.get('body', '')
                page_id = page.get('id', 'unknown')
                when = page.get('when', 'unknown')
                by_user = page.get('by', 'unknown')
                
                # Write markdown file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"*Source: Confluence | Page ID: {page_id}*\n")
                    f.write(f"*Last Updated: {when} by {by_user}*\n\n")
                    f.write("---\n\n")
                    f.write(body)
                
                exported_count += 1
                print(f"✓ Exported: {safe_title[:60]}...")
        
        print(f"✓ Total Confluence pages exported: {exported_count}")
        
    except Exception as e:
        print(f"⚠ Error exporting Confluence data: {e}")


def copy_documentation():
    """Copy relevant markdown documentation files."""
    print("\nCopying documentation files...")
    
    # Copy custom context markdown files
    if CUSTOM_CONTEXT_DIR.exists():
        md_files = list(CUSTOM_CONTEXT_DIR.glob("*.md"))
        for md_file in md_files:
            shutil.copy(md_file, OUTPUT_DIR / "documentation" / md_file.name)
            print(f"✓ Copied: {md_file.name}")
    
    # Copy transcript analyses
    if TRANSCRIPTS_DIR.exists():
        md_files = list(TRANSCRIPTS_DIR.glob("*.md"))
        for md_file in md_files:
            shutil.copy(md_file, OUTPUT_DIR / "transcripts" / md_file.name)
            print(f"✓ Copied: {md_file.name}")


def create_notebooklm_guide():
    """Create a guide for querying NotebookLM."""
    print("\nCreating NotebookLM query guide...")
    
    guide_path = OUTPUT_DIR / "00-NOTEBOOKLM-QUERY-GUIDE.md"
    
    with open(guide_path, 'w') as f:
        f.write("""# NotebookLM Correlation Query Guide

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

""")
    
    print(f"✓ Created: {guide_path.name}")


def create_mapping_template():
    """Create a template for the mapping file."""
    print("\nCreating mapping file template...")
    
    template_path = OUTPUT_DIR / "time-entry-mappings-TEMPLATE.json"
    
    template = {
        "_comment": "Use NotebookLM to generate the mappings, then paste them here",
        "clockify_to_jira": {
            "MaxCom Development": "MAXCOM",
            "Internal Tools": "TOOLS",
            "Example Clockify Project": "JIRA_KEY"
        },
        "jira_to_portfolio": {
            "MAXCOM": "proj_application_intake_optimization",
            "TOOLS": "proj_internal_tooling",
            "JIRA_KEY": "portfolio_project_id"
        },
        "description_keywords": {
            "AIO": "proj_application_intake_optimization",
            "application intake": "proj_application_intake_optimization",
            "booking": "proj_booking_optimization",
            "keyword": "portfolio_project_id"
        }
    }
    
    with open(template_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"✓ Created: {template_path.name}")


def create_summary():
    """Create a summary of exported files."""
    print("\nCreating export summary...")
    
    file_count = sum(1 for _ in OUTPUT_DIR.rglob('*') if _.is_file())
    
    summary_path = OUTPUT_DIR / "00-EXPORT-SUMMARY.md"
    
    with open(summary_path, 'w') as f:
        f.write(f"# NotebookLM Export Summary\n\n")
        f.write(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Files:** {file_count}\n\n")
        f.write("## Contents\n\n")
        
        for subdir in sorted(OUTPUT_DIR.iterdir()):
            if subdir.is_dir():
                files = list(subdir.glob('*'))
                f.write(f"### {subdir.name}/ ({len(files)} files)\n\n")
                for file in sorted(files):
                    size_kb = file.stat().st_size / 1024
                    f.write(f"- `{file.name}` ({size_kb:.1f} KB)\n")
                f.write("\n")
        
        f.write("## Next Steps\n\n")
        f.write("1. Upload all files to NotebookLM (max 300 files)\n")
        f.write("2. Follow queries in `00-NOTEBOOKLM-QUERY-GUIDE.md`\n")
        f.write("3. Copy NotebookLM's output to `time-entry-mappings.json`\n")
        f.write("4. Use the correlator with the generated mappings\n")
    
    print(f"✓ Created: {summary_path.name}")
    print(f"\n{'='*60}")
    print(f"📊 Export Complete!")
    print(f"{'='*60}")
    print(f"Location: {OUTPUT_DIR}")
    print(f"Total Files: {file_count}")
    print(f"\nNext: Upload to NotebookLM and run correlation queries")


def main():
    """Main export process."""
    print("="*60)
    print("NotebookLM Data Export")
    print("="*60)
    
    create_output_structure()
    export_portfolio_data()
    export_jira_data()
    export_clockify_data()
    export_confluence_data()
    copy_documentation()
    create_notebooklm_guide()
    create_mapping_template()
    create_summary()


if __name__ == "__main__":
    main()
