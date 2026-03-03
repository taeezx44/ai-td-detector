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


def load_dataset(dataset_path: str = "data/merged_real_dataset.csv") -> bool:
    """Load and prepare dataset for dashboard.

    Returns True if a dataset was successfully loaded/prepared, otherwise False.
    """
    global current_dataset, dataset_stats

    # Try different dataset paths
    dataset_paths = [
        dataset_path,
        "data/merged_dataset.csv",
        "data/sample_research_dataset.csv",
    ]

    df = None
    loaded_path = None

    for path in dataset_paths:
        try:
            df = pd.read_csv(path)
            loaded_path = path
            print(f"Successfully loaded dataset: {path}")
            break
        except FileNotFoundError:
            print(f"Dataset not found: {path}")
            continue
        except Exception as e:
            print(f"Error loading dataset {path}: {e}")
            continue

    if df is None:
        print("No dataset found, creating sample data...")
        # Create sample data for demo so the dashboard is never empty
        df = pd.DataFrame(
            {
                "name": [
                    "Sample AI Repo 1",
                    "Sample AI Repo 2",
                    "Sample Human Repo 1",
                    "Sample Human Repo 2",
                ],
                "url": [
                    "https://github.com/sample/ai1",
                    "https://github.com/sample/ai2",
                    "https://github.com/sample/human1",
                    "https://github.com/sample/human2",
                ],
                "language": ["python", "javascript", "python", "javascript"],
                "ai_td_score": [0.67, 0.54, 0.35, 0.28],
                "complexity_score": [0.45, 0.38, 0.25, 0.20],
                "duplication_score": [0.23, 0.18, 0.12, 0.08],
                "documentation_score": [0.67, 0.72, 0.45, 0.38],
                "error_handling_score": [0.34, 0.28, 0.19, 0.15],
                "stars": [150, 89, 234, 167],
                "forks": [23, 12, 45, 28],
                "type": ["AI", "AI", "Human", "Human"],
            }
        )
        loaded_path = "sample_data"

    try:
        # Clean and prepare data
        df["ai_td_score"] = pd.to_numeric(df["ai_td_score"], errors="coerce")
        df["complexity_score"] = pd.to_numeric(df["complexity_score"], errors="coerce")
        df["duplication_score"] = pd.to_numeric(df["duplication_score"], errors="coerce")
        df["documentation_score"] = pd.to_numeric(
            df["documentation_score"], errors="coerce"
        )
        df["error_handling_score"] = pd.to_numeric(
            df["error_handling_score"], errors="coerce"
        )

        # Backfill ai_confidence from type if needed
        if "ai_confidence" not in df.columns:
            if "type" in df.columns:
                df["ai_confidence"] = df["type"].apply(
                    lambda t: "None" if str(t).lower() == "human" else "High"
                )
            else:
                df["ai_confidence"] = "None"

        # Ensure history-related columns exist for all rows
        if "source" not in df.columns:
            # Mark existing rows as coming from the static dataset
            df["source"] = "static"
        if "analysis_method" not in df.columns:
            df["analysis_method"] = "dataset"
        if "created_at" not in df.columns:
            df["created_at"] = ""

        # Fill missing values
        df = df.fillna(
            {
                "ai_td_score": 0.0,
                "complexity_score": 0.0,
                "duplication_score": 0.0,
                "documentation_score": 0.0,
                "error_handling_score": 0.0,
                "ai_confidence": "None",
                "severity": "LOW",
            }
        )

        current_dataset = df

        # Split into AI vs human repos
        ai_repos = df[df["ai_confidence"] != "None"]
        human_repos = df[df["ai_confidence"] == "None"]

        # Compute basic statistics
        avg_ai = ai_repos["ai_td_score"].mean() if len(ai_repos) > 0 else 0.0
        avg_human = (
            human_repos["ai_td_score"].mean() if len(human_repos) > 0 else 0.0
        )

        # Cohen's d style effect size (simple pooled std)
        effect_size = 0.0
        if len(ai_repos) > 1 and len(human_repos) > 1:
            ai_scores = ai_repos["ai_td_score"]
            human_scores = human_repos["ai_td_score"]
            pooled_var = (
                (ai_scores.var(ddof=1) + human_scores.var(ddof=1)) / 2.0
            )
            if pooled_var > 0:
                effect_size = (avg_ai - avg_human) / (pooled_var ** 0.5)

        # Language distribution
        languages = df["language"].value_counts().to_dict() if "language" in df.columns else {}

        dataset_stats = {
            "total_repos": len(df),
            "ai_repos": len(ai_repos),
            "human_repos": len(human_repos),
            "avg_ai_score": float(avg_ai),
            "avg_human_score": float(avg_human),
            "effect_size": float(effect_size),
            "languages": languages,
            "loaded_path": loaded_path,
        }

        print(f"Dataset loaded successfully: {len(df)} repositories")
        print(f"AI repos: {len(ai_repos)}, Human repos: {len(human_repos)}")
        return True

    except Exception as e:
        print(f"Error processing dataset: {e}")
        # Create minimal dataset as fallback
        current_dataset = pd.DataFrame(
            {
                "name": ["Demo Repo"],
                "url": ["https://github.com/demo/repo"],
                "language": ["python"],
                "ai_td_score": [0.5],
                "complexity_score": [0.3],
                "duplication_score": [0.2],
                "documentation_score": [0.4],
                "error_handling_score": [0.3],
                "stars": [100],
                "forks": [10],
                "type": ["AI"],
                "ai_confidence": ["High"],
                "severity": ["MEDIUM"],
            }
        )

        dataset_stats = {
            "total_repos": 1,
            "ai_repos": 1,
            "human_repos": 0,
            "avg_ai_score": 0.5,
            "avg_human_score": 0.0,
            "effect_size": 0.0,
            "languages": {"python": 1},
            "loaded_path": "fallback",
        }
        return False


