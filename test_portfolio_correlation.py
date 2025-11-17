"""
Test Portfolio Correlation System

Demonstrates AI-powered correlation of portfolio estimates to actual work.
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

from scripts.analyzers.portfolio_correlator import PortfolioCorrelator, load_portfolio_data
from scripts.connectors.gemini_client import GeminiClient
from scripts.connectors.rag_manager import RAGManager
from scripts.connectors.jira_client import JiraClient
from scripts.connectors.clockify_client import ClockifyClient


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


def test_correlation_with_ai():
    """Test AI-powered correlation."""
    print("\n" + "="*60)
    print("TESTING AI-POWERED PORTFOLIO CORRELATION")
    print("="*60)
    
    # Initialize Gemini client and RAG manager
    print("\n1️⃣  Initializing AI systems...")
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("   Set it in .env file or run with --basic flag")
        return
    
    gemini = GeminiClient(api_key=api_key)
    rag = RAGManager()
    
    print("   ✅ Gemini AI initialized")
    print("   ✅ RAG system initialized")
    
    correlator = PortfolioCorrelator(gemini_client=gemini, rag_manager=rag)
    
    # Load portfolio data
    print("\n2️⃣  Loading portfolio data...")
    portfolio_file = "data-sources/custom-context/faye-portfolio-Laura 1 agressive.json"
    portfolio_projects = load_portfolio_data(portfolio_file)
    
    if not portfolio_projects:
        print(f"❌ No portfolio projects found in {portfolio_file}")
        return
    
    print(f"✅ Loaded {len(portfolio_projects)} portfolio projects")
    
    # Show first few projects
    print("\nPortfolio Projects:")
    for i, proj in enumerate(portfolio_projects[:5], 1):
        name = proj.get('name', 'Unknown')
        hours = proj.get('totalHours', proj.get('total_hours', 0))
        print(f"  {i}. {name} ({hours}h)")
    
    # Load Jira and Clockify data
    print("\n3️⃣  Loading actual work data...")
    jira_issues = load_jira_data()
    clockify_entries = load_clockify_data()
    
    print(f"✅ Loaded {len(jira_issues)} Jira issues")
    print(f"✅ Loaded {len(clockify_entries)} Clockify time entries")
    
    # Test correlation on first project
    if portfolio_projects:
        print("\n4️⃣  Testing correlation on sample project...")
        test_project = portfolio_projects[0]
        project_name = test_project.get('name', 'Unknown')
        
        print(f"\n📊 Correlating: '{project_name}'")
        print(f"   Estimated Hours: {test_project.get('totalHours', test_project.get('total_hours', 0))}h")
        
        # Run AI correlation
        result = correlator.correlate_project(
            portfolio_project=test_project,
            jira_issues=jira_issues,
            clockify_entries=clockify_entries
        )
        
        # Display results
        print("\n" + "-"*60)
        print("CORRELATION RESULTS")
        print("-"*60)
        
        matched = result.get('matched_items', {})
        print(f"\n🔗 Matched Jira Issues: {len(matched.get('jira', []))}")
        for issue in matched.get('jira', [])[:5]:
            print(f"   - {issue.get('key')}: {issue.get('summary', 'No summary')}")
        
        print(f"\n⏰ Matched Clockify Entries: {len(matched.get('clockify', []))}")
        print(f"   Total Hours Logged: {matched.get('clockify_hours', 0):.1f}h")
        
        variance = result.get('variance', {})
        print(f"\n📈 Variance Analysis:")
        print(f"   Estimated: {variance.get('estimated_hours', 0):.1f}h")
        print(f"   Actual: {variance.get('actual_hours', 0):.1f}h")
        print(f"   Delta: {variance.get('delta_hours', 0):+.1f}h ({variance.get('delta_percent', 0):+.1f}%)")
        print(f"   Status: {variance.get('status', 'unknown').upper()}")
        
        print(f"\n🎯 Confidence Score: {result.get('confidence_score', 0):.0%}")
        print(f"\n💡 AI Reasoning:")
        reasoning = result.get('reasoning', 'No reasoning provided')
        for line in reasoning.split('\n'):
            print(f"   {line}")
        
        print("\n" + "="*60)
        print("✅ Correlation test complete!")
        print("="*60)


def test_basic_correlation():
    """Test basic keyword correlation (no AI)."""
    print("\n" + "="*60)
    print("TESTING BASIC KEYWORD CORRELATION")
    print("="*60)
    
    # Initialize without AI
    print("\n1️⃣  Initializing correlator (no AI)...")
    correlator = PortfolioCorrelator(gemini_client=None)
    
    # Load data
    print("\n2️⃣  Loading data...")
    portfolio_projects = load_portfolio_data()
    jira_issues = load_jira_data()
    clockify_entries = load_clockify_data()
    
    if not portfolio_projects:
        print("❌ No portfolio data found")
        return
    
    # Test correlation
    print("\n3️⃣  Running basic keyword matching...")
    test_project = portfolio_projects[0]
    project_name = test_project.get('name', 'Unknown')
    
    print(f"\n📊 Correlating: '{project_name}'")
    
    result = correlator.correlate_project(
        portfolio_project=test_project,
        jira_issues=jira_issues,
        clockify_entries=clockify_entries
    )
    
    # Display results
    matched = result.get('matched_items', {})
    print(f"\n✅ Matched {len(matched.get('jira_keys', []))} Jira issues")
    print(f"✅ Found {matched.get('clockify_hours', 0):.1f}h in Clockify")
    print(f"⚠️  Confidence: {result.get('confidence_score', 0):.0%} (basic matching)")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print("\n🚀 Portfolio Correlation System Test Suite")
    
    # Check which test to run
    if len(sys.argv) > 1 and sys.argv[1] == "--basic":
        test_basic_correlation()
    else:
        test_correlation_with_ai()
