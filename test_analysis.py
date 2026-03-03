#!/usr/bin/env python3
"""
Test script to verify the AI-TD analysis is working
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from scripts.real_repo_analyzer import RealRepositoryAnalyzer

def test_analysis():
    """Test the repository analysis."""
    analyzer = RealRepositoryAnalyzer()
    
    # Test with a simple repository
    test_repo = "https://github.com/octocat/Hello-World"
    print(f"Testing analysis with: {test_repo}")
    
    result = analyzer.analyze_repo_url(test_repo)
    
    print("\nAnalysis Result:")
    print(f"Success: {result.get('analysis_success', False)}")
    
    if result.get('analysis_success'):
        print(f"Repository: {result.get('name', 'Unknown')}")
        print(f"AI-TD Score: {result.get('ai_td_score', 0):.3f}")
        print(f"Complexity: {result.get('complexity_score', 0):.3f}")
        print(f"Documentation: {result.get('documentation_score', 0):.3f}")
        print(f"Files analyzed: {result.get('files_analyzed', 0)}")
        print(f"Severity: {result.get('severity', 'LOW')}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_analysis()