# Ensure a dataset is loaded even when the app is started by a WSGI server
load_dataset()


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/history')
def history_page():
    """History page showing repositories analyzed via Quick Analysis."""
    return render_template('history.html')


@app.route('/api/stats')
def get_stats():
    """Get dataset statistics."""
    global dataset_stats

    if not dataset_stats:
        # Try to (re)load if nothing is available yet
        load_dataset()

    if dataset_stats:
        return jsonify(dataset_stats)
    return jsonify({'error': 'No dataset loaded'})


@app.route('/api/repositories')
def get_repositories():
    """Get repository list with filtering."""
    global current_dataset

    if current_dataset is None:
        load_dataset()
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
    
    # Convert to JSON with defensive casting (handle NaN/missing values)
    repositories = []
    for _, row in paginated_df.iterrows():
        def safe_int(value, default=0):
            try:
                if pd.isna(value):
                    return default
                return int(value)
            except Exception:
                return default

        def safe_float(value, default=0.0):
            try:
                if pd.isna(value):
                    return default
                return float(value)
            except Exception:
                return default

        repo = {
            'name': row.get('name', '') or '',
            'url': row.get('url', '') or '',
            'language': row.get('language', '') or '',
            'stars': safe_int(row.get('stars', 0)),
            'forks': safe_int(row.get('forks', 0)),
            'size_kb': safe_int(row.get('size_kb', 0)),
            'ai_confidence': row.get('ai_confidence', 'None') or 'None',
            'ai_td_score': safe_float(row.get('ai_td_score', 0.0)),
            'complexity_score': safe_float(row.get('complexity_score', 0.0)),
            'duplication_score': safe_float(row.get('duplication_score', 0.0)),
            'documentation_score': safe_float(row.get('documentation_score', 0.0)),
            'error_handling_score': safe_float(row.get('error_handling_score', 0.0)),
            'severity': row.get('severity', 'LOW') or 'LOW',
            'files_analyzed': safe_int(row.get('files_analyzed', 0)),
            'total_lines': safe_int(row.get('total_lines', 0)),
        }
        repositories.append(repo)
    
    return jsonify({
        'repositories': repositories,
        'total': len(df),
        'page': page,
        'per_page': per_page,
        'pages': (len(df) + per_page - 1) // per_page
    })


