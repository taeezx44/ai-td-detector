#!/usr/bin/env python3
"""
Batch GitHub Repository Collector for AI-TD Research

Automates large-scale repository collection with multiple search queries,
rate limit management, progress tracking, and resume capability.

Usage:
    python scripts/batch_collector.py --config config/batch_config.json
    python scripts/batch_collector.py --resume data/collection_progress.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests
from tqdm import tqdm

# Import existing collector
sys.path.append(str(Path(__file__).parent))
from data_collector import GitHubDataCollector, AI_MARKERS


class BatchCollector:
    """Batch collector for large-scale repository collection."""
    
    def __init__(self, config: Dict, token: Optional[str] = None):
        """
        Initialize batch collector.
        
        Args:
            config: Configuration dictionary
            token: GitHub personal access token
        """
        self.config = config
        self.collector = GitHubDataCollector(token)
        self.progress_file = config.get('progress_file', 'data/collection_progress.json')
        self.output_dir = Path(config.get('output_dir', 'data'))
        self.output_dir.mkdir(exist_ok=True)
        
        # Load existing progress if resuming
        self.progress = self.load_progress()
        
        # Rate limit management
        self.requests_per_hour = config.get('requests_per_hour', 5000)
        self.request_interval = 3600 / self.requests_per_hour  # seconds between requests
        self.last_request_time = 0
        
        # Collection targets
        self.target_repos_per_query = config.get('target_repos_per_query', 100)
        self.max_total_repos = config.get('max_total_repos', 1000)
        
    def load_progress(self) -> Dict:
        """Load collection progress from file."""
        if Path(self.progress_file).exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'started_at': None,
            'completed_at': None,
            'queries_completed': [],
            'current_query_index': 0,
            'total_repos_collected': 0,
            'failed_queries': [],
            'rate_limit_hits': 0,
            'errors': []
        }
    
    def save_progress(self):
        """Save collection progress to file."""
        self.progress['last_updated'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            wait_time = self.request_interval - time_since_last
            if wait_time > 1:
                print(f"Rate limit management: waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def collect_query(self, query: str, query_index: int) -> List[Dict]:
        """
        Collect repositories for a single query.
        
        Args:
            query: Search query string
            query_index: Index of the query in the list
            
        Returns:
            List of repository data
        """
        print(f"\n{'='*60}")
        print(f"Collecting Query {query_index + 1}: {query}")
        print(f"{'='*60}")
        
        repos = []
        page = 1
        per_page = 100
        
        # Calculate target for this query
        remaining_global = self.max_total_repos - self.progress['total_repos_collected']
        target_for_query = min(self.target_repos_per_query, remaining_global)
        
        if target_for_query <= 0:
            print("Global target reached. Skipping query.")
            return repos
        
        print(f"Target: {target_for_query} repositories")
        
        with tqdm(total=target_for_query, desc=f"Query {query_index + 1}") as pbar:
            while len(repos) < target_for_query:
                self.wait_for_rate_limit()
                
                try:
                    # Search commits instead of repositories for better AI marker detection
                    search_url = "https://api.github.com/search/commits"
                    params = {
                        "q": query,
                        "per_page": min(per_page, target_for_query - len(repos)),
                        "page": page
                    }
                    
                    response = self.collector.session.get(search_url, params=params)
                    self.collector._check_rate_limit(response)
                    
                    if response.status_code == 403:
                        self.progress['rate_limit_hits'] += 1
                        print("Rate limit exceeded. Waiting longer...")
                        time.sleep(300)  # Wait 5 minutes
                        continue
                    elif response.status_code != 200:
                        error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                        print(f"Error searching commits: {error_msg}")
                        self.progress['errors'].append({
                            'query': query,
                            'error': error_msg,
                            'timestamp': datetime.now().isoformat()
                        })
                        break
                    
                    data = response.json()
                    commits = data.get("items", [])
                    
                    if not commits:
                        print("No more commits found.")
                        break
                    
                    # Extract unique repositories from commits
                    new_repos = 0
                    for commit in commits:
                        if len(repos) >= target_for_query:
                            break
                        
                        repo = commit.get("repository", {})
                        repo_url = repo.get("html_url", "")
                        
                        # Skip if we already have this repo (across all queries)
                        all_collected_urls = set()
                        # This would need to be tracked more efficiently in production
                        
                        repo_data = self.collector._extract_repo_metadata(repo, commit)
                        repo_data['collection_query'] = query
                        repo_data['collection_query_index'] = query_index
                        repos.append(repo_data)
                        new_repos += 1
                        pbar.update(1)
                    
                    if new_repos == 0:
                        print("No new repositories in this page. Moving to next query.")
                        break
                    
                    page += 1
                    print(f"Collected {len(repos)}/{target_for_query} repositories...")
                    
                except Exception as e:
                    error_msg = f"Exception: {str(e)}"
                    print(f"Error during collection: {error_msg}")
                    self.progress['errors'].append({
                        'query': query,
                        'error': error_msg,
                        'timestamp': datetime.now().isoformat()
                    })
                    break
        
        print(f"Query completed: {len(repos)} repositories collected")
        return repos
    
    def save_query_results(self, repos: List[Dict], query: str, query_index: int):
        """Save results for a single query."""
        if not repos:
            return
        
        # Create filename from query
        safe_query = query.replace('"', '').replace(':', '_').replace(' ', '_')[:50]
        filename = f"batch_{query_index:02d}_{safe_query}.csv"
        filepath = self.output_dir / filename
        
        # Save to CSV
        self.collector.save_to_csv(repos, filename)
        
        # Also save to master file
        master_file = self.output_dir / "batch_all_repos.csv"
        if master_file.exists():
            existing_df = self.collector.load_from_csv("batch_all_repos.csv")
            all_repos = existing_df + repos
        else:
            all_repos = repos
        
        self.collector.save_to_csv(all_repos, "batch_all_repos.csv")
        
        print(f"Saved {len(repos)} repositories to {filename}")
        print(f"Master dataset: {len(all_repos)} total repositories")
    
    def run_collection(self):
        """Run the complete batch collection process."""
        queries = self.config.get('queries', [])
        
        if not queries:
            print("No queries configured!")
            return
        
        print(f"Starting batch collection with {len(queries)} queries")
        print(f"Target: {self.max_total_repos} total repositories")
        print(f"Rate limit: {self.requests_per_hour} requests/hour")
        
        # Update progress
        self.progress['started_at'] = datetime.now().isoformat()
        
        # Start from where we left off
        start_index = self.progress.get('current_query_index', 0)
        
        for i, query in enumerate(queries[start_index:], start=start_index):
            if self.progress['total_repos_collected'] >= self.max_total_repos:
                print("Global target reached. Stopping collection.")
                break
            
            if query in self.progress['queries_completed']:
                print(f"Skipping completed query: {query}")
                continue
            
            try:
                repos = self.collect_query(query, i)
                self.save_query_results(repos, query, i)
                
                # Update progress
                self.progress['queries_completed'].append(query)
                self.progress['current_query_index'] = i + 1
                self.progress['total_repos_collected'] += len(repos)
                self.save_progress()
                
                print(f"Progress: {self.progress['total_repos_collected']}/{self.max_total_repos} repositories")
                
            except KeyboardInterrupt:
                print("\nCollection interrupted by user. Progress saved.")
                self.save_progress()
                break
            except Exception as e:
                print(f"Failed to collect query '{query}': {e}")
                self.progress['failed_queries'].append(query)
                self.save_progress()
                continue
        
        # Finalize
        self.progress['completed_at'] = datetime.now().isoformat()
        self.save_progress()
        
        self.print_summary()
    
    def print_summary(self):
        """Print collection summary."""
        print("\n" + "="*60)
        print("BATCH COLLECTION SUMMARY")
        print("="*60)
        
        duration = None
        if self.progress['started_at'] and self.progress['completed_at']:
            start = datetime.fromisoformat(self.progress['started_at'])
            end = datetime.fromisoformat(self.progress['completed_at'])
            duration = end - start
        
        print(f"Total repositories collected: {self.progress['total_repos_collected']}")
        print(f"Queries completed: {len(self.progress['queries_completed'])}/{len(self.config.get('queries', []))}")
        print(f"Failed queries: {len(self.progress['failed_queries'])}")
        print(f"Rate limit hits: {self.progress['rate_limit_hits']}")
        print(f"Errors encountered: {len(self.progress['errors'])}")
        
        if duration:
            print(f"Collection duration: {duration}")
            if duration.total_seconds() > 0:
                rate = self.progress['total_repos_collected'] / duration.total_seconds() * 3600
                print(f"Average rate: {rate:.1f} repos/hour")
        
        if self.progress['failed_queries']:
            print(f"\nFailed queries:")
            for query in self.progress['failed_queries']:
                print(f"  - {query}")
        
        if self.progress['errors'][-5:]:  # Show last 5 errors
            print(f"\nRecent errors:")
            for error in self.progress['errors'][-5:]:
                print(f"  - {error['query']}: {error['error']}")
        
        print("="*60)
    
    def create_default_config(self, output_path: str):
        """Create a default configuration file."""
        config = {
            "queries": [
                '"co-authored-by: github copilot"',
                '"generated by copilot"',
                '"generated by chatgpt"',
                '"generated by claude"',
                '"ai-assisted"',
                '"ai-generated"',
                '"copilot-suggested"',
                '[copilot]',
                '[ai]',
                '[chatgpt]',
                'copilot language:python',
                'copilot language:javascript',
                'chatgpt language:python',
                'ai-assisted language:typescript',
                'llm-generated',
                'auto-generated by ai'
            ],
            "target_repos_per_query": 100,
            "max_total_repos": 1000,
            "requests_per_hour": 5000,
            "output_dir": "data",
            "progress_file": "data/collection_progress.json"
        }
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Default configuration saved to {output_path}")
        return config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Batch GitHub Repository Collector")
    parser.add_argument("--config", help="Configuration JSON file")
    parser.add_argument("--create-config", help="Create default config file")
    parser.add_argument("--resume", help="Resume from progress file")
    parser.add_argument("--token", help="GitHub personal access token")
    
    args = parser.parse_args()
    
    if args.create_config:
        collector = BatchCollector({})
        collector.create_default_config(args.create_config)
        return
    
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    elif args.resume:
        # Load config from progress file
        with open(args.resume, 'r') as f:
            progress = json.load(f)
        # Use default config with progress info
        collector = BatchCollector({})
        config = collector.create_default_config("temp_config.json")
        config['progress_file'] = args.resume
    else:
        print("Please specify --config or --resume")
        parser.print_help()
        return
    
    token = args.token or os.getenv("GITHUB_TOKEN")
    collector = BatchCollector(config, token)
    
    print("Starting batch collection...")
    print("Press Ctrl+C to pause and resume later")
    print(f"Progress will be saved to: {collector.progress_file}")
    
    try:
        collector.run_collection()
    except KeyboardInterrupt:
        print("\nCollection interrupted. Progress saved.")
        collector.save_progress()


if __name__ == "__main__":
    main()
