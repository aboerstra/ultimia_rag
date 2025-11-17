"""
Portfolio Correlation Persistence

Saves correlation results and indexes them in RAG for conversational access.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class CorrelationPersistence:
    """
    Manages persistence and RAG indexing of portfolio correlations.
    """
    
    def __init__(self, storage_path: str = "data-sources/custom-context/portfolio-correlations.json", rag_manager=None):
        """
        Initialize persistence manager.
        
        Args:
            storage_path: Path to save correlation results
            rag_manager: RAGManager instance for indexing
        """
        self.storage_path = Path(storage_path)
        self.rag_manager = rag_manager
        self.correlations = self._load_correlations()
    
    def _load_correlations(self) -> Dict:
        """Load existing correlations from file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse {self.storage_path}, starting fresh")
                return {}
        return {}
    
    def save_correlation(
        self,
        project_name: str,
        correlation_result: Dict,
        portfolio_project: Dict
    ) -> None:
        """
        Save correlation result and index in RAG.
        
        Args:
            project_name: Portfolio project name (key)
            correlation_result: Correlation analysis results
            portfolio_project: Full portfolio project details
        """
        # Create correlation record
        correlation_record = {
            "project_name": project_name,
            "analyzed_at": datetime.now().isoformat(),
            "portfolio_details": {
                "description": portfolio_project.get('description', ''),
                "estimated_hours": portfolio_project.get('total_hours', 0),
                "start_date": portfolio_project.get('start_date', ''),
                "end_date": portfolio_project.get('end_date', '')
            },
            "matched_jira_keys": correlation_result['matched_items']['jira_keys'],
            "matched_jira_count": len(correlation_result['matched_items']['jira']),
            "clockify_hours": correlation_result['matched_items']['clockify_hours'],
            "clockify_entry_count": len(correlation_result['matched_items']['clockify']),
            "confidence_score": correlation_result['confidence_score'],
            "reasoning": correlation_result['reasoning'],
            "variance": correlation_result['variance']
        }
        
        # Save to storage
        self.correlations[project_name] = correlation_record
        self._write_correlations()
        
        # Index in RAG for conversational access
        self._index_in_rag(correlation_record)
        
        logger.info(f"Saved correlation for '{project_name}' with {correlation_record['confidence_score']:.0%} confidence")
    
    def _write_correlations(self) -> None:
        """Write correlations to file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.correlations, f, indent=2)
    
    def _index_in_rag(self, correlation_record: Dict) -> None:
        """
        Index correlation in RAG system for conversational retrieval.
        
        Creates a searchable summary that AI can reference.
        """
        if not self.rag_manager:
            logger.warning("No RAG manager provided, skipping indexing")
            return
        
        project_name = correlation_record['project_name']
        variance = correlation_record['variance']
        
        # Create human-readable summary
        summary = f"""PORTFOLIO CORRELATION: {project_name}

**Analysis Date**: {correlation_record['analyzed_at']}

**Estimated Hours**: {variance['estimated_hours']:.1f}h  
**Actual Hours Logged**: {variance['actual_hours']:.1f}h  
**Variance**: {variance['delta_hours']:+.1f}h ({variance['delta_percent']:+.1f}%)  
**Status**: {variance['status'].upper().replace('_', ' ')}

**Matched Jira Issues** ({correlation_record['matched_jira_count']}):
{', '.join(correlation_record['matched_jira_keys'])}

**Clockify Time Tracking**: {correlation_record['clockify_hours']:.1f}h across {correlation_record['clockify_entry_count']} entries

**Confidence**: {correlation_record['confidence_score']:.0%}

**AI Analysis**: {correlation_record['reasoning']}

---
This correlation allows accurate tracking of portfolio estimates vs actual work completed.
"""
        
        try:
            # Add to RAG with metadata
            self.rag_manager.add_document(
                content=summary,
                metadata={
                    'source': f'Portfolio Correlation: {project_name}',
                    'type': 'portfolio_correlation',
                    'project_name': project_name,
                    'confidence': correlation_record['confidence_score'],
                    'analyzed_at': correlation_record['analyzed_at']
                }
            )
            logger.info(f"Indexed '{project_name}' correlation in RAG system")
        except Exception as e:
            logger.error(f"Failed to index correlation in RAG: {e}")
    
    def get_correlation(self, project_name: str) -> Dict:
        """
        Retrieve saved correlation for a project.
        
        Args:
            project_name: Portfolio project name
            
        Returns:
            Correlation record or empty dict
        """
        return self.correlations.get(project_name, {})
    
    def list_correlations(self) -> List[Dict]:
        """
        List all saved correlations.
        
        Returns:
            List of correlation records
        """
        return list(self.correlations.values())
    
    def get_summary_report(self) -> str:
        """
        Generate a summary report of all correlations.
        
        Returns:
            Formatted report text
        """
        if not self.correlations:
            return "No portfolio correlations have been analyzed yet."
        
        report = "# Portfolio Correlation Summary\n\n"
        report += f"Total Projects Analyzed: {len(self.correlations)}\n\n"
        
        for project_name, corr in sorted(self.correlations.items()):
            variance = corr['variance']
            status_emoji = {
                'on_track': '✅',
                'over_budget': '⚠️',
                'under_budget': '📉'
            }.get(variance['status'], '❓')
            
            report += f"\n## {status_emoji} {project_name}\n"
            report += f"- **Estimated**: {variance['estimated_hours']:.1f}h\n"
            report += f"- **Actual**: {variance['actual_hours']:.1f}h\n"
            report += f"- **Variance**: {variance['delta_hours']:+.1f}h ({variance['delta_percent']:+.1f}%)\n"
            report += f"- **Confidence**: {corr['confidence_score']:.0%}\n"
            report += f"- **Jira Issues**: {corr['matched_jira_count']}\n"
            report += f"- **Analyzed**: {corr['analyzed_at'][:10]}\n"
        
        return report


def correlate_and_save(
    portfolio_correlator,
    persistence_manager,
    portfolio_project: Dict,
    jira_issues: List[Dict],
    clockify_entries: List[Dict]
) -> Dict:
    """
    Helper function to correlate and automatically save/index results.
    
    Args:
        portfolio_correlator: PortfolioCorrelator instance
        persistence_manager: CorrelationPersistence instance
        portfolio_project: Portfolio project to correlate
        jira_issues: Candidate Jira issues
        clockify_entries: Candidate time entries
        
    Returns:
        Correlation results
    """
    project_name = portfolio_project.get('name', 'Unknown')
    
    # Run correlation
    result = portfolio_correlator.correlate_project(
        portfolio_project=portfolio_project,
        jira_issues=jira_issues,
        clockify_entries=clockify_entries
    )
    
    # Save and index
    persistence_manager.save_correlation(
        project_name=project_name,
        correlation_result=result,
        portfolio_project=portfolio_project
    )
    
    return result
