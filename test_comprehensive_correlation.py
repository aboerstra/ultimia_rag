"""
Test Comprehensive Portfolio Correlation System

Demonstrates 100% allocation of all Clockify hours to projects and value streams.
"""

import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from scripts.analyzers.comprehensive_correlator import ComprehensiveCorrelator
from scripts.analyzers.portfolio_correlator import load_portfolio_data
from scripts.connectors.gemini_client import GeminiClient
from scripts.connectors.rag_manager import RAGManager


def load_jira_data(filepath="data-sources/jira/raw/issues.json"):
    """Load Jira issues from file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Jira data not found at {filepath}")
        return []


def load_clockify_data(filepath="data-sources/clockify/raw/time_entries.json"):
    """Load Clockify time entries from file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Clockify data not found at {filepath}")
        return []


def print_report(result: dict, portfolio_projects: list, value_streams: list):
    """Print a comprehensive allocation report."""
    report = result['report']
    stage_stats = result['stage_stats']
    
    print("\n" + "="*70)
    print("📊 COMPREHENSIVE PORTFOLIO HOURS ALLOCATION REPORT")
    print("="*70)
    
    # Total summary
    total_hours = report['total_hours']
    total_entries = report['total_entries']
    
    print(f"\n🔢 OVERALL SUMMARY")
    print(f"   Total Clockify Hours: {total_hours:.1f}h")
    print(f"   Total Entries: {total_entries}")
    print(f"   Allocation Coverage: {result['coverage']:.0f}%")
    
    # Allocation method breakdown
    print(f"\n📈 ALLOCATION METHOD BREAKDOWN")
    print(f"   ├─ Jira Direct: {stage_stats['jira_direct']['count']} entries ({stage_stats['jira_direct']['hours']:.1f}h, {stage_stats['jira_direct']['hours']/total_hours*100:.1f}%)")
    print(f"   ├─ AI Semantic: {stage_stats['ai_semantic']['count']} entries ({stage_stats['ai_semantic']['hours']:.1f}h, {stage_stats['ai_semantic']['hours']/total_hours*100:.1f}%)")
    print(f"   └─ Proportional Overhead: {stage_stats['proportional']['count']} original entries")
    print(f"      distributed as {sum(1 for a in result['allocations'] if a['allocation_method'] == 'proportional_overhead')} allocations")
    print(f"      ({stage_stats['proportional']['hours']:.1f}h, {stage_stats['proportional']['hours']/total_hours*100:.1f}%)")
    
    # By value stream
    print(f"\n🌊 BY VALUE STREAM")
    vs_map = {vs['id']: vs for vs in value_streams}
    for vs_id, vs_data in sorted(report['by_value_stream'].items(), key=lambda x: x[1]['hours'], reverse=True):
        vs = vs_map.get(vs_id, {'name': 'Unknown'})
        hours = vs_data['hours']
        pct = (hours / total_hours * 100) if total_hours > 0 else 0
        
        print(f"\n   {vs['name']}: {hours:.1f}h ({pct:.1f}%)")
        print(f"      ├─ Direct (Jira): {vs_data['jira_direct']:.1f}h")
        print(f"      ├─ AI Match: {vs_data['ai_semantic']:.1f}h")
        print(f"      └─ Overhead Dist: {vs_data['proportional_overhead']:.1f}h")
    
    # By project (top 10)
    print(f"\n📦 BY PROJECT (Top 10)")
    proj_map = {proj['id']: proj for proj in portfolio_projects}
    sorted_projects = sorted(report['by_project'].items(), key=lambda x: x[1]['hours'], reverse=True)
    
    for i, (proj_id, proj_data) in enumerate(sorted_projects[:10], 1):
        project = proj_map.get(proj_id, {'name': 'Unknown', 'totalHours': 0})
        hours = proj_data['hours']
        estimated = project.get('totalHours', project.get('total_hours', 0))
        pct = (hours / total_hours * 100) if total_hours > 0 else 0
        
        # Calculate variance
        if estimated > 0:
            variance = hours - estimated
            variance_pct = (variance / estimated * 100)
            variance_str = f"{variance:+.1f}h ({variance_pct:+.1f}%)"
        else:
            variance_str = "N/A (no estimate)"
        
        print(f"\n   {i}. {project['name']}")
        print(f"      Hours: {hours:.1f}h ({pct:.1f}% of total)")
        print(f"      Estimated: {estimated}h | Actual: {hours:.1f}h | Variance: {variance_str}")
        print(f"      Allocation: Direct={proj_data['jira_direct']:.1f}h, AI={proj_data['ai_semantic']:.1f}h, Overhead={proj_data['proportional_overhead']:.1f}h")
    
    print("\n" + "="*70)
    print("✅ 100% ALLOCATION COMPLETE")
    print("="*70)


