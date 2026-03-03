#!/usr/bin/env python3
"""
AI-TD Detector Web Dashboard

Interactive web dashboard for visualizing AI-induced technical debt analysis.
Provides real-time insights, repository comparisons, and trend analysis.

Usage:
    python web-dashboard/app.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Ensure project root + engine/scripts packages are importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "engine"))

from scripts.real_repo_analyzer import RealRepositoryAnalyzer


app = Flask(__name__)
CORS(app)

# Global variables
repo_analyzer = RealRepositoryAnalyzer()
current_dataset = None
dataset_stats = None


def load_dataset(dataset_path: str = "data/merged_real_dataset.csv"):
    """Load and prepare dataset for dashboard."""
    global current_dataset, dataset_stats
    
    try:
        df = pd.read_csv(dataset_path)
        
        # Clean and prepare data
        df['ai_td_score'] = pd.to_numeric(df['ai_td_score'], errors='coerce')
        df['complexity_score'] = pd.to_numeric(df['complexity_score'], errors='coerce')
        df['duplication_score'] = pd.to_numeric(df['duplication_score'], errors='coerce')
        df['documentation_score'] = pd.to_numeric(df['documentation_score'], errors='coerce')
        df['error_handling_score'] = pd.to_numeric(df['error_handling_score'], errors='coerce')
        
        # Fill missing values
        df = df.fillna({
            'ai_td_score': 0.0,
            'complexity_score': 0.0,
            'duplication_score': 0.0,
            'documentation_score': 0.0,
            'error_handling_score': 0.0,
            'ai_confidence': 'None',
            'severity': 'LOW'
        })
        
        current_dataset = df
        
        # Calculate statistics
        ai_repos = df[df['ai_confidence'] != 'None']
        human_repos = df[df['ai_confidence'] == 'None']
        
        dataset_stats = {
            'total_repos': len(df),
            'ai_repos': len(ai_repos),
            'human_repos': len(human_repos),
            'avg_ai_score': ai_repos['ai_td_score'].mean() if len(ai_repos) > 0 else 0,
            'avg_human_score': human_repos['ai_td_score'].mean() if len(human_repos) > 0 else 0,
            'effect_size': abs(ai_repos['ai_td_score'].mean() - human_repos['ai_td_score'].mean()) if len(ai_repos) > 0 and len(human_repos) > 0 else 0,
            'languages': df['language'].value_counts().to_dict(),
            'severity_dist': df['severity'].value_counts().to_dict()
        }
        
        print(f"Dataset loaded: {len(df)} repositories")
        return True
        
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return False


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """Get dataset statistics."""
    if dataset_stats:
        return jsonify(dataset_stats)
    return jsonify({'error': 'No dataset loaded'})


@app.route('/api/repositories')
def get_repositories():
    """Get repository list with filtering."""
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'})
    
    # Get query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    sort_by = request.args.get('sort_by', 'ai_td_score')
    sort_order = request.args.get('sort_order', 'desc')
    filter_type = request.args.get('filter_type', 'all')
    language_filter = request.args.get('language', '')
    
    # Filter data
    df = current_dataset.copy()
    
    if filter_type == 'ai':
        df = df[df['ai_confidence'] != 'None']
    elif filter_type == 'human':
        df = df[df['ai_confidence'] == 'None']
    
    if language_filter:
        df = df[df['language'] == language_filter]
    
    # Sort data
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=(sort_order == 'asc'))
    
    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    paginated_df = df.iloc[start:end]
    
    # Convert to JSON
    repositories = []
    for _, row in paginated_df.iterrows():
        repo = {
            'name': row.get('name', ''),
            'url': row.get('url', ''),
            'language': row.get('language', ''),
            'stars': int(row.get('stars', 0)),
            'size_kb': int(row.get('size_kb', 0)),
            'ai_confidence': row.get('ai_confidence', 'None'),
            'ai_td_score': float(row.get('ai_td_score', 0)),
            'complexity_score': float(row.get('complexity_score', 0)),
            'duplication_score': float(row.get('duplication_score', 0)),
            'documentation_score': float(row.get('documentation_score', 0)),
            'error_handling_score': float(row.get('error_handling_score', 0)),
            'severity': row.get('severity', 'LOW'),
            'files_analyzed': int(row.get('files_analyzed', 0)),
            'total_lines': int(row.get('total_lines', 0))
        }
        repositories.append(repo)
    
    return jsonify({
        'repositories': repositories,
        'total': len(df),
        'page': page,
        'per_page': per_page,
        'pages': (len(df) + per_page - 1) // per_page
    })


@app.route('/api/charts/score-distribution')
def get_score_distribution():
    """Get AI-TD score distribution chart."""
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'})
    
    ai_repos = current_dataset[current_dataset['ai_confidence'] != 'None']
    human_repos = current_dataset[current_dataset['ai_confidence'] == 'None']
    
    # Create histogram data
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=ai_repos['ai_td_score'],
        name='AI Repositories',
        nbinsx=20,
        opacity=0.7,
        marker_color='red'
    ))
    
    fig.add_trace(go.Histogram(
        x=human_repos['ai_td_score'],
        name='Human Repositories',
        nbinsx=20,
        opacity=0.7,
        marker_color='blue'
    ))
    
    fig.update_layout(
        title='AI-TD Score Distribution',
        xaxis_title='AI-TD Score',
        yaxis_title='Number of Repositories',
        barmode='overlay',
        height=400
    )
    
    return jsonify(fig.to_json())


@app.route('/api/charts/dimension-comparison')
def get_dimension_comparison():
    """Get dimension comparison chart."""
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'})
    
    ai_repos = current_dataset[current_dataset['ai_confidence'] != 'None']
    human_repos = current_dataset[current_dataset['ai_confidence'] == 'None']
    
    dimensions = ['complexity_score', 'duplication_score', 'documentation_score', 'error_handling_score']
    dimension_names = ['Complexity', 'Duplication', 'Documentation', 'Error Handling']
    
    ai_means = [ai_repos[dim].mean() for dim in dimensions]
    human_means = [human_repos[dim].mean() for dim in dimensions]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='AI Repositories',
        x=dimension_names,
        y=ai_means,
        marker_color='red'
    ))
    
    fig.add_trace(go.Bar(
        name='Human Repositories',
        x=dimension_names,
        y=human_means,
        marker_color='blue'
    ))
    
    fig.update_layout(
        title='Technical Debt Dimensions Comparison',
        xaxis_title='Dimension',
        yaxis_title='Average Score',
        barmode='group',
        height=400
    )
    
    return jsonify(fig.to_json())


@app.route('/api/charts/language-distribution')
def get_language_distribution():
    """Get language distribution chart."""
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'})
    
    language_counts = current_dataset['language'].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=language_counts.index,
            values=language_counts.values,
            hole=0.3
        )
    ])
    
    fig.update_layout(
        title='Repository Language Distribution',
        height=400
    )
    
    return jsonify(fig.to_json())


@app.route('/api/charts/severity-distribution')
def get_severity_distribution():
    """Get severity distribution chart."""
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'})
    
    ai_repos = current_dataset[current_dataset['ai_confidence'] != 'None']
    human_repos = current_dataset[current_dataset['ai_confidence'] == 'None']
    
    severity_order = ['LOW', 'MEDIUM', 'HIGH']
    
    ai_severity = ai_repos['severity'].value_counts().reindex(severity_order, fill_value=0)
    human_severity = human_repos['severity'].value_counts().reindex(severity_order, fill_value=0)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='AI Repositories',
        x=severity_order,
        y=ai_severity.values,
        marker_color='red'
    ))
    
    fig.add_trace(go.Bar(
        name='Human Repositories',
        x=severity_order,
        y=human_severity.values,
        marker_color='blue'
    ))
    
    fig.update_layout(
        title='Severity Distribution',
        xaxis_title='Severity Level',
        yaxis_title='Number of Repositories',
        barmode='group',
        height=400
    )
    
    return jsonify(fig.to_json())


@app.route('/api/analyze', methods=['POST'])
def analyze_repository():
    """Analyze a single repository."""
    data = request.get_json()
    
    if not data or 'repo_url' not in data:
        return jsonify({'error': 'Repository URL required'})
    
    repo_url = data['repo_url']
    
    try:
        # Extract owner/repo from URL
        if 'github.com' in repo_url:
            parts = repo_url.strip('/').split('/')
            if len(parts) >= 2:
                repo_name = f"{parts[-2]}/{parts[-1]}"
            else:
                return jsonify({'error': 'Invalid GitHub URL'})
        else:
            repo_name = repo_url
        
        # Analyze repository with real AI-TD engine
        print(f"Analyzing repository: {repo_name}")

        analysis = repo_analyzer.analyze_repo_url(repo_url)
        if not analysis or not analysis.get('analysis_success'):
            return jsonify({'error': 'Analysis failed. Ensure the repository is accessible and contains supported languages.'}), 400

        result = {
            'repo_name': analysis.get('name', repo_name),
            'repo_url': analysis.get('url', repo_url),
            'ai_td_score': analysis.get('ai_td_score', 0.0),
            'complexity_score': analysis.get('complexity_score', 0.0),
            'duplication_score': analysis.get('duplication_score', 0.0),
            'documentation_score': analysis.get('documentation_score', 0.0),
            'error_handling_score': analysis.get('error_handling_score', 0.0),
            'severity': analysis.get('severity', 'LOW'),
            'files_analyzed': analysis.get('files_analyzed', 0),
            'total_lines': analysis.get('total_lines', 0),
            'analysis_time': analysis.get('analysis_time', 0.0),
        }

        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/export')
def export_data():
    """Export dataset as CSV."""
    if current_dataset is None:
        return jsonify({'error': 'No dataset loaded'})
    
    # Convert to CSV
    csv_data = current_dataset.to_csv(index=False)
    
    return jsonify({
        'csv_data': csv_data,
        'filename': f'ai_td_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    })


if __name__ == '__main__':
    # Load default dataset
    load_dataset()
    
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Get port from environment variable (for Render) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    print("Starting AI-TD Dashboard...")
    print(f"Server running on port {port}")
    
    app.run(debug=False, host='0.0.0.0', port=port)
