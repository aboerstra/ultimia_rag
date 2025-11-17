"""Main orchestrator for QBR data collection and analysis."""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from connectors.llm_client import LLMClient
from connectors.jira_client import JiraClient
from connectors.clockify_client import ClockifyClient
from connectors.salesforce_client import SalesforceClient
from collectors.pdf_processor import PDFProcessor
from config import Config

try:
    from atlassian import Confluence
    CONFLUENCE_AVAILABLE = True
except ImportError:
    CONFLUENCE_AVAILABLE = False


class QBROrchestrator:
    """Main orchestrator for running the complete QBR analysis pipeline."""
    
    def __init__(self):
        self.llm = LLMClient()
        self.jira = JiraClient()
        self.clockify = ClockifyClient()
        self.pdf_processor = PDFProcessor()
        
    def step1_extract_transcripts(self) -> List[Dict]:
        """Step 1: Extract text from all PDF transcripts."""
        print("\n" + "="*60)
        print("STEP 1: Extracting text from transcripts")
        print("="*60)
        
        transcripts = self.pdf_processor.process_all_transcripts()
        
        # Save extracted text
        for transcript in transcripts:
            self.pdf_processor.save_extracted_text(transcript)
        
        print(f"\n✅ Extracted {len(transcripts)} transcripts")
        return transcripts
    
    def step2_analyze_transcripts(self, transcripts: List[Dict]) -> List[Dict]:
        """Step 2: Analyze transcripts with Claude."""
        print("\n" + "="*60)
        print("STEP 2: Analyzing transcripts with Claude")
        print("="*60)
        
        analyses = []
        
        for i, transcript in enumerate(transcripts, 1):
            print(f"\n  [{i}/{len(transcripts)}] Analyzing: {transcript['filename']}")
            
            try:
                analysis = self.llm.analyze_transcript(
                    transcript['text'],
                    transcript['filename']
                )
                analysis['filename'] = transcript['filename']
                analysis['metadata'] = transcript['metadata']
                analyses.append(analysis)
                
                # Save individual analysis
                self._save_json(
                    analysis,
                    Config.TRANSCRIPTS_EXTRACTED / f"{transcript['filename'].replace('.pdf', '_analysis.json')}"
                )
                
            except Exception as e:
                print(f"    ❌ Error analyzing {transcript['filename']}: {e}")
                analyses.append({
                    'filename': transcript['filename'],
                    'error': str(e)
                })
        
        print(f"\n✅ Analyzed {len(analyses)} transcripts")
        return analyses
    
    def step3_synthesize_insights(self, analyses: List[Dict]):
        """Step 3: Synthesize insights from all analyses."""
        print("\n" + "="*60)
        print("STEP 3: Synthesizing cross-transcript insights")
        print("="*60)
        
        # Filter out failed analyses
        valid_analyses = [a for a in analyses if 'error' not in a]
        
        if not valid_analyses:
            print("❌ No valid analyses to synthesize")
            return
        
        print(f"\n  Synthesizing insights from {len(valid_analyses)} transcripts...")
        
        try:
            synthesis = self.llm.synthesize_insights(valid_analyses)
            
            # Save synthesis
            output_path = Config.SYNTHESIS / 'transcript-synthesis.md'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(synthesis)
            
            print(f"\n✅ Synthesis saved to {output_path}")
            
        except Exception as e:
            print(f"❌ Error during synthesis: {e}")
    
    def step4_collect_jira_data(self):
        """Step 4: Collect data from Jira."""
        print("\n" + "="*60)
        print("STEP 4: Collecting Jira data")
        print("="*60)
        
        try:
            # Get all projects
            print("\n  Fetching Jira projects...")
            projects = self.jira.get_all_projects()
            print(f"  Found {len(projects)} projects")
            
            for project in projects:
                print(f"    - {project['key']}: {project['name']}")
            
            self._save_json(projects, Config.JIRA_RAW / 'projects.json')
            
            # Get issues (filtered by JIRA_PROJECT if set)
            if Config.JIRA_PROJECT:
                print(f"\n  Fetching issues from project '{Config.JIRA_PROJECT}' (last {Config.DATE_RANGE_MONTHS} months)...")
                issues = self.jira.get_issues(
                    project_key=Config.JIRA_PROJECT,
                    months_back=Config.DATE_RANGE_MONTHS
                )
            else:
                print(f"\n  Fetching issues from all projects (last {Config.DATE_RANGE_MONTHS} months)...")
                issues = self.jira.get_issues(months_back=Config.DATE_RANGE_MONTHS)
            
            print(f"  Found {len(issues)} issues")
            self._save_json(issues, Config.JIRA_RAW / 'issues.json')
            
            # Get boards
            print("\n  Fetching boards...")
            boards = self.jira.get_boards()
            print(f"  Found {len(boards)} boards")
            
            self._save_json(boards, Config.JIRA_RAW / 'boards.json')
            
            print("\n✅ Jira data collected")
            
        except Exception as e:
            print(f"❌ Error collecting Jira data: {e}")
    
    def step4b_collect_confluence_data(self):
        """Step 4b: Collect data from Confluence."""
        print("\n" + "="*60)
        print("STEP 4B: Collecting Confluence data")
        print("="*60)
        
        if not CONFLUENCE_AVAILABLE:
            print("⚠️  Confluence library not available, skipping...")
            return
        
        try:
            # Initialize Confluence client
            confluence = Confluence(
                url=Config.CONFLUENCE_URL,
                username=Config.CONFLUENCE_EMAIL,
                password=Config.CONFLUENCE_API_TOKEN,
                cloud=True
            )
            
            # Get all spaces
            print("\n  Fetching Confluence spaces...")
            all_spaces = confluence.get_all_spaces(start=0, limit=100)
            spaces = all_spaces.get('results', [])
            print(f"  Found {len(spaces)} spaces")
            
            for space in spaces[:10]:  # Show first 10
                print(f"    - {space['key']}: {space['name']}")
            
            self._save_json(spaces, Config.CONFLUENCE_RAW / 'spaces.json')
            
            # Get pages from specified space if configured
            if Config.JIRA_SPACE:
                print(f"\n  Fetching pages from space '{Config.JIRA_SPACE}'...")
                
                # Get all pages in the space
                pages = []
                start = 0
                limit = 50
                
                while True:
                    result = confluence.get_all_pages_from_space(
                        Config.JIRA_SPACE,
                        start=start,
                        limit=limit,
                        expand='body.storage,version'
                    )
                    
                    if not result:
                        break
                    
                    pages.extend(result)
                    
                    if len(result) < limit:
                        break
                    
                    start += limit
                
                print(f"  Found {len(pages)} pages in {Config.JIRA_SPACE}")
                
                # Save pages with full content
                pages_with_content = [{
                    'id': p['id'],
                    'title': p['title'],
                    'type': p['type'],
                    'space': p.get('space', {}),
                    'version': p.get('version', {}).get('number'),
                    'when': p.get('version', {}).get('when'),
                    'by': p.get('version', {}).get('by', {}).get('displayName'),
                    'body': p.get('body', {}).get('storage', {}).get('value', ''),  # Include content!
                    'body_length': len(p.get('body', {}).get('storage', {}).get('value', ''))
                } for p in pages]
                
                self._save_json(pages_with_content, Config.CONFLUENCE_RAW / f'{Config.JIRA_SPACE}_pages.json')
                
                # Calculate total content size
                total_chars = sum(p['body_length'] for p in pages_with_content)
                print(f"  Collected {total_chars:,} characters of content")
                
                print(f"\n  Recent page activity:")
                for page in sorted(pages, key=lambda x: x.get('version', {}).get('when', ''), reverse=True)[:5]:
                    version = page.get('version', {})
                    print(f"    - {page['title']} (updated {version.get('when', 'unknown')})")
                
            else:
                print("\n  ℹ️  No Confluence space configured (JIRA_SPACE not set)")
            
            print("\n✅ Confluence data collected")
            
        except Exception as e:
            print(f"❌ Error collecting Confluence data: {e}")
            import traceback
            traceback.print_exc()
    
    def step5_collect_clockify_data(self):
        """Step 5: Collect data from Clockify."""
        print("\n" + "="*60)
        print("STEP 5: Collecting Clockify data")
        print("="*60)
        
        try:
            # Set workspace
            workspaces = self.clockify.get_workspaces()
            if workspaces:
                print(f"\n  Found {len(workspaces)} workspace(s)")
                for ws in workspaces:
                    print(f"    - {ws['name']}")
                self.clockify.set_workspace(workspaces[0]['id'])
            
            # Get projects (filtered by client if set)
            if Config.CLOCKIFY_CLIENT:
                print(f"\n  Fetching Clockify projects for client {Config.CLOCKIFY_CLIENT}...")
                projects = self.clockify.get_projects(client_id=Config.CLOCKIFY_CLIENT)
            else:
                print("\n  Fetching all Clockify projects...")
                projects = self.clockify.get_projects()
            
            print(f"  Found {len(projects)} projects")
            self._save_json(projects, Config.CLOCKIFY_RAW / 'projects.json')
            
            # Get time entries (filtered by CLIENT if set, more flexible than specific project IDs)
            project_ids = None
            if Config.CLOCKIFY_CLIENT:
                # Get all projects for this client
                client_projects = self.clockify.get_projects(client_id=Config.CLOCKIFY_CLIENT)
                project_ids = [p['id'] for p in client_projects]
                print(f"\n  Fetching time entries for {len(project_ids)} MAXCOM projects (last {Config.DATE_RANGE_MONTHS} months)...")
                entries = self.clockify.get_time_entries(project_ids=project_ids)
            else:
                print(f"\n  Fetching time entries for all projects (last {Config.DATE_RANGE_MONTHS} months)...")
                entries = self.clockify.get_time_entries()
            
            print(f"  Found {len(entries)} time entries")
            self._save_json(entries, Config.CLOCKIFY_RAW / 'time_entries.json')
            
            # Get summary by project (with same client-based filter)
            print("\n  Calculating project summary...")
            summary = self.clockify.get_summary_by_project(project_ids=project_ids)
            
            self._save_json(summary, Config.CLOCKIFY_RAW / 'project_summary.json')
            
            print("\n  Project Hours Summary:")
            for project, data in summary.items():
                print(f"    {project}: {data['total_hours']:.1f} hrs ({data['billable_hours']:.1f} billable)")
            
            print("\n✅ Clockify data collected")
            
        except Exception as e:
            print(f"❌ Error collecting Clockify data: {e}")
    
    def step6_collect_salesforce_data(self):
        """Step 6: Collect Salesforce metadata from both orgs."""
        print("\n" + "="*60)
        print("STEP 6: Collecting Salesforce metadata")
        print("="*60)
        
        try:
            # Production (will try CLI OAuth first, then credentials)
            print("\n  Connecting to Production org...")
            prod_client = SalesforceClient(is_sandbox=False)
            
            prod_data = {
                'environment': 'production',
                'custom_objects': prod_client.get_custom_objects(),
                'apex_classes': prod_client.get_apex_classes(),
                'flows': prod_client.get_flows(),
                'coverage': prod_client.get_apex_coverage(),
                'validation_rules': prod_client.get_validation_rules(),
                'deployments': prod_client.get_deployment_history()
            }
            
            self._save_json(prod_data, Config.SALESFORCE_RAW / 'production' / 'metadata.json')
            print(f"  ✅ Production: {len(prod_data['custom_objects'])} objects, {len(prod_data['apex_classes'])} Apex classes")
            
            # Sandbox (try CLI OAuth first, then credentials)
            sandbox_available = False
            try:
                print("\n  Connecting to Sandbox org...")
                sandbox_client = SalesforceClient(is_sandbox=True)
                sandbox_available = True
            except ValueError:
                # No sandbox available via CLI or credentials
                print("\n  ℹ️  Sandbox org not available (not logged in via CLI and no credentials configured)")
            
            if sandbox_available:
                
                sandbox_data = {
                    'environment': 'sandbox',
                    'custom_objects': sandbox_client.get_custom_objects(),
                    'apex_classes': sandbox_client.get_apex_classes(),
                    'flows': sandbox_client.get_flows(),
                    'coverage': sandbox_client.get_apex_coverage(),
                    'validation_rules': sandbox_client.get_validation_rules(),
                    'deployments': sandbox_client.get_deployment_history()
                }
                
                self._save_json(sandbox_data, Config.SALESFORCE_RAW / 'sandbox' / 'metadata.json')
                print(f"  ✅ Sandbox: {len(sandbox_data['custom_objects'])} objects, {len(sandbox_data['apex_classes'])} Apex classes")
                
                # Compare environments - both current state and deployment history
                print("\n  Comparing environments...")
                
                # Calculate date range based on CONFIG
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=Config.DATE_RANGE_MONTHS * 30)
                
                comparison = prod_client.compare_with_environment(
                    sandbox_client,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                self._save_json(comparison, Config.SALESFORCE_RAW / 'comparison.json')
                
                # Report current state differences
                if comparison['only_in_production']:
                    print(f"  ⚠️  {len(comparison['only_in_production'])} objects only in production")
                if comparison['only_in_sandbox']:
                    print(f"  ⚠️  {len(comparison['only_in_sandbox'])} objects only in sandbox")
                if comparison['field_differences']:
                    print(f"  ⚠️  {len(comparison['field_differences'])} objects with field differences")
                
                # Report deployment comparison
                if 'deployment_comparison' in comparison:
                    dep_comp = comparison['deployment_comparison']
                    prod_count = dep_comp['production_deployments']['count']
                    sandbox_count = dep_comp['sandbox_deployments']['count']
                    sync_status = dep_comp['analysis']['sync_status']
                    
                    print(f"\n  📊 Deployment Activity ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}):")
                    print(f"     Production: {prod_count} deployments")
                    print(f"     Sandbox: {sandbox_count} deployments")
                    print(f"     Sync Status: {sync_status}")
                    
                    if sync_status == 'out_of_sync':
                        items_needing_sync = dep_comp['analysis']['items_needing_sync']
                        print(f"     ⚠️  {items_needing_sync} items need synchronization")
            
            # Generate metrics summary
            apex_lines = sum(cls.get('LengthWithoutComments', 0) for cls in prod_data['apex_classes'])
            coverage = prod_data['coverage']['overall_coverage']
            
            metrics = {
                'custom_objects': len(prod_data['custom_objects']),
                'apex_classes': len(prod_data['apex_classes']),
                'apex_lines_of_code': apex_lines,
                'test_coverage_percent': coverage,
                'active_flows': len(prod_data['flows']),
                'validation_rules': len(prod_data['validation_rules']),
                'coverage_status': 'Good' if coverage >= 75 else 'Needs Improvement'
            }
            
            self._save_json(metrics, Config.SALESFORCE_RAW / 'metrics.json')
            
            print(f"\n  📊 Metrics Summary:")
            print(f"     - Custom Objects: {metrics['custom_objects']}")
            print(f"     - Apex Classes: {metrics['apex_classes']} ({metrics['apex_lines_of_code']} lines)")
            print(f"     - Test Coverage: {metrics['test_coverage_percent']}% ({metrics['coverage_status']})")
            print(f"     - Active Flows: {metrics['active_flows']}")
            
            print("\n✅ Salesforce data collected")
            
        except ValueError as e:
            print(f"⚠️  Salesforce integration skipped: {e}")
        except Exception as e:
            print(f"❌ Error collecting Salesforce data: {e}")
            import traceback
            traceback.print_exc()
    
    def step7_generate_qbr_draft(self):
        """Step 7: Generate QBR draft using all collected data."""
        print("\n" + "="*60)
        print("STEP 7: Generating QBR draft")
        print("="*60)
        
        print("\n  Loading collected data...")
        
        # Load synthesis
        synthesis_path = Config.SYNTHESIS / 'transcript-synthesis.md'
        synthesis = ""
        if synthesis_path.exists():
            with open(synthesis_path, 'r', encoding='utf-8') as f:
                synthesis = f.read()
        
        # Load Jira data
        jira_issues = self._load_json(Config.JIRA_RAW / 'issues.json') or []
        
        # Load Clockify data
        clockify_summary = self._load_json(Config.CLOCKIFY_RAW / 'project_summary.json') or {}
        
        # Load Salesforce data
        sf_metrics = self._load_json(Config.SALESFORCE_RAW / 'metrics.json') or {}
        sf_prod_data = self._load_json(Config.SALESFORCE_RAW / 'production' / 'metadata.json') or {}
        sf_comparison = self._load_json(Config.SALESFORCE_RAW / 'comparison.json') or {}
        
        print(f"  - Transcript synthesis: {len(synthesis)} characters")
        print(f"  - Jira issues: {len(jira_issues)}")
        print(f"  - Clockify projects: {len(clockify_summary)}")
        print(f"  - Salesforce objects: {sf_metrics.get('custom_objects', 0)}")
        
        # Generate QBR content using Claude
        print("\n  Generating QBR with Claude...")
        
        system_prompt = """You are preparing a Quarterly Business Review presentation for Michael Kianmahd. 
Create a comprehensive, data-driven QBR that inspires confidence through transparency and clear progress tracking."""
        
        # Build Salesforce section
        sf_section = ""
        if sf_metrics:
            sf_section = f"""
SALESFORCE DATA (Technical Delivery Proof):
- Custom Objects: {sf_metrics.get('custom_objects', 0)}
- Apex Classes: {sf_metrics.get('apex_classes', 0)} ({sf_metrics.get('apex_lines_of_code', 0)} lines)
- Test Coverage: {sf_metrics.get('test_coverage_percent', 0)}% ({sf_metrics.get('coverage_status', 'Unknown')})
- Active Flows: {sf_metrics.get('active_flows', 0)}
- Validation Rules: {sf_metrics.get('validation_rules', 0)}
"""
            if sf_comparison.get('summary'):
                sf_section += f"""
Environment Comparison (Prod vs Sandbox):
- Total drift items: {sf_comparison['summary'].get('drift_count', 0)}
- Objects only in production: {len(sf_comparison.get('only_in_production', []))}
- Objects only in sandbox: {len(sf_comparison.get('only_in_sandbox', []))}
"""
        
        prompt = f"""Create a QBR presentation document using this data:

TRANSCRIPT SYNTHESIS:
{synthesis[:10000]}

JIRA DATA:
- Total issues: {len(jira_issues)}
- Status breakdown: {self._get_status_breakdown(jira_issues)}

CLOCKIFY DATA:
{json.dumps(clockify_summary, indent=2)[:2000]}
{sf_section}
Create a markdown QBR document with these sections:

1. EXECUTIVE SUMMARY (1-page overview)
   - Overall status (Red/Yellow/Green)
   - Key wins
   - Critical issues
   - Key asks from Michael

2. PROGRESS DASHBOARD
   - Delivery metrics (completed vs planned)
   - Velocity trends
   - Budget status (hours vs budget)

3. VALUE STREAM UPDATES
   For each major workstream:
   - Status and % complete
   - Recent milestones
   - Upcoming milestones
   - Dependencies and blockers

4. BUSINESS IMPACT
   - How our work maps to business goals
   - ROI and efficiency gains

5. LOOKING AHEAD (30/60/90 days)
   - Concrete deliverables with dates
   - Resource needs
   - Known risks

Make it specific, data-driven, and actionable."""

        try:
            qbr_content = self.llm.analyze(prompt, system_prompt, max_tokens=4000)
            
            # Save QBR draft
            output_path = Config.QBR_OUTPUT / 'qbr-draft.md'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Maxim QBR - {datetime.now().strftime('%B %Y')}\n\n")
                f.write(qbr_content)
            
            print(f"\n✅ QBR draft saved to {output_path}")
            
        except Exception as e:
            print(f"❌ Error generating QBR: {e}")
    
    def _save_json(self, data, path: Path):
        """Save data as JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_json(self, path: Path):
        """Load JSON file."""
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_status_breakdown(self, issues: List[Dict]) -> Dict:
        """Get count of issues by status."""
        breakdown = {}
        for issue in issues:
            status = issue.get('status', 'Unknown')
            breakdown[status] = breakdown.get(status, 0) + 1
        return breakdown
    
    def run_full_pipeline(self):
        """Run the complete QBR analysis pipeline."""
        print("\n" + "="*60)
        print("MAXIM QBR ANALYSIS PIPELINE")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Run all steps
            transcripts = self.step1_extract_transcripts()
            analyses = self.step2_analyze_transcripts(transcripts)
            self.step3_synthesize_insights(analyses)
            self.step4_collect_jira_data()
            self.step4b_collect_confluence_data()
            self.step5_collect_clockify_data()
            self.step6_collect_salesforce_data()
            self.step7_generate_qbr_draft()
            
            print("\n" + "="*60)
            print("✅ PIPELINE COMPLETE!")
            print("="*60)
            print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"\nResults available in:")
            print(f"  - Transcript analysis: {Config.TRANSCRIPTS_EXTRACTED}")
            print(f"  - Synthesis: {Config.SYNTHESIS}")
            print(f"  - QBR draft: {Config.QBR_OUTPUT / 'qbr-draft.md'}")
            
        except KeyboardInterrupt:
            print("\n\n❌ Pipeline interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    orchestrator = QBROrchestrator()
    orchestrator.run_full_pipeline()
