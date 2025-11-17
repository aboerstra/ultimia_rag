"""
Portfolio Correlation Engine

AI-powered system to correlate portfolio estimates with actual Jira work and Clockify time.
Uses semantic understanding rather than exact string matching to handle variations in naming.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PortfolioCorrelator:
    """
    Correlates portfolio project estimates to actual work using AI semantic understanding.
    Enhanced with RAG context retrieval for better domain knowledge.
    """
    
    def __init__(self, gemini_client=None, rag_manager=None):
        """
        Initialize the correlator.
        
        Args:
            gemini_client: GeminiClient instance for AI-powered correlation
            rag_manager: RAGManager instance for context retrieval (optional)
        """
        self.gemini_client = gemini_client
        self.rag_manager = rag_manager
        
    def correlate_project(
        self,
        portfolio_project: Dict,
        jira_issues: List[Dict],
        clockify_entries: List[Dict],
        date_range: Optional[Tuple[str, str]] = None
    ) -> Dict:
        """
        Correlate a portfolio project to actual Jira and Clockify data using AI.
        
        Args:
            portfolio_project: Portfolio project dict with name, estimates, etc.
            jira_issues: List of Jira issues (candidates for matching)
            clockify_entries: List of Clockify time entries
            date_range: Optional (start, end) date range to filter by
            
        Returns:
            Dict with matched items, confidence score, and variance analysis
        """
        logger.info(f"Correlating portfolio project: {portfolio_project.get('name', 'Unknown')}")
        
        # Filter by date range if provided
        if date_range:
            jira_issues = self._filter_jira_by_date(jira_issues, date_range)
            clockify_entries = self._filter_clockify_by_date(clockify_entries, date_range)
        
        # Use AI to find semantic matches
        if self.gemini_client:
            correlation = self._ai_correlate(portfolio_project, jira_issues, clockify_entries)
        else:
            # Fallback to basic keyword matching
            correlation = self._basic_correlate(portfolio_project, jira_issues, clockify_entries)
        
        # Calculate variance
        correlation['variance'] = self._calculate_variance(
            portfolio_project,
            correlation['matched_items']
        )
        
        return correlation
    
    def _ai_correlate(
        self,
        portfolio_project: Dict,
        jira_issues: List[Dict],
        clockify_entries: List[Dict]
    ) -> Dict:
        """
        Use Gemini AI to intelligently correlate based on context and semantics.
        
        Args:
            portfolio_project: Portfolio project to match
            jira_issues: Candidate Jira issues
            clockify_entries: Candidate time entries
            
        Returns:
            Correlation results with matched items and confidence
        """
        # Build context-rich prompt for AI
        prompt = self._build_correlation_prompt(
            portfolio_project,
            jira_issues,
            clockify_entries
        )
        
        # Define the correlation function for Gemini
        correlation_function = {
            "name": "correlate_portfolio_to_actuals",
            "description": "Correlate portfolio estimates to actual Jira work and Clockify time",
            "parameters": {
                "type": "object",
                "properties": {
                    "matched_jira_keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Jira issue keys that match this portfolio project"
                    },
                    "matched_clockify_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Clockify entry IDs that match this project"
                    },
                    "confidence_score": {
                        "type": "number",
                        "description": "Confidence level (0-1) in the correlation"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation of why these items were matched"
                    }
                },
                "required": ["matched_jira_keys", "matched_clockify_ids", "confidence_score", "reasoning"]
            }
        }
        
        try:
            # Call Gemini with function calling
            response = self.gemini_client.chat_with_tools(
                prompt=prompt,
                tools=[{"type": "function", "function": correlation_function}],
                max_tokens=8000
            )
            
            # Extract function call results
            if response.get('tool_calls'):
                result = response['tool_calls'][0]['arguments']
                
                # Aggregate matched items
                matched_jira = [
                    issue for issue in jira_issues 
                    if issue.get('key') in result['matched_jira_keys']
                ]
                matched_clockify = [
                    entry for entry in clockify_entries
                    if entry.get('id') in result['matched_clockify_ids']
                ]
                
                total_hours = sum(float(e.get('hours', 0)) for e in matched_clockify)
                
                return {
                    'matched_items': {
                        'jira': matched_jira,
                        'jira_keys': result['matched_jira_keys'],
                        'clockify': matched_clockify,
                        'clockify_hours': total_hours
                    },
                    'confidence_score': result['confidence_score'],
                    'reasoning': result['reasoning']
                }
            else:
                logger.warning("No function call in AI response, using fallback")
                return self._basic_correlate(portfolio_project, jira_issues, clockify_entries)
                
        except Exception as e:
            logger.error(f"AI correlation failed: {e}, using fallback")
            return self._basic_correlate(portfolio_project, jira_issues, clockify_entries)
    
    def _retrieve_rag_context(self, project_name: str, max_results: int = 3) -> List[Dict]:
        """
        Retrieve relevant context from RAG system for a portfolio project.
        
        Args:
            project_name: Name of the portfolio project
            max_results: Maximum number of context chunks to retrieve
            
        Returns:
            List of relevant context chunks
        """
        if not self.rag_manager:
            return []
        
        try:
            # Query RAG for project context
            results = self.rag_manager.search(
                query=f"What is {project_name}? What does this initiative involve?",
                n_results=max_results,
                use_hybrid=True
            )
            
            context_chunks = []
            if results:
                for result in results:
                    content = result.get('content', result.get('document', ''))
                    metadata = result.get('metadata', {})
                    context_chunks.append({
                        'content': content,
                        'source': metadata.get('source', 'Unknown')
                    })
            
            logger.info(f"Retrieved {len(context_chunks)} RAG context chunks for '{project_name}'")
            return context_chunks
            
        except Exception as e:
            logger.warning(f"Failed to retrieve RAG context: {e}")
            return []
    
    def _build_correlation_prompt(
        self,
        portfolio_project: Dict,
        jira_issues: List[Dict],
        clockify_entries: List[Dict]
    ) -> str:
        """Build a detailed prompt for AI correlation with RAG-enhanced context."""
        
        # Extract portfolio details
        project_name = portfolio_project.get('name', 'Unknown')
        project_desc = portfolio_project.get('description', '')
        estimated_hours = portfolio_project.get('totalHours', portfolio_project.get('total_hours', 0))
        date_start = portfolio_project.get('startDate', portfolio_project.get('start_date', ''))
        date_end = portfolio_project.get('endDate', portfolio_project.get('end_date', ''))
        
        # Retrieve RAG context for this project
        rag_context = self._retrieve_rag_context(project_name)
        rag_context_text = ""
        if rag_context:
            rag_context_text = "\n\nDOCUMENTATION CONTEXT (from internal knowledge base):\n"
            for i, chunk in enumerate(rag_context, 1):
                source = chunk.get('source', 'Unknown')
                content = chunk.get('content', '')
                rag_context_text += f"\n[Source {i}: {source}]\n{content}\n"
        
        # Build Jira candidates summary (limit to top matches)
        jira_summary = []
        for issue in jira_issues[:20]:  # Limit to avoid token overflow
            jira_summary.append(
                f"  - {issue.get('key')}: {issue.get('summary', 'No summary')}"
            )
        
        # Build Clockify candidates summary
        clockify_summary = []
        seen_descriptions = set()
        for entry in clockify_entries[:30]:  # Limit entries
            entry_id = entry.get('id', 'no-id')
            desc = entry.get('description', 'No description')
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                hours = entry.get('hours', 0)
                user = entry.get('user_name', 'Unknown')
                clockify_summary.append(f"  - [{entry_id}] '{desc}' - {hours}h ({user})")
        
        prompt = f"""You are analyzing a project portfolio to correlate estimates with actual work.

