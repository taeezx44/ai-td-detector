#!/usr/bin/env python3
"""
Real Repository Analyzer for AI-TD Detector

Analyzes real GitHub repositories for AI-induced technical debt.
Supports multiple programming languages and provides comprehensive analysis.
"""

import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from tqdm import tqdm

# Add parent directories to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "engine"))

from engine import AITDDetector


class RealRepositoryAnalyzer:
    """Analyzes real repositories for AI-induced technical debt."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.detector = AITDDetector()
        self.temp_dir = None
        self.supported_languages = {
            'python': ['.py'],
            'javascript': ['.js'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cc', '.cxx'],
            'c': ['.c'],
            'go': ['.go'],
            'rust': ['.rs'],
            'ruby': ['.rb'],
            'php': ['.php'],
        }
    
    def analyze_repo_url(self, repo_url: str) -> Dict:
        """
        Analyze a repository from URL.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Parse repository URL
            repo_info = self._parse_repo_url(repo_url)
            if not repo_info:
                return {
                    'analysis_success': False,
                    'error': 'Invalid repository URL'
                }
            
            # Clone repository temporarily
            repo_path = self._clone_repository(repo_info)
            if not repo_path:
                return {
                    'analysis_success': False,
                    'error': 'Failed to clone repository'
                }
            
            # Analyze the repository
            analysis = self._analyze_repository_path(repo_path, repo_info)
            
            # Cleanup
            self._cleanup_temp_dir()
            
            return analysis
            
        except Exception as e:
            self._cleanup_temp_dir()
            return {
                'analysis_success': False,
                'error': f'Failed to clone repository: {str(e)}. This could be due to: 1) Repository not found or private, 2) Network connectivity issues, 3) GitHub rate limits, 4) Invalid repository URL format. Please check the repository URL and try again.'
            }
    
    def _parse_repo_url(self, repo_url: str) -> Optional[Dict]:
        """Parse GitHub repository URL."""
        try:
            # Handle different GitHub URL formats
            patterns = [
                r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
                r'github\.com/([^/]+)/([^/]+?)/tree/([^/]+)/([^/]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, repo_url)
                if match:
                    if len(match.groups()) == 2:
                        owner, repo = match.groups()
                        branch = 'main'
                        path = ''
                    elif len(match.groups()) == 4:
                        owner, repo, branch, path = match.groups()
                    else:
                        continue
                    
                    return {
                        'owner': owner,
                        'repo': repo.replace('.git', ''),
                        'branch': branch,
                        'path': path,
                        'url': repo_url
                    }
            
            return None
            
        except Exception:
            return None
    
    def _clone_repository(self, repo_info: Dict) -> Optional[str]:
        """Clone repository to temporary directory."""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix='ai_td_analysis_')
            
            # Use GitHub API to get repository info
            api_url = f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}"
            
            # Try without authentication first (public repos)
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 404:
                print(f"Repository not found: {repo_info['owner']}/{repo_info['repo']}")
                return None
            
            if response.status_code == 403:
                print(f"Repository access forbidden (rate limit or private): {repo_info['owner']}/{repo_info['repo']}")
                return None
            
            if response.status_code != 200:
                print(f"GitHub API error {response.status_code}: {response.text}")
                return None
            
            repo_data = response.json()
            
            # Check if repository is empty
            if repo_data.get('size', 0) == 0:
                print(f"Repository is empty: {repo_info['owner']}/{repo_info['repo']}")
                return None
            
            # Get default branch if not specified
            if not repo_info.get('branch') or repo_info['branch'] == 'main':
                repo_info['branch'] = repo_data.get('default_branch', 'main')
            
            # Try ZIP download first (faster)
            if self._try_zip_download(repo_info):
                return self._find_extracted_directory()
            
            # Fallback to git clone
            if self._try_git_clone(repo_info):
                return self._find_extracted_directory()
            
            print("Both ZIP download and git clone failed")
            return None
            
        except Exception as e:
            print(f"Error cloning repository: {e}")
            self._cleanup_temp_dir()
            return None
    
    def _try_zip_download(self, repo_info: Dict) -> bool:
        """Try to download repository as ZIP."""
        try:
            zip_url = f"https://github.com/{repo_info['owner']}/{repo_info['repo']}/archive/{repo_info['branch']}.zip"
            print(f"Downloading ZIP: {zip_url}")
            
            zip_response = requests.get(zip_url, timeout=30)
            
            if zip_response.status_code != 200:
                print(f"ZIP download failed: {zip_response.status_code}")
                return False
            
            # Save and extract ZIP
            zip_path = os.path.join(self.temp_dir, 'repo.zip')
            with open(zip_path, 'wb') as f:
                f.write(zip_response.content)
            
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            print("ZIP download successful")
            return True
            
        except Exception as e:
            print(f"ZIP download error: {e}")
            return False
    
    def _try_git_clone(self, repo_info: Dict) -> bool:
        """Try to clone repository using git."""
        try:
            import subprocess
            
            git_url = f"https://github.com/{repo_info['owner']}/{repo_info['repo']}.git"
            clone_dir = os.path.join(self.temp_dir, 'repo')
            
            print(f"Git cloning: {git_url}")
            
            # Try git clone
            result = subprocess.run([
                'git', 'clone', '--depth', '1', '--branch', repo_info['branch'], 
                git_url, clone_dir
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("Git clone successful")
                return True
            else:
                print(f"Git clone failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Git clone error: {e}")
            return False
    
    def _find_extracted_directory(self) -> Optional[str]:
        """Find the extracted repository directory."""
        try:
            # Look for extracted directory
            for item in os.listdir(self.temp_dir):
                item_path = os.path.join(self.temp_dir, item)
                if os.path.isdir(item_path) and item != '__MACOSX':
                    return item_path
            
            print("No extracted directory found")
            return None
            
        except Exception as e:
            print(f"Error finding extracted directory: {e}")
            return None
    
    def _analyze_repository_path(self, repo_path: str, repo_info: Dict) -> Dict:
        """Analyze repository at given path."""
        try:
            # Find code files
            code_files = self._find_code_files(repo_path)
            
            print(f"Found {len(code_files)} code files")
            
            if not code_files:
                return {
                    'analysis_success': False,
                    'error': 'No supported code files found. Repository may contain only documentation, configuration files, or unsupported languages.'
                }
            
            # Show supported languages found
            languages_found = set()
            for file_path in code_files:
                lang = self._detect_language(file_path)
                if lang:
                    languages_found.add(lang)
            
            print(f"Supported languages found: {', '.join(sorted(languages_found))}")
            
            # Analyze each file
            total_lines = 0
            files_analyzed = 0
            all_scores = []
            
            print(f"Analyzing {len(code_files)} files...")
            
            for file_path in tqdm(code_files, desc="Analyzing files"):
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if not content.strip():
                        continue
                    
                    # Parse file
                    language = self._detect_language(file_path)
                    if not language:
                        print(f"Warning: Could not detect language for {file_path}")
                        continue
                    
                    # Analyze with AI-TD detector
                    analysis = self.detector.analyze_code(content, language)
                    
                    if analysis:
                        all_scores.append(analysis)
                        total_lines += len(content.splitlines())
                        files_analyzed += 1
                    else:
                        print(f"Warning: Analysis failed for {file_path}")
                
                except Exception as e:
                    print(f"Error analyzing file {file_path}: {e}")
                    continue
            
            if not all_scores:
                return {
                    'analysis_success': False,
                    'error': f'Failed to analyze any files. Tried {files_analyzed} files, but none produced valid results. This may be due to parsing errors or unsupported code patterns.'
                }
            
            print(f"Successfully analyzed {files_analyzed} files with {total_lines} total lines")
            
            # Aggregate results
            aggregated_scores = self._aggregate_scores(all_scores)
            
            # Determine severity
            severity = self._determine_severity(aggregated_scores['ai_td_score'])
            
            return {
                'analysis_success': True,
                'name': f"{repo_info['owner']}/{repo_info['repo']}",
                'url': repo_info['url'],
                'language': self._get_primary_language(repo_path),
                'files_analyzed': files_analyzed,
                'total_lines': total_lines,
                'analysis_time': time.time(),
                **aggregated_scores,
                'severity': severity
            }
            
        except Exception as e:
            return {
                'analysis_success': False,
                'error': f'Analysis error: {str(e)}. This may be due to repository structure, file encoding issues, or internal analysis failures.'
            }
    
    def _find_code_files(self, repo_path: str) -> List[str]:
        """Find all supported code files in repository."""
        code_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['node_modules', 'venv', 'env', '__pycache__', 
                               'target', 'build', 'dist', '.git']]
            
            for file in files:
                file_path = os.path.join(root, file)
                language = self._detect_language(file_path)
                if language:
                    code_files.append(file_path)
        
        return code_files
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension."""
        file_ext = Path(file_path).suffix.lower()
        
        for language, extensions in self.supported_languages.items():
            if file_ext in extensions:
                return language
        
        return None
    
    def _get_primary_language(self, repo_path: str) -> str:
        """Get primary language of repository."""
        language_counts = {}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['node_modules', 'venv', 'env', '__pycache__']]
            
            for file in files:
                language = self._detect_language(os.path.join(root, file))
                if language:
                    language_counts[language] = language_counts.get(language, 0) + 1
        
        if language_counts:
            return max(language_counts, key=language_counts.get)
        
        return 'Unknown'
    
    def _aggregate_scores(self, scores: List[Dict]) -> Dict:
        """Aggregate analysis scores from multiple files."""
        if not scores:
            return {
                'ai_td_score': 0.0,
                'complexity_score': 0.0,
                'duplication_score': 0.0,
                'documentation_score': 0.0,
                'error_handling_score': 0.0
            }
        
        # Calculate weighted averages based on file size
        total_weight = sum(score.get('file_size', 1) for score in scores)
        
        aggregated = {}
        for metric in ['ai_td_score', 'complexity_score', 'duplication_score', 
                      'documentation_score', 'error_handling_score']:
            weighted_sum = sum(
                score.get(metric, 0.0) * score.get('file_size', 1) 
                for score in scores
            )
            aggregated[metric] = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        return aggregated
    
    def _determine_severity(self, ai_td_score: float) -> str:
        """Determine severity level based on AI-TD score."""
        if ai_td_score >= 0.7:
            return 'HIGH'
        elif ai_td_score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Error cleaning up temp directory: {e}")
            finally:
                self.temp_dir = None


if __name__ == "__main__":
    # Test the analyzer
    analyzer = RealRepositoryAnalyzer()
    
    # Example usage
    test_repo = "https://github.com/microsoft/vscode"
    print(f"Analyzing {test_repo}...")
    
    result = analyzer.analyze_repo_url(test_repo)
    
    if result.get('analysis_success'):
        print("Analysis successful!")
        print(f"AI-TD Score: {result.get('ai_td_score', 0):.3f}")
        print(f"Severity: {result.get('severity', 'LOW')}")
        print(f"Files analyzed: {result.get('files_analyzed', 0)}")
    else:
        print(f"Analysis failed: {result.get('error', 'Unknown error')}")