def main():
    """Run comprehensive correlation test."""
    print("\n🚀 COMPREHENSIVE PORTFOLIO CORRELATION TEST")
    print("   (100% Allocation System)")
    print()
    
    # Initialize AI systems
    print("1️⃣  Initializing systems...")
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        gemini = GeminiClient(api_key=api_key)
        rag = RAGManager()
        print("   ✅ Gemini AI initialized")
        print("   ✅ RAG system initialized")
    else:
        print("   ⚠️  No Gemini API key - AI matching disabled")
        gemini = None
        rag = None
    
    correlator = ComprehensiveCorrelator(
        gemini_client=gemini,
        rag_manager=rag
    )
    
    # Load data
    print("\n2️⃣  Loading data...")
    portfolio_file = "data-sources/custom-context/faye-portfolio-Laura 1 agressive.json"
    
    with open(portfolio_file, 'r') as f:
        portfolio_data = json.load(f)
    
    portfolio_projects = portfolio_data['projects']
    value_streams = portfolio_data['valueStreams']
    jira_issues = load_jira_data()
    clockify_entries = load_clockify_data()
    
    print(f"   ✅ {len(portfolio_projects)} portfolio projects")
    print(f"   ✅ {len(value_streams)} value streams")
    print(f"   ✅ {len(jira_issues)} Jira issues")
    print(f"   ✅ {len(clockify_entries)} Clockify entries ({sum(e['hours'] for e in clockify_entries):.1f}h total)")
    
    # Run comprehensive correlation
    print("\n3️⃣  Running comprehensive correlation...")
    print("   Stage 1: Jira-based direct correlation...")
    print("   Stage 2: AI semantic matching..." if gemini else "   Stage 2: SKIPPED (no AI)")
    print("   Stage 3: Proportional distribution...")
    
    result = correlator.correlate_all_hours(
        portfolio_projects=portfolio_projects,
        value_streams=value_streams,
        jira_issues=jira_issues,
        clockify_entries=clockify_entries
    )
    
    # Print comprehensive report
    print_report(result, portfolio_projects, value_streams)
    
    # Verification
    original_total = sum(e['hours'] for e in clockify_entries)
    allocated_total = sum(a['hours'] for a in result['allocations'])
    
    print(f"\n🔍 VERIFICATION")
    print(f"   Original Clockify hours: {original_total:.2f}h")
    print(f"   Allocated hours: {allocated_total:.2f}h")
    print(f"   Difference: {abs(original_total - allocated_total):.4f}h")
    
    if abs(original_total - allocated_total) < 0.01:
        print(f"   ✅ PERFECT ALLOCATION - All hours accounted for!")
    else:
        print(f"   ⚠️  Allocation mismatch detected")
    
    # Save results
    output_file = "portfolio_allocation_results.json"
    with open(output_file, 'w') as f:
        # Convert for JSON serialization
        json_safe_result = {
            'stage_stats': result['stage_stats'],
            'report': result['report'],
            'coverage': result['coverage'],
            'total_allocations': len(result['allocations'])
        }
        json.dump(json_safe_result, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