PORTFOLIO PROJECT (AUTHORITATIVE ESTIMATE):
Name: "{project_name}"
Description: {project_desc}
Estimated Hours: {estimated_hours}h
Date Range: {date_start} to {date_end}{rag_context_text}

JIRA ISSUES (Candidates - may or may not be related):
{chr(10).join(jira_summary) if jira_summary else '  (No Jira candidates)'}

CLOCKIFY TIME ENTRIES (Candidates - may or may not be related):
{chr(10).join(clockify_summary) if clockify_summary else '  (No Clockify candidates)'}

TASK: 
Identify which Jira issues and Clockify entries belong to this portfolio project.
Use semantic understanding - names won't match exactly. Look for:
- Similar terminology (synonyms, abbreviations, variations)
- Temporal alignment (dates overlap)
- Epic/parent-child relationships in Jira
- Team member assignments
- Domain context (related features/areas)

Provide:
1. matched_jira_keys: List of Jira keys that match
2. matched_clockify_ids: List of Clockify IDs that match
3. confidence_score: 0-1 (how confident you are)
4. reasoning: Why you matched these items

Be conservative - only match if you're reasonably confident (>0.6).
"""
        
        return prompt
    
    def _basic_correlate(
        self,
        portfolio_project: Dict,
        jira_issues: List[Dict],
        clockify_entries: List[Dict]
    ) -> Dict:
        """
        Fallback correlation using basic keyword matching.
        
        Args:
            portfolio_project: Portfolio project
            jira_issues: Candidate Jira issues
            clockify_entries: Candidate time entries
            
        Returns:
            Basic correlation results
        """
        project_name = portfolio_project.get('name', '').lower()
        keywords = set(project_name.split())
        
        # Match Jira by keywords in summary
        matched_jira = []
        for issue in jira_issues:
            summary = issue.get('summary', '').lower()
            if any(kw in summary for kw in keywords if len(kw) > 3):
                matched_jira.append(issue)
        
        # Match Clockify by keywords in description
        matched_clockify = []
        for entry in clockify_entries:
            description = entry.get('description', '').lower()
            if any(kw in description for kw in keywords if len(kw) > 3):
                matched_clockify.append(entry)
        
        total_hours = sum(float(e.get('hours', 0)) for e in matched_clockify)
        
        return {
            'matched_items': {
                'jira': matched_jira,
                'jira_keys': [issue['key'] for issue in matched_jira],
                'clockify': matched_clockify,
                'clockify_hours': total_hours
            },
            'confidence_score': 0.5,  # Low confidence for basic matching
            'reasoning': f"Basic keyword matching on: {', '.join(keywords)}"
        }
    
    def _calculate_variance(
        self,
        portfolio_project: Dict,
        matched_items: Dict
    ) -> Dict:
        """
        Calculate variance between estimated and actual hours.
        
        Args:
            portfolio_project: Portfolio project with estimates
            matched_items: Matched Jira and Clockify items
            
        Returns:
            Variance analysis
        """
        estimated = float(portfolio_project.get('totalHours', portfolio_project.get('total_hours', 0)))
        actual = matched_items.get('clockify_hours', 0)
        delta = actual - estimated
        
        if estimated > 0:
            percent = (delta / estimated) * 100
        else:
            percent = 0
        
        status = 'on_track'
        if abs(percent) > 20:
            status = 'over_budget' if delta > 0 else 'under_budget'
        
        return {
            'estimated_hours': estimated,
            'actual_hours': actual,
            'delta_hours': delta,
            'delta_percent': round(percent, 1),
            'status': status
        }
    
    def _filter_jira_by_date(
        self,
        issues: List[Dict],
        date_range: Tuple[str, str]
    ) -> List[Dict]:
        """Filter Jira issues by date range."""
        # TODO: Implement date filtering based on Jira created/updated dates
        return issues
    
    def _filter_clockify_by_date(
        self,
        entries: List[Dict],
        date_range: Tuple[str, str]
    ) -> List[Dict]:
        """Filter Clockify entries by date range."""
        start_date, end_date = date_range
        
        filtered = []
        for entry in entries:
            entry_date = entry.get('start', '')
            if entry_date:
                # Extract date portion
                entry_date = entry_date.split('T')[0]
                if start_date <= entry_date <= end_date:
                    filtered.append(entry)
        
        return filtered


def load_portfolio_data(filepath: str = "data-sources/custom-context/faye-portfolio-Laura 1 agressive.json") -> List[Dict]:
    """
    Load and parse portfolio data from JSON file.
    
    Args:
        filepath: Path to portfolio JSON file
        
    Returns:
        List of portfolio projects
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Extract projects from portfolio structure
        projects = []
        
        # Handle different portfolio JSON structures
        if isinstance(data, list):
            projects = data
        elif isinstance(data, dict):
            # Look for common keys
            for key in ['projects', 'portfolio', 'items', 'workstreams']:
                if key in data:
                    projects = data[key]
                    break
            
            # If still not found, check if dict values are projects
            if not projects and all(isinstance(v, dict) for v in data.values()):
                projects = list(data.values())
        
        logger.info(f"Loaded {len(projects)} portfolio projects from {filepath}")
        return projects
        
    except FileNotFoundError:
        logger.error(f"Portfolio file not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing portfolio JSON: {e}")
        return []
