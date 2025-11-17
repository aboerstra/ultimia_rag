#!/usr/bin/env python3
"""
Build Portfolio Correlation Reference (Batch Process)

This script runs the comprehensive 3-stage correlation offline (can take 5-10 minutes)
and saves a persistent reference that can be queried instantly in the chat.

Usage:
    python scripts/build_correlation_reference.py              # Full rebuild
    python scripts/build_correlation_reference.py --update     # Full rebuild (same)
    python scripts/build_correlation_reference.py --incremental # Future: update only new entries
"""

import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from connectors.gemini_client import GeminiClient
from connectors.rag_manager import RAGManager
from connectors.jira_client import JiraClient
from connectors.clockify_client import ClockifyClient
from analyzers.comprehensive_correlator import ComprehensiveCorrelator
from analyzers.correlation_persistence import CorrelationPersistence

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_portfolio_snapshot():
    """Load the most recent portfolio snapshot."""
    portfolio_dir = Path(__file__).parent.parent / 'data-sources' / 'custom-context'
    
    # Look for portfolio JSON files
    portfolio_files = list(portfolio_dir.glob('*portfolio*.json'))
    
    if not portfolio_files:
        logger.error("No portfolio snapshot found!")
        return None, None
    
    # Use the most recent
    latest = max(portfolio_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Loading portfolio snapshot: {latest.name}")
    
    with open(latest, 'r') as f:
        snapshot = json.load(f)
    
    return snapshot.get('projects', []), snapshot.get('valueStreams', [])


def build_correlation_reference(incremental=False):
    """
    Build the correlation reference by running comprehensive 3-stage correlation.
    
    Args:
        incremental: If True, only process new entries (future enhancement)
    """
    logger.info("=" * 80)
    logger.info("BUILDING PORTFOLIO CORRELATION REFERENCE")
    logger.info("=" * 80)
    logger.info("This process may take 5-10 minutes with AI matching enabled.")
    logger.info("")
    
    # 1. Initialize components
    logger.info("1. Initializing components...")
    gemini_client = GeminiClient(api_key=Config.GEMINI_API_KEY)
    rag_manager = RAGManager()
    jira_client = JiraClient()  # Not used directly, only for correlator
    
    correlator = ComprehensiveCorrelator(
        gemini_client=gemini_client,
        rag_manager=rag_manager,
        jira_client=jira_client
    )
    
    persistence = CorrelationPersistence()
    
    # 2. Load portfolio snapshot
    logger.info("\n2. Loading portfolio snapshot...")
    projects, value_streams = load_portfolio_snapshot()
    
    if not projects:
        logger.error("Failed to load portfolio data!")
        return False
    
    logger.info(f"   Loaded {len(projects)} projects, {len(value_streams)} value streams")
    
    # 3. Load Jira issues from cached file
    logger.info("\n3. Loading Jira issues from cached file...")
    jira_file = Path(__file__).parent.parent / 'data-sources' / 'jira' / 'raw' / 'issues.json'
    with open(jira_file, 'r') as f:
        jira_issues = json.load(f)
    logger.info(f"   Loaded {len(jira_issues)} Jira issues (MAXCOM)")
    
    # 4. Load Clockify entries from cached file
    logger.info("\n4. Loading Clockify entries from cached file...")
    clockify_file = Path(__file__).parent.parent / 'data-sources' / 'clockify' / 'raw' / 'time_entries.json'
    with open(clockify_file, 'r') as f:
        clockify_entries = json.load(f)
    logger.info(f"   Loaded {len(clockify_entries)} Clockify entries (MAXCOM)")
    
    # 5. Run comprehensive correlation
    logger.info("\n5. Running 3-stage correlation...")
    logger.info("   Stage 1: Direct Jira correlation")
    logger.info("   Stage 2: AI semantic matching (with filtered RAG)")
    logger.info("   Stage 3: Proportional overhead distribution")
    logger.info("")
    
    start_time = datetime.now()
    
    results = correlator.correlate_all_hours(
        portfolio_projects=projects,
        value_streams=value_streams,
        jira_issues=jira_issues,
        clockify_entries=clockify_entries
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"\n✓ Correlation complete in {elapsed:.1f} seconds")
    
    # 6. Display summary
    logger.info("\n6. Correlation Summary:")
    logger.info(f"   Total hours allocated: {results['report']['total_hours']:.1f}h")
    logger.info(f"   Total entries: {results['report']['total_entries']}")
    logger.info(f"   Coverage: {results['coverage']}%")
    logger.info("")
    logger.info("   Breakdown by stage:")
    for stage, stats in results['stage_stats'].items():
        logger.info(f"     - {stage}: {stats['count']} entries, {stats['hours']:.1f}h")
    
    # 7. Save to persistent storage
    logger.info("\n7. Saving correlation reference...")
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata = {
        'generated_at': timestamp,
        'portfolio_projects': len(projects),
        'value_streams': len(value_streams),
        'jira_issues': len(jira_issues),
        'clockify_entries': len(clockify_entries),
        'total_hours': results['report']['total_hours'],
        'coverage': results['coverage']
    }
    
    persistence.save_correlation(
        allocations=results['allocations'],
        metadata=metadata
    )
    
    logger.info(f"   ✓ Saved to: {persistence.storage_path}")
    
    logger.info("\n" + "=" * 80)
    logger.info("CORRELATION REFERENCE BUILD COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Generated at: {timestamp}")
    logger.info(f"Total processing time: {elapsed:.1f} seconds")
    logger.info("\nThe correlation reference is now available for instant chat queries!")
    
    return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Build portfolio correlation reference (batch process)'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Perform full rebuild (same as default)'
    )
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Update only new entries (future enhancement)'
    )
    
    args = parser.parse_args()
    
    try:
        success = build_correlation_reference(incremental=args.incremental)
        
        if success:
            logger.info("\n✅ Build successful!")
            sys.exit(0)
        else:
            logger.error("\n❌ Build failed!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Build failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