@app.route('/api/history')
def get_history():
    """Get history of repositories analyzed via Quick Analysis."""
    global current_dataset

    if current_dataset is None:
        load_dataset()
        if current_dataset is None:
            return jsonify({'error': 'No dataset loaded'})

    # Get query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    severity_filter = request.args.get('severity', '').upper()
    query = request.args.get('q', '').strip()

    df = current_dataset.copy()

    # Keep only rows that came from Quick Analysis (runtime analysis)
    if 'source' in df.columns:
        df = df[df['source'] == 'quick_analysis']
    elif 'analysis_method' in df.columns:
        df = df[df['analysis_method'] != 'dataset']

    # Optional severity filter
    if severity_filter in ('LOW', 'MEDIUM', 'HIGH'):
        if 'severity' in df.columns:
            df = df[df['severity'].str.upper() == severity_filter]

    # Optional text search (name/url)
    if query:
        q = query.lower()
        name_series = df['name'].astype(str).str.lower() if 'name' in df.columns else ''
        url_series = df['url'].astype(str).str.lower() if 'url' in df.columns else ''
        mask = name_series.str.contains(q, na=False) | url_series.str.contains(q, na=False)
        df = df[mask]

    # Sort newest first if we have timestamps
    if 'created_at' in df.columns:
        df = df.sort_values('created_at', ascending=False)

    # Paginate
    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_df = df.iloc[start:end]

    history_items = []
    for _, row in paginated_df.iterrows():
        def safe_float(value, default=0.0):
            try:
                if pd.isna(value):
                    return default
                return float(value)
            except Exception:
                return default

        history_items.append({
            'name': row.get('name', '') or '',
            'url': row.get('url', '') or '',
            'language': row.get('language', '') or '',
            'ai_td_score': safe_float(row.get('ai_td_score', 0.0)),
            'complexity_score': safe_float(row.get('complexity_score', 0.0)),
            'duplication_score': safe_float(row.get('duplication_score', 0.0)),
            'documentation_score': safe_float(row.get('documentation_score', 0.0)),
            'error_handling_score': safe_float(row.get('error_handling_score', 0.0)),
            'severity': row.get('severity', 'LOW') or 'LOW',
            'analysis_method': row.get('analysis_method', '') or '',
            'created_at': row.get('created_at', '') or '',
            'files_analyzed': int(row.get('files_analyzed', 0) or 0),
            'total_lines': int(row.get('total_lines', 0) or 0),
        })

    return jsonify({
        'history': history_items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    })


@app.route('/api/history/export')
def export_history():
    """Export Quick Analysis history as CSV."""
    global current_dataset

    if current_dataset is None:
        load_dataset()
        if current_dataset is None:
            return jsonify({'error': 'No dataset loaded'})

    df = current_dataset.copy()

    # Keep only Quick Analysis entries
    if 'source' in df.columns:
        df = df[df['source'] == 'quick_analysis']
    elif 'analysis_method' in df.columns:
        df = df[df['analysis_method'] != 'dataset']

    if df.empty:
        return jsonify({'error': 'No history entries to export'})

    # Select and order relevant columns for CSV export
    columns = [
        'name',
        'url',
        'language',
        'ai_td_score',
        'complexity_score',
        'duplication_score',
        'documentation_score',
        'error_handling_score',
        'severity',
        'files_analyzed',
        'total_lines',
        'analysis_method',
        'created_at',
    ]

    existing_cols = [c for c in columns if c in df.columns]
    export_df = df[existing_cols]

    csv_data = export_df.to_csv(index=False)

    return jsonify({
        'csv_data': csv_data,
        'filename': f'ai_td_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
    })


