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
            'html': ['.html', '.htm'],  # Added HTML support
            'css': ['.css'],           # Added CSS support
        }
    
    def analyze_repo_url(self, repo_url: str) -> Dict:
        """Analyze a GitHub repository by URL using GitHub Contents API.

        Uses GitHub REST API to fetch file contents directly — no git clone or
        ZIP download needed. Works reliably on Render free tier.
        """
        start_time = time.time()

        try:
            repo_info = self._parse_repo_url(repo_url)
            if not repo_info:
                return {
                    'analysis_success': False,
                    'error': f'Invalid GitHub URL: {repo_url}. Expected: https://github.com/owner/repo'
                }

            owner = repo_info['owner']
            repo  = repo_info['repo']

            headers = {
                'User-Agent': 'AI-TD-Detector/1.0.0',
                'Accept': 'application/vnd.github.v3+json',
            }
            # Use token if available (raises rate limit from 60 → 5000/hr)
            token = os.environ.get('GITHUB_TOKEN', '')
            if token:
                headers['Authorization'] = f'token {token}'

            # ── 1. Fetch repo metadata ──────────────────────────────────────
            meta_resp = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers=headers, timeout=10
            )
            if meta_resp.status_code == 404:
                return {'analysis_success': False, 'error': f'Repository {owner}/{repo} not found or is private.'}
            if meta_resp.status_code == 403:
                return {'analysis_success': False, 'error': 'GitHub API rate limit exceeded. Please try again later.'}
            if meta_resp.status_code != 200:
                return {'analysis_success': False, 'error': f'GitHub API error {meta_resp.status_code}.'}

            meta = meta_resp.json()
            default_branch = meta.get('default_branch', 'main')
            stars  = meta.get('stargazers_count', 0)
            forks  = meta.get('forks_count', 0)
            primary_lang = (meta.get('language') or 'unknown').lower()

            # ── 2. Fetch full file tree (recursive) ─────────────────────────
            tree_resp = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1',
                headers=headers, timeout=15
            )
            if tree_resp.status_code != 200:
                return {'analysis_success': False, 'error': f'Could not fetch file tree (status {tree_resp.status_code}).'}

            tree_data = tree_resp.json()
            if tree_data.get('truncated'):
                print('Warning: file tree truncated (large repo) — analysing first 200 files only')

            # ── 3. Filter to supported source files (skip tests/vendor/node_modules) ──
            SKIP_DIRS = {
                'node_modules', 'venv', 'env', '__pycache__', '.git',
                'build', 'dist', 'target', 'vendor', '.github',
            }
            SUPPORTED_EXTS = {
                '.py': 'python', '.js': 'javascript',
                '.ts': 'typescript', '.tsx': 'typescript',
            }
            MAX_FILES = 40   # Analyse up to 40 files per repo to stay fast
            MAX_FILE_BYTES = 100_000  # Skip very large files

            candidate_files = []
            for item in tree_data.get('tree', []):
                if item.get('type') != 'blob':
                    continue
                path = item.get('path', '')
                parts = path.split('/')
                # Skip hidden / vendor directories
                if any(p.startswith('.') or p in SKIP_DIRS for p in parts[:-1]):
                    continue
                ext = Path(path).suffix.lower()
                if ext in SUPPORTED_EXTS:
                    candidate_files.append({
                        'path': path,
                        'language': SUPPORTED_EXTS[ext],
                        'size': item.get('size', 0),
                        'sha': item.get('sha', ''),
                    })

            if not candidate_files:
                return {
                    'analysis_success': False,
                    'error': 'No supported source files found (Python/JS/TS). Repository may use an unsupported language.'
                }

            # Prioritise smaller files so we can analyse more diversity quickly
            candidate_files.sort(key=lambda f: f['size'])
            selected_files = candidate_files[:MAX_FILES]

            # ── 4. Fetch & analyse each file ────────────────────────────────
            all_scores: List[Dict] = []
            total_lines = 0
            files_analyzed = 0

            for file_info in selected_files:
                if file_info['size'] > MAX_FILE_BYTES:
                    continue
                try:
                    content_resp = requests.get(
                        f"https://api.github.com/repos/{owner}/{repo}/contents/{file_info['path']}",
                        headers=headers, timeout=10
                    )
                    if content_resp.status_code != 200:
                        continue

                    content_data = content_resp.json()
                    import base64
                    raw = base64.b64decode(content_data.get('content', '')).decode('utf-8', errors='ignore')

                    if not raw.strip():
                        continue

                    analysis = self.detector.analyze_code(raw, file_info['language'])
                    if analysis:
                        analysis['file_size'] = len(raw)
                        all_scores.append(analysis)
                        total_lines += len(raw.splitlines())
                        files_analyzed += 1

                except Exception as e:
                    print(f"Error fetching/analysing {file_info['path']}: {e}")
                    continue

            if not all_scores:
                return {
                    'analysis_success': False,
                    'error': 'Files were found but none could be analysed. They may be empty or use unsupported syntax.'
                }

            # ── 5. Aggregate & return ───────────────────────────────────────
            aggregated = self._aggregate_scores(all_scores)
            severity   = self._determine_severity(aggregated['ai_td_score'])

            return {
                'analysis_success': True,
                'name': f'{owner}/{repo}',
                'url': f'https://github.com/{owner}/{repo}',
                'language': primary_lang,
                'stars': stars,
                'forks': forks,
                'files_analyzed': files_analyzed,
                'total_lines': total_lines,
                'severity': severity,
                'analysis_method': 'github_api_contents',
                'analysis_time': time.time() - start_time,
                **aggregated,
            }

        except Exception as e:
            return {
                'analysis_success': False,
                'error': f'Unexpected error: {str(e)}'
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
        """Clone repository to temporary directory.

        NOTE: This helper is kept for backward compatibility but `analyze_repo_url`
        now orchestrates ZIP/clone directly after creating `temp_dir`.
        """
        try:
            # Ensure temporary directory exists
            if not self.temp_dir:
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
            
            # Try git clone with shorter timeout for Render
            result = subprocess.run([
                'git', 'clone', '--depth', '1', '--branch', repo_info['branch'], 
                git_url, clone_dir
            ], capture_output=True, text=True, timeout=30)  # Reduced from 60 to 30
            
            if result.returncode == 0:
                print("Git clone successful")
                return True
            else:
                print(f"Git clone failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("Git clone timeout (30s) - trying GitHub API fallback")
            return False
        except Exception as e:
            print(f"Git clone error: {e}")
            return False
    
    def _try_github_api_fallback(self, repo_info: Dict) -> bool:
        """Try to get basic repository info via GitHub API."""
        try:
            import requests
            
            api_url = f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}"
            print(f"GitHub API fallback: {api_url}")
            
            # Add User-Agent header to avoid rate limiting
            headers = {
                'User-Agent': 'AI-TD-Detector/1.0.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(api_url, timeout=10, headers=headers)
            
            if response.status_code == 200:
                repo_data = response.json()
                
                # Create minimal analysis from API data
                self._create_minimal_analysis(repo_data, repo_info)
                return True
            elif response.status_code == 403:
                # Rate limited
                print(f"GitHub API rate limited. Waiting and retrying...")
                import time
                time.sleep(2)  # Wait 2 seconds
                
                # Retry once
                response = requests.get(api_url, timeout=10, headers=headers)
                if response.status_code == 200:
                    repo_data = response.json()
                    self._create_minimal_analysis(repo_data, repo_info)
                    return True
                else:
                    print(f"GitHub API retry failed: {response.status_code}")
                    return False
            else:
                print(f"GitHub API failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"GitHub API fallback error: {e}")
            return False
    
    def _create_minimal_analysis(self, repo_data: Dict, repo_info: Dict):
        """Create minimal analysis from GitHub API data."""
        try:
            # Create a simple analysis based on repository metadata
            language = repo_data.get('language', 'Unknown').lower()
            stars = repo_data.get('stargazers_count', 0)
            forks = repo_data.get('forks_count', 0)
            size = repo_data.get('size', 0)
            
            # Estimate AI-TD score based on repository characteristics
            # This is a simplified scoring for when we can't analyze code
            base_score = 0.3
            
            # Adjust based on repository size (larger repos might have more complexity)
            if size > 10000:  # Large repository
                base_score += 0.2
            elif size > 1000:
                base_score += 0.1
            
            # Adjust based on popularity (popular repos might be better maintained)
            if stars > 10000:
                base_score -= 0.1  # Popular repos likely have better code quality
            elif stars > 1000:
                base_score -= 0.05
            
            # Ensure score is within bounds
            ai_td_score = max(0.0, min(1.0, base_score))
            
            # Create minimal result
            self.minimal_result = {
                'analysis_success': True,
                'name': f"{repo_info['owner']}/{repo_info['repo']}",
                'url': f"https://github.com/{repo_info['owner']}/{repo_info['repo']}",
                'language': language,
                'ai_td_score': ai_td_score,
                'complexity_score': ai_td_score * 0.7,
                'duplication_score': ai_td_score * 0.3,
                'documentation_score': max(0.2, 1.0 - ai_td_score * 0.5),
                'error_handling_score': ai_td_score * 0.6,
                'stars': stars,
                'forks': forks,
                'files_analyzed': 0,
                'total_lines': 0,
                'severity': 'HIGH' if ai_td_score > 0.6 else 'MEDIUM' if ai_td_score > 0.3 else 'LOW',
                'analysis_method': 'github_api_fallback'
            }
            
            print(f"Created minimal analysis with AI-TD score: {ai_td_score}")
            
        except Exception as e:
            print(f"Error creating minimal analysis: {e}")
            self.minimal_result = None
    
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
