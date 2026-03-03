#!/usr/bin/env python3
"""
Human Repository Collector for AI-TD Research

Collects repositories with NO AI markers to serve as control group.
These repositories are assumed to be human-written for comparison.

Usage:
    python scripts/human_collector.py --output data/human_repos.csv --max-repos 20
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
from tqdm import tqdm

# Import existing collector
sys.path.append(str(Path(__file__).parent))
from data_collector import GitHubDataCollector, AI_MARKERS


class HumanRepositoryCollector:
    """Collect human-written repositories for control group."""
    
    def __init__(self, token: str = None):
        """Initialize collector with optional GitHub token."""
        self.session = requests.Session()
        self.token = token
        
        if token:
            self.session.headers.update({
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            })
        
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = time.time() + 3600
    
    def _check_rate_limit(self, response):
        """Check and handle GitHub API rate limits."""
        remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
        reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 3600))
        
        self.rate_limit_remaining = remaining
        self.rate_limit_reset = reset_time
        
        if remaining <= 1:
            wait_time = max(0, reset_time - time.time() + 60)
            if wait_time > 0:
                print(f"Rate limit reached. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
    
    def search_human_repositories(self, query: str, max_repos: int = 20) -> List[Dict]:
        """
        Search for repositories and filter out ones with AI markers.
        
        Args:
            query: Search query string
            max_repos: Maximum number of repositories to collect
            
        Returns:
            List of human-written repositories
        """
        print(f"Searching for human repositories: {query}")
        
        human_repos = []
        page = 1
        per_page = 100
        
        with tqdm(total=max_repos, desc="Collecting Human Repos") as pbar:
            while len(human_repos) < max_repos:
                # Search repositories
                search_url = "https://api.github.com/search/repositories"
                params = {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": per_page,
                    "page": page
                }
                
                response = self.session.get(search_url, params=params)
                self._check_rate_limit(response)
                
                if response.status_code != 200:
                    print(f"Error searching repositories: {response.status_code}")
                    break
                
                data = response.json()
                repos = data.get("items", [])
                
                if not repos:
                    print("No more repositories found.")
                    break
                
                # Check each repository for AI markers
                for repo in repos:
                    if len(human_repos) >= max_repos:
                        break
                    
                    repo_name = repo.get("full_name", "")
                    
                    # Skip if too small or too large
                    size = repo.get("size", 0)
                    if size < 5000 or size > 50000:  # 5K-50K lines
                        continue
                    
                    # Check for AI markers in recent commits
                    if self._has_ai_markers(repo_name):
                        print(f"Skipping {repo_name} - has AI markers")
                        continue
                    
                    # This appears to be a human repository
                    human_repo_data = self._extract_repo_metadata(repo)
                    human_repo_data.update({
                        "ai_commits_found": 0,
                        "ai_commit_ratio": 0.0,
                        "ai_confidence": "None",
                        "ai_confidence_level": "None",
                        "likely_ai_assisted": False,
                        "total_commits_analyzed": 0,
                        "ai_commits": [],
                        "collected_at": datetime.now().isoformat(),
                        "search_query": query,
                        "repo_type": "human_control"
                    })
                    
                    human_repos.append(human_repo_data)
                    pbar.update(1)
                
                page += 1
                print(f"Collected {len(human_repos)}/{max_repos} human repositories")
        
        return human_repos
    
    def _has_ai_markers(self, repo_full_name: str) -> bool:
        """
        Check if repository has AI markers in recent commits.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            
        Returns:
            True if AI markers found, False otherwise
        """
        commits_url = f"https://api.github.com/repos/{repo_full_name}/commits"
        params = {"per_page": 50}  # Check last 50 commits
        
        response = self.session.get(commits_url, params=params)
        self._check_rate_limit(response)
        
        if response.status_code != 200:
            return False
        
        commits = response.json()
        
        for commit in commits:
            commit_data = commit.get("commit", {})
            commit_message = commit_data.get("message", "")
            
            # Check for AI markers
            for pattern in AI_MARKERS:
                if pattern.search(commit_message):
                    return True
        
        return False
    
    def _extract_repo_metadata(self, repo: Dict) -> Dict:
        """Extract repository metadata from GitHub API response."""
        return {
            "name": repo.get("full_name", ""),
            "url": repo.get("html_url", ""),
            "description": repo.get("description", ""),
            "language": repo.get("language", ""),
            "size_kb": repo.get("size", 0),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "created_at": repo.get("created_at", ""),
            "updated_at": repo.get("updated_at", ""),
            "is_private": repo.get("private", False),
            "default_branch": repo.get("default_branch", "main"),
        }
    
    def save_to_csv(self, repos: List[Dict], filename: str):
        """Save repositories to CSV file."""
        if not repos:
            print("No repositories to save")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(repos)
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        # Save to CSV
        output_path = Path("data") / filename
        df.to_csv(output_path, index=False)
        print(f"Saved {len(repos)} human repositories to {output_path}")
    
    def collect_balanced_human_set(self, max_repos: int = 20) -> List[Dict]:
        """
        Collect a balanced set of human repositories matching AI repo characteristics.
        
        Args:
            max_repos: Number of human repositories to collect
            
        Returns:
            List of human repositories
        """
        print(f"Collecting {max_repos} human repositories for control group...")
        
        # Define search queries for human repositories
        human_queries = [
            "language:python stars:100..1000 created:>2022-01-01",
            "language:javascript stars:100..1000 created:>2022-01-01", 
            "language:typescript stars:100..1000 created:>2022-01-01",
            "stars:>200 NOT co-authored-by:copilot NOT generated-by:chatgpt",
            "stars:>200 NOT ai-assisted NOT ai-generated",
            "created:>2022-01-01 stars:100..500 NOT copilot",
            "language:python created:>2022-01-01 size:5000..50000",
            "framework library tool utility stars:100..1000"
        ]
        
        all_human_repos = []
        target_per_query = max_repos // len(human_queries)
        
        for query in human_queries:
            if len(all_human_repos) >= max_repos:
                break
            
            remaining = max_repos - len(all_human_repos)
            repos = self.search_human_repositories(query, min(target_per_query, remaining))
            all_human_repos.extend(repos)
        
        # Remove duplicates
        seen_urls = set()
        unique_repos = []
        for repo in all_human_repos:
            if repo['url'] not in seen_urls:
                seen_urls.add(repo['url'])
                unique_repos.append(repo)
        
        print(f"Collected {len(unique_repos)} unique human repositories")
        return unique_repos[:max_repos]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Human Repository Collector")
    parser.add_argument("--output", default="human_repos.csv", help="Output CSV file")
    parser.add_argument("--max-repos", type=int, default=20, help="Maximum repositories to collect")
    parser.add_argument("--token", help="GitHub personal access token")
    
    args = parser.parse_args()
    
    token = args.token or os.getenv("GITHUB_TOKEN")
    collector = HumanRepositoryCollector(token)
    
    # Collect human repositories
    human_repos = collector.collect_balanced_human_set(args.max_repos)
    
    if human_repos:
        collector.save_to_csv(human_repos, args.output)
        
        # Print summary
        languages = {}
        for repo in human_repos:
            lang = repo.get('language', 'Unknown')
            languages[lang] = languages.get(lang, 0) + 1
        
        print(f"\nHuman Repository Summary:")
        print(f"  Total: {len(human_repos)} repositories")
        print(f"  Languages: {languages}")
        print(f"  Avg stars: {sum(r.get('stars', 0) for r in human_repos) / len(human_repos):.1f}")
        print(f"  Avg size: {sum(r.get('size_kb', 0) for r in human_repos) / len(human_repos):.0f} KB")
    else:
        print("No human repositories collected")


if __name__ == "__main__":
    main()