@app.route('/api/charts/score-distribution')
def get_score_distribution():
    """Get AI-TD score distribution chart."""
    if current_dataset is None:
        load_dataset()
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
        load_dataset()
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
        load_dataset()
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
        load_dataset()
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
    """Analyze a single repository and (optionally) append it to the dashboard dataset."""
    global current_dataset, dataset_stats
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
            error_msg = analysis.get('error', 'Unknown error occurred during analysis')
            return jsonify({'error': f'Analysis failed: {error_msg}'}), 400

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

        # --- Update in-memory dataset so stats/charts/table reflect this analysis ---
        try:
            # Ensure we have a DataFrame to append to
            if current_dataset is None:
                current_dataset = pd.DataFrame()

            # Build a row compatible with the main dataset schema
            new_row = {
                "name": result["repo_name"],
                "url": result["repo_url"],
                "language": analysis.get("language", ""),
                "ai_td_score": result["ai_td_score"],
                "complexity_score": result["complexity_score"],
                "duplication_score": result["duplication_score"],
                "documentation_score": result["documentation_score"],
                "error_handling_score": result["error_handling_score"],
                "stars": analysis.get("stars", 0),
                "forks": analysis.get("forks", 0),
                # Treat analyzed repo as AI-assisted so it appears in AI stats
                "ai_confidence": analysis.get("ai_confidence", "High"),
                "severity": result["severity"],
                "files_analyzed": result["files_analyzed"],
                "total_lines": result["total_lines"],
                # History / origin metadata
                "type": analysis.get("type", "AI"),
                "analysis_method": analysis.get("analysis_method", "quick_analysis"),
                "source": "quick_analysis",
                "created_at": datetime.utcnow().isoformat(timespec="seconds"),
            }

            # Append to dataset
            current_dataset = pd.concat(
                [current_dataset, pd.DataFrame([new_row])],
                ignore_index=True,
            )

            # Recalculate summary statistics for /api/stats
            ai_repos = current_dataset[current_dataset['ai_confidence'] != 'None']
            human_repos = current_dataset[current_dataset['ai_confidence'] == 'None']

            avg_ai = ai_repos['ai_td_score'].mean() if len(ai_repos) > 0 else 0.0
            avg_human = (
                human_repos['ai_td_score'].mean() if len(human_repos) > 0 else 0.0
            )

            effect_size = 0.0
            if len(ai_repos) > 1 and len(human_repos) > 1:
                ai_scores = ai_repos['ai_td_score']
                human_scores = human_repos['ai_td_score']
                pooled_var = (
                    (ai_scores.var(ddof=1) + human_scores.var(ddof=1)) / 2.0
                )
                if pooled_var > 0:
                    effect_size = (avg_ai - avg_human) / (pooled_var ** 0.5)

            languages = (
                current_dataset['language'].value_counts().to_dict()
                if 'language' in current_dataset.columns
                else {}
            )

            dataset_stats = {
                'total_repos': len(current_dataset),
                'ai_repos': len(ai_repos),
                'human_repos': len(human_repos),
                'avg_ai_score': float(avg_ai),
                'avg_human_score': float(avg_human),
                'effect_size': float(effect_size),
                'languages': languages,
                'loaded_path': dataset_stats['loaded_path'] if dataset_stats else 'runtime',
            }

            # Best-effort persist to CSV so that data can be reused if the server restarts
            try:
                data_dir = PROJECT_ROOT / 'data'
                data_dir.mkdir(exist_ok=True)
                (data_dir / 'merged_real_dataset.csv').write_text(
                    current_dataset.to_csv(index=False),
                    encoding='utf-8',
                )
            except Exception as persist_err:
                print(f"Warning: failed to persist updated dataset: {persist_err}")

        except Exception as update_err:
            # Do not fail the analysis just because dataset update failed
            print(f"Warning: failed to update in-memory dataset after analysis: {update_err}")

        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/export')
def export_data():
    """Export dataset as CSV."""
    if current_dataset is None:
        load_dataset()
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
