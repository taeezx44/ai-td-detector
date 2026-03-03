#!/usr/bin/env python3
"""
GitHub Repository Data Collector for AI-TD Detector Research

Collects GitHub repositories with AI commit markers and analyzes them for the AI-TD study.
Implements Multi-signal Identification strategy:
1. Explicit Commit Markers
2. Repository Survey (future)
3. Code Pattern Fingerprinting (future)
4. Manual Verification (future)

Usage:
    python scripts/data_collector.py --search "copilot" --max-repos 100
    python scripts/data_collector.py --analyze candidates.csv
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from tqdm import tqdm

# AI commit marker patterns (case-insensitive)
AI_COMMIT_PATTERNS = [
    r"co-authored-by:\s*github\s*copilot",
    r"generated\s+by\s+(copilot|chatgpt|gpt-?4|claude|ai|llm)",
    r"ai[- ]generated",
    r"ai[- ]assisted",
    r"copilot[- ]suggested",
    r"\[copilot\]",
    r"\[ai\]",
    r"\[chatgpt\]",
    r"\[claude\]",
    r"auto[- ]generated\s+by\s+(ai|llm|copilot|chatgpt)",
]

# Compile regex patterns
AI_MARKERS = [re.compile(pattern, re.IGNORECASE) for pattern in AI_COMMIT_PATTERNS]

class GitHubDataCollector:
    """Collects GitHub repositories with AI commit markers."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize collector with GitHub token.
        
        Args:
            token: GitHub personal access token (optional for higher rate limits)
        """
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-TD-Detector-Research/1.0"
        })
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = time.time() + 3600
    
    def _check_rate_limit(self, response: requests.Response):
        """Check and handle GitHub API rate limits."""
        if "X-RateLimit-Remaining" in response.headers:
            self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in response.headers:
            self.rate_limit_reset = int(response.headers["X-RateLimit-Reset"])
        
        if self.rate_limit_remaining < 10:
            wait_time = max(0, self.rate_limit_reset - time.time())
            print(f"Rate limit low. Waiting {wait_time:.0f} seconds...")
            time.sleep(wait_time + 1)
    
    def search_repositories(self, query: str, max_repos: int = 100) -> List[Dict]:
        """
        Search GitHub repositories using commit message search.
        
        Args:
            query: Search query (e.g., "copilot", "ai-generated")
            max_repos: Maximum number of repositories to collect
            
        Returns:
            List of repository metadata
        """
        print(f"Searching repositories with query: {query}")
        
        repos = []
        page = 1
        per_page = 100
        
        with tqdm(total=max_repos, desc="Collecting repositories") as pbar:
            while len(repos) < max_repos:
                # Search commits instead of repositories for better AI marker detection
                search_url = "https://api.github.com/search/commits"
                params = {
                    "q": query,
                    "per_page": min(per_page, max_repos - len(repos)),
                    "page": page
                }
                
                try:
                    response = self.session.get(search_url, params=params)
                    self._check_rate_limit(response)
                    
                    if response.status_code == 403:
                        print("Rate limit exceeded. Please wait or provide a GitHub token.")
                        break
                    elif response.status_code != 200:
                        print(f"Error searching commits: {response.status_code}")
                        print(response.text)
                        break
                    
                    data = response.json()
                    commits = data.get("items", [])
                    
                    if not commits:
                        print("No more commits found.")
                        break
                    
                    # Extract unique repositories from commits
                    for commit in commits:
                        if len(repos) >= max_repos:
                            break
                        
                        repo = commit.get("repository", {})
                        repo_url = repo.get("html_url", "")
                        
                        # Skip if we already have this repo
                        if repo_url in [r.get("url", "") for r in repos]:
                            continue
                        
                        repo_data = self._extract_repo_metadata(repo, commit)
                        repos.append(repo_data)
                        pbar.update(1)
                    
                    page += 1
                    
                except Exception as e:
                    print(f"Error during search: {e}")
                    break
        
        print(f"Found {len(repos)} unique repositories")
        return repos
    
    def _extract_repo_metadata(self, repo: Dict, commit: Dict) -> Dict:
        """Extract relevant metadata from repository and commit."""
        commit_data = commit.get("commit", {})
        commit_message = commit_data.get("message", "")
        
        # Count AI markers in commit message
        ai_marker_count = sum(1 for pattern in AI_MARKERS if pattern.search(commit_message))
        
        # Detect AI confidence level
        ai_confidence = self._detect_ai_confidence(commit_message, ai_marker_count)
        
        return {
            "name": repo.get("full_name", ""),
            "url": repo.get("html_url", ""),
            "description": repo.get("description", ""),
            "language": repo.get("language", ""),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "created_at": repo.get("created_at", ""),
            "updated_at": repo.get("updated_at", ""),
            "size_kb": repo.get("size", 0),
            "is_private": repo.get("private", False),
            "default_branch": repo.get("default_branch", "main"),
            
            # AI-specific data
            "ai_commit_sha": commit.get("sha", ""),
            "ai_commit_message": commit_message,
            "ai_commit_date": commit_data.get("committer", {}).get("date", ""),
            "ai_marker_count": ai_marker_count,
            "ai_confidence": ai_confidence,
            "ai_signals": self._detect_ai_signals(commit_message),
            
            # Collection metadata
            "collected_at": datetime.now().isoformat(),
            "search_query": "",
        }
    
    def _detect_ai_confidence(self, commit_message: str, marker_count: int) -> str:
        """Detect AI confidence level based on commit message."""
        if marker_count >= 2 or "co-authored-by: github copilot" in commit_message.lower():
            return "High"
        elif marker_count == 1:
            return "Medium"
        else:
            return "Low"
    
    def _detect_ai_signals(self, commit_message: str) -> List[str]:
        """Detect specific AI signals in commit message."""
        signals = []
        for i, pattern in enumerate(AI_MARKERS):
            if pattern.search(commit_message):
                signals.append(AI_COMMIT_PATTERNS[i])
        return signals
    
    def analyze_repository(self, repo_full_name: str) -> Dict:
        """
        Analyze a specific repository for AI markers and metadata.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            
        Returns:
            Repository analysis data
        """
        print(f"Analyzing repository: {repo_full_name}")
        
        # Get repository info
        repo_url = f"https://api.github.com/repos/{repo_full_name}"
        response = self.session.get(repo_url)
        self._check_rate_limit(response)
        
        if response.status_code != 200:
            print(f"Error getting repository info: {response.status_code}")
            return {}
        
        repo = response.json()
        
        # Extract repository metadata (FIX: Get real language and size)
        repo_metadata = {
            'name': repo.get('full_name', ''),
            'url': repo.get('html_url', ''),
            'description': repo.get('description', ''),
            'language': repo.get('language', ''),  # Real language from repo API
            'size_kb': repo.get('size', 0),  # Real size in KB from repo API
            'stars': repo.get('stargazers_count', 0),
            'forks': repo.get('forks_count', 0),
            'created_at': repo.get('created_at', ''),
            'updated_at': repo.get('updated_at', ''),
            'is_private': repo.get('private', False),
            'default_branch': repo.get('default_branch', 'main')
        }
        
        # Get recent commits for analysis
        commits_url = f"https://api.github.com/repos/{repo_full_name}/commits"
        params = {
            "per_page": 100,
            "sha": repo.get("default_branch", "main")
        }
        
        response = self.session.get(commits_url, params=params)
        self._check_rate_limit(response)
        
        ai_commits = []
        total_commits = 0
        
        if response.status_code == 200:
            commits = response.json()
            total_commits = len(commits)
            
            for commit in commits:
                commit_data = commit.get("commit", {})
                commit_message = commit_data.get("message", "")
                
                # Check for AI markers
                ai_marker_count = sum(1 for pattern in AI_MARKERS if pattern.search(commit_message))
                if ai_marker_count > 0:
                    ai_commits.append({
                        "sha": commit.get("sha", ""),
                        "message": commit_message,
                        "date": commit_data.get("committer", {}).get("date", ""),
                        "marker_count": ai_marker_count,
                        "confidence": self._detect_ai_confidence(commit_message, ai_marker_count),
                        "signals": self._detect_ai_signals(commit_message)
                    })
        
        # Calculate AI metrics
        ai_commit_ratio = len(ai_commits) / total_commits if total_commits > 0 else 0
        
        # Combine repository metadata with analysis results
        result = repo_metadata.copy()
        result.update({
            # Analysis results
            "total_commits_analyzed": total_commits,
            "ai_commits_found": len(ai_commits),
            "ai_commit_ratio": round(ai_commit_ratio, 4),
            "ai_confidence_level": self._calculate_overall_confidence(ai_commits),
            "ai_commits": ai_commits[:10],  # Store first 10 AI commits for review
            
            # Classification
            "likely_ai_assisted": ai_commit_ratio > 0.05,  # 5% threshold
            "ai_confidence": self._classify_repo_confidence(ai_commit_ratio),
            
            # Collection metadata
            "collected_at": datetime.now().isoformat(),
        })
        
        return result
    
    def _calculate_overall_confidence(self, ai_commits: List[Dict]) -> str:
        """Calculate overall confidence level for repository."""
        if not ai_commits:
            return "None"
        
        high_conf = sum(1 for c in ai_commits if c["confidence"] == "High")
        total = len(ai_commits)
        
        if high_conf / total >= 0.5:
            return "High"
        elif high_conf / total >= 0.2:
            return "Medium"
        else:
            return "Low"
    
    def _classify_repo_confidence(self, ai_commit_ratio: float) -> str:
        """Classify repository AI confidence based on commit ratio."""
        if ai_commit_ratio >= 0.20:  # 20%+ AI commits
            return "High"
        elif ai_commit_ratio >= 0.05:  # 5-20% AI commits
            return "Medium"
        elif ai_commit_ratio > 0:  # 1-5% AI commits
            return "Low"
        else:
            return "None"
    
    def save_to_csv(self, repos: List[Dict], filename: str):
        """Save repository data to CSV file."""
        if not repos:
            print("No repositories to save.")
            return
        
        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        filepath = data_dir / filename
        
        # Get all unique keys from all repos
        all_keys = set()
        for repo in repos:
            all_keys.update(repo.keys())
        
        # Write to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(all_keys))
            writer.writeheader()
            
            for repo in repos:
                # Convert lists to strings for CSV
                row = {}
                for key, value in repo.items():
                    if isinstance(value, list):
                        row[key] = json.dumps(value)
                    else:
                        row[key] = value
                writer.writerow(row)
        
        print(f"Saved {len(repos)} repositories to {filepath}")
    
    def load_from_csv(self, filename: str) -> List[Dict]:
        """Load repository data from CSV file."""
        data_dir = Path("data")
        filepath = data_dir / filename
        
        if not filepath.exists():
            print(f"File {filepath} does not exist.")
            return []
        
        repos = []
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert JSON strings back to lists
                repo = {}
                for key, value in row.items():
                    if key in ['ai_signals', 'ai_commits'] and value:
                        try:
                            repo[key] = json.loads(value)
                        except json.JSONDecodeError:
                            repo[key] = []
                    else:
                        repo[key] = value
                repos.append(repo)
        
        print(f"Loaded {len(repos)} repositories from {filepath}")
        return repos


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="GitHub Data Collector for AI-TD Research")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--search", help="Search query for AI commits")
    parser.add_argument("--max-repos", type=int, default=100, help="Maximum repositories to collect")
    parser.add_argument("--analyze", help="Analyze specific repository (owner/repo)")
    parser.add_argument("--output", default="ai_repos.csv", help="Output CSV filename")
    parser.add_argument("--load", help="Load existing CSV file for analysis")
    
    args = parser.parse_args()
    
    # Initialize collector
    token = args.token or os.getenv("GITHUB_TOKEN")
    collector = GitHubDataCollector(token)
    
    if args.analyze:
        # Analyze specific repository
        result = collector.analyze_repository(args.analyze)
        print(json.dumps(result, indent=2))
        
        # Save to individual file
        filename = f"analysis_{args.analyze.replace('/', '_')}.json"
        with open(f"data/{filename}", 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Saved analysis to data/{filename}")
        
    elif args.search:
        # Search for repositories
        repos = collector.search_repositories(args.search, args.max_repos)
        
        # Save results
        collector.save_to_csv(repos, args.output)
        
        # Print summary
        ai_repos = [r for r in repos if r.get("ai_confidence") != "Low"]
        print(f"\nSummary:")
        print(f"Total repos: {len(repos)}")
        print(f"High confidence AI repos: {len([r for r in repos if r.get('ai_confidence') == 'High'])}")
        print(f"Medium confidence AI repos: {len([r for r in repos if r.get('ai_confidence') == 'Medium'])}")
        print(f"Low confidence AI repos: {len([r for r in repos if r.get('ai_confidence') == 'Low'])}")
        
    elif args.load:
        # Load existing data
        repos = collector.load_from_csv(args.load)
        print(f"Loaded {len(repos)} repositories")
        
        # Analyze a sample
        if repos:
            sample_repo = repos[0].get("name", "")
            if sample_repo:
                print(f"\nSample analysis for {sample_repo}:")
                analysis = collector.analyze_repository(sample_repo)
                print(json.dumps(analysis, indent=2))
    
    else:
        print("Please specify --search, --analyze, or --load")
        parser.print_help()


if __name__ == "__main__":
    main()
