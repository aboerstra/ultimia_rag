"""
Comprehensive Portfolio Correlation System

Achieves 100% allocation of all Clockify hours to portfolio projects and value streams
using a multi-stage approach:
1. Jira-based direct correlation
2. RAG-enhanced AI semantic matching
3. Proportional overhead distribution
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class ComprehensiveCorrelator:
    """
    Comprehensive correlator that ensures 100% allocation of all Clockify hours
    to portfolio projects and value streams.
    """
    
    def __init__(self, gemini_client=None, rag_manager=None, jira_client=None):
        """
        Initialize comprehensive correlator.
        
        Args:
            gemini_client: GeminiClient for AI-powered matching
            rag_manager: RAGManager for context retrieval
            jira_client: JiraClient for issue lookups
        """
        self.gemini_client = gemini_client
        self.rag_manager = rag_manager
        self.jira_client = jira_client
        
    def correlate_all_hours(
        self,
        portfolio_projects: List[Dict],
        value_streams: List[Dict],
        jira_issues: List[Dict],
        clockify_entries: List[Dict]
    ) -> Dict:
        """
        Correlate ALL Clockify hours to portfolio projects using multi-stage approach.
        
        Returns:
            Dict with complete allocation breakdown and reports
        """
        logger.info(f"Starting comprehensive correlation of {len(clockify_entries)} Clockify entries")
        
        # Build lookup maps
        jira_map = {issue['key']: issue for issue in jira_issues}
        project_map = {proj['id']: proj for proj in portfolio_projects}
        vs_map = {vs['id']: vs for vs in value_streams}
        
        # Track allocations
        allocations = []
        stage_stats = {
            'jira_direct': {'count': 0, 'hours': 0.0},
            'ai_semantic': {'count': 0, 'hours': 0.0},
            'proportional': {'count': 0, 'hours': 0.0}
        }
        
        # Stage 1: Jira-based direct correlation
        jira_correlated, remaining = self._stage1_jira_correlation(
            clockify_entries, jira_map, portfolio_projects, vs_map
        )
        allocations.extend(jira_correlated)
        stage_stats['jira_direct']['count'] = len(jira_correlated)
        stage_stats['jira_direct']['hours'] = sum(a['hours'] for a in jira_correlated)
        
        logger.info(f"Stage 1 (Jira): {len(jira_correlated)} entries, {stage_stats['jira_direct']['hours']:.1f}h")
        
        # Stage 2: AI semantic matching
        if self.gemini_client and self.rag_manager:
            ai_correlated, remaining = self._stage2_ai_correlation(
                remaining, portfolio_projects, vs_map
            )
            allocations.extend(ai_correlated)
            stage_stats['ai_semantic']['count'] = len(ai_correlated)
            stage_stats['ai_semantic']['hours'] = sum(a['hours'] for a in ai_correlated)
            
            logger.info(f"Stage 2 (AI): {len(ai_correlated)} entries, {stage_stats['ai_semantic']['hours']:.1f}h")
        
        # Stage 3: Proportional distribution
        proportional = self._stage3_proportional_distribution(
            remaining, allocations, portfolio_projects, vs_map
        )
        allocations.extend(proportional)
        stage_stats['proportional']['count'] = len(proportional)
        stage_stats['proportional']['hours'] = sum(a['hours'] for a in proportional)
        
        logger.info(f"Stage 3 (Proportional): {len(proportional)} entries, {stage_stats['proportional']['hours']:.1f}h")
        
        # Generate comprehensive reports
        report = self._generate_comprehensive_report(
            allocations, portfolio_projects, value_streams, stage_stats
        )
        
        return {
            'allocations': allocations,
            'stage_stats': stage_stats,
            'report': report,
            'coverage': 100.0  # Always 100%
        }
    
    def _stage1_jira_correlation(
        self,
        clockify_entries: List[Dict],
        jira_map: Dict,
        portfolio_projects: List[Dict],
        vs_map: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Stage 1: Direct correlation via Jira references.
        
        Returns:
            (correlated_entries, remaining_entries)
        """
        correlated = []
        remaining = []
        
        for entry in clockify_entries:
            # Extract Jira key from description
            jira_key = self._extract_jira_key(entry.get('description', ''))
            
            if jira_key and jira_key in jira_map:
                jira_issue = jira_map[jira_key]
                
                # Find matching portfolio project
                project, vs = self._map_jira_to_portfolio(
                    jira_issue, portfolio_projects, vs_map
                )
                
                if project:
                    correlated.append({
                        'clockify_id': entry['id'],
                        'description': entry['description'],
                        'hours': entry['hours'],
                        'date': entry.get('start', '').split('T')[0],
                        'user': entry.get('user_name', 'Unknown'),
                        'project_id': project['id'],
                        'project_name': project['name'],
                        'value_stream_id': vs['id'] if vs else None,
                        'value_stream_name': vs['name'] if vs else 'Unknown',
                        'allocation_method': 'jira_direct',
                        'jira_key': jira_key,
                        'confidence': 1.0
                    })
                else:
                    # Jira key found but couldn't map to portfolio
                    remaining.append(entry)
            else:
                # No Jira reference
                remaining.append(entry)
        
        return correlated, remaining
    
    def _stage2_ai_correlation(
        self,
        clockify_entries: List[Dict],
        portfolio_projects: List[Dict],
        vs_map: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Stage 2: AI-powered semantic matching with RAG context.
        
        Returns:
            (correlated_entries, remaining_entries)
        """
        correlated = []
        remaining = []
        
        # Process in small batches to avoid API rate limits
        logger.info(f"Stage 2 (AI): Processing {len(clockify_entries)} entries for semantic matching")
        
        for i, entry in enumerate(clockify_entries):
            if i % 10 == 0:
                logger.info(f"  Progress: {i}/{len(clockify_entries)} entries processed")
            
            description = entry.get('description', '')
            
            # Get RAG context for this work description
            rag_context = self._get_rag_context(description)
            
            # Use AI to match to portfolio project
            match = self._ai_match_to_project(
                description, rag_context, portfolio_projects, vs_map
            )
            
            if match and match['confidence'] >= 0.75:
                correlated.append({
                    'clockify_id': entry['id'],
                    'description': entry['description'],
                    'hours': entry['hours'],
                    'date': entry.get('start', '').split('T')[0],
                    'user': entry.get('user_name', 'Unknown'),
                    'project_id': match['project']['id'],
                    'project_name': match['project']['name'],
                    'value_stream_id': match['value_stream']['id'] if match.get('value_stream') else None,
                    'value_stream_name': match['value_stream']['name'] if match.get('value_stream') else 'Unknown',
                    'allocation_method': 'ai_semantic',
                    'confidence': match['confidence'],
                    'reasoning': match.get('reasoning', '')
                })
            else:
                # AI couldn't confidently match
                remaining.append(entry)
        
        return correlated, remaining
    
    def _stage3_proportional_distribution(
        self,
        clockify_entries: List[Dict],
        existing_allocations: List[Dict],
        portfolio_projects: List[Dict],
        vs_map: Dict
    ) -> List[Dict]:
        """
        Stage 3: Distribute remaining hours proportionally across active projects.
        
        Returns:
            List of proportionally allocated entries
        """
        if not clockify_entries:
            return []
        
        # Calculate weights based on already-allocated hours per project
        project_hours = defaultdict(float)
        for allocation in existing_allocations:
            project_hours[allocation['project_id']] += allocation['hours']
        
        # Only use projects that have actual hours logged (active projects)
        active_projects = {
            proj_id: hours for proj_id, hours in project_hours.items() if hours > 0
        }
        
        if not active_projects:
            # Fallback: use all in-progress projects equally
            active_projects = {
                proj['id']: 1.0 for proj in portfolio_projects 
                if proj.get('status') == 'in-progress'
            }
        
        # Calculate proportion weights
        total_hours = sum(active_projects.values())
        weights = {
            proj_id: hours / total_hours 
            for proj_id, hours in active_projects.items()
        }
        
        # Distribute entries proportionally
        proportional = []
        for entry in clockify_entries:
            # Distribute this entry across projects
            for proj_id, weight in weights.items():
                project = next(p for p in portfolio_projects if p['id'] == proj_id)
                vs = vs_map.get(project.get('valueStreamId'))
                
                proportional.append({
                    'clockify_id': entry['id'],
                    'description': entry['description'],
                    'hours': entry['hours'] * weight,  # Proportional hours
                    'date': entry.get('start', '').split('T')[0],
                    'user': entry.get('user_name', 'Unknown'),
                    'project_id': proj_id,
                    'project_name': project['name'],
                    'value_stream_id': vs['id'] if vs else None,
                    'value_stream_name': vs['name'] if vs else 'Unknown',
                    'allocation_method': 'proportional_overhead',
                    'confidence': 0.0,  # N/A for proportional
                    'proportion_weight': weight
                })
        
        return proportional
    
    def _extract_jira_key(self, description: str) -> Optional[str]:
        """Extract Jira key (MAXCOM-XXX) from description."""
        match = re.search(r'MAXCOM-\d+', description, re.IGNORECASE)
        return match.group(0).upper() if match else None
    
    def _map_jira_to_portfolio(
        self,
        jira_issue: Dict,
        portfolio_projects: List[Dict],
        vs_map: Dict
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Map a Jira issue to portfolio project and value stream.
        
        Uses Jira project, epic, labels, and summary to find best match.
        """
        # Try to match based on Jira project name or epic
        jira_project_key = jira_issue.get('project_key', '')
        jira_summary = jira_issue.get('summary', '').lower()
        
        # Simple heuristic: look for project keywords in Jira summary
        for project in portfolio_projects:
            project_name = project.get('name', '').lower()
            # Check if project name words appear in Jira summary
            if any(word in jira_summary for word in project_name.split() if len(word) > 3):
                vs = vs_map.get(project.get('valueStreamId'))
                return project, vs
        
        # No match found
        return None, None
    
    def _get_rag_context(self, description: str) -> str:
        """Retrieve relevant context from RAG, filtered to baseline business process documents."""
        if not self.rag_manager:
            return ""
        
        # Baseline business process document IDs from Confluence
        BASELINE_DOC_IDS = [
            '3669524483',  # Maxim Overview
            '3669458950',  # Section 1: Introduction to Maxim
            '3669393434',  # Section 2: Business Processes
            '3669557264',  # Section 3: Technology Overview
            '3777495108',  # New Lead/Applicant Qualification
            '3669557252',  # Application Intake Process (Dealers)
            '3778314242',  # Application Intake Process (Applicants)
            '3741220865',  # Application Intake
            '3669393452',  # Decision to Proceed with Application
            '3416064004',  # Credit Reports
            '3383918595',  # Calculate Scoring & Pricing Tool
            '3466395684',  # Tvalue
            '3669524507',  # Documentation Process
            '3495526401',  # Document Merge / Conga
            '3811704885',  # Docusign (new)
            '3669721099',  # Booking and Funding Process
            '3899064333',  # Customer Interview
            '3381002248',  # LeaseWorks Integration
            '3669426196',  # Collections, Repossession, and Asset Management
            '3824222276',  # Box
            '3669557278',  # Comparative Analysis: Trucking
            '3668967447',  # Client Documentation Guide
        ]
        
        try:
            # Get more results initially so we can filter
            results = self.rag_manager.search(
                query=description,
                n_results=10,
                use_hybrid=True
            )
            
            # Filter to baseline docs only
            filtered = []
            for result in results:
                metadata = result.get('metadata', {})
                doc_id = metadata.get('page_id') or metadata.get('id', '')
                if str(doc_id) in BASELINE_DOC_IDS:
                    filtered.append(result)
                    if len(filtered) >= 3:  # Stop after 3 matches
                        break
            
            # Format context
            context_parts = []
            for i, result in enumerate(filtered, 1):
                content = result.get('content', result.get('document', ''))
                title = result.get('metadata', {}).get('title', 'Unknown')
                # Allow 800 chars per doc for rich context
                context_parts.append(f"[{title}]\n{content[:800]}")
            
            return "\n\n".join(context_parts)
        except Exception as e:
            logger.warning(f"RAG context retrieval failed: {e}")
            return ""
    
    def _ai_match_to_project(
        self,
        description: str,
        rag_context: str,
        portfolio_projects: List[Dict],
        vs_map: Dict
    ) -> Optional[Dict]:
        """Use AI to match work description to portfolio project with JSON-structured output."""
        if not self.gemini_client:
            return None
        
        # Build concise project list (just ID and name)
        project_list = "\n".join([
            f"{p['id']}: {p['name']}"
            for p in portfolio_projects
        ])
        
        prompt = f"""You are analyzing time tracking entries for a financial services company (Maxim). Match this work entry to the most appropriate portfolio project.

WORK ENTRY: "{description}"

BUSINESS CONTEXT:
{rag_context if rag_context else '(No context available)'}

PORTFOLIO PROJECTS:
{project_list}

Based on the work description and business context, determine the most likely project match.

IMPORTANT RULES:
- Only match if confidence is >75% (0.75)
- Be conservative with matches
- Consider semantic meaning, not just keywords  
- "AIO" could refer to different projects (Application Intake Optimization vs. AI-based solutions)

Return ONLY valid JSON in this format:
{{
  "matched": true/false,
  "project_id": "proj_xxx" or null,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}}"""

        try:
            # Use full 8K token limit for response
            response = self.gemini_client.generate_text(prompt, max_tokens=8000)
            
            # Parse JSON from response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if not json_match:
                logger.warning(f"No JSON found in AI response: {response[:200]}")
                return None
            
            result = json.loads(json_match.group())
            
            # Validate response structure
            if not result.get('matched') or not result.get('project_id'):
                return None
            
            # Find the matched project and value stream
            project = next((p for p in portfolio_projects if p['id'] == result['project_id']), None)
            if not project:
                logger.warning(f"AI matched unknown project ID: {result['project_id']}")
                return None
            
            vs = vs_map.get(project.get('valueStreamId'))
            
            return {
                'project': project,
                'value_stream': vs,
                'confidence': float(result.get('confidence', 0.0)),
                'reasoning': result.get('reasoning', 'No reasoning provided')
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from AI response: {e}")
            return None
        except Exception as e:
            logger.error(f"AI matching failed: {e}")
            return None
    
    def _generate_comprehensive_report(
        self,
        allocations: List[Dict],
        portfolio_projects: List[Dict],
        value_streams: List[Dict],
        stage_stats: Dict
    ) -> Dict:
        """Generate comprehensive allocation report."""
        
        total_hours = sum(a['hours'] for a in allocations)
        
        # By project
        by_project = defaultdict(lambda: {
            'hours': 0.0,
            'jira_direct': 0.0,
            'ai_semantic': 0.0,
            'proportional_overhead': 0.0
        })
        
        for alloc in allocations:
            proj_id = alloc['project_id']
            by_project[proj_id]['hours'] += alloc['hours']
            method = alloc['allocation_method']
            by_project[proj_id][method] = by_project[proj_id].get(method, 0.0) + alloc['hours']
        
        # By value stream
        by_vs = defaultdict(lambda: {
            'hours': 0.0,
            'jira_direct': 0.0,
            'ai_semantic': 0.0,
            'proportional_overhead': 0.0
        })
        
        for alloc in allocations:
            vs_id = alloc.get('value_stream_id')
            if vs_id:
                by_vs[vs_id]['hours'] += alloc['hours']
                method = alloc['allocation_method']
                by_vs[vs_id][method] = by_vs[vs_id].get(method, 0.0) + alloc['hours']
        
        return {
            'total_hours': total_hours,
            'total_entries': len(allocations),
            'by_project': dict(by_project),
            'by_value_stream': dict(by_vs),
            'stage_breakdown': stage_stats
        }
