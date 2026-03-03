#!/usr/bin/env python3
"""
Dataset Management Pipeline for AI-TD Research

Manages, filters, merges, and validates repository datasets for the research.
Implements quality filters and prepares balanced AI vs Human datasets.

Usage:
    python scripts/dataset_manager.py --merge data/*.csv --output data/merged_dataset.csv
    python scripts/dataset_manager.py --filter data/merged_dataset.csv --output data/filtered_dataset.csv
    python scripts/dataset_manager.py --validate data/filtered_dataset.csv
    python scripts/dataset_manager.py --balance data/filtered_dataset.csv --output data/balanced_dataset.csv
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np


class DatasetManager:
    """Manages AI-TD research datasets."""
    
    def __init__(self):
        self.min_size_kb = 5000  # 5,000 lines minimum
        self.max_size_kb = 50000  # 50,000 lines maximum
        self.target_languages = ['Python', 'JavaScript', 'TypeScript', 'Jupyter Notebook']
        self.min_age_days = 365  # 1 year minimum
        self.target_total = 40  # Target dataset size
        self.ai_ratio = 0.5  # 50% AI repositories
    
    def merge_datasets(self, file_paths: List[str], output_path: str) -> pd.DataFrame:
        """
        Merge multiple CSV datasets into one.
        
        Args:
            file_paths: List of CSV file paths to merge
            output_path: Output CSV file path
            
        Returns:
            Merged DataFrame
        """
        print(f"Merging {len(file_paths)} datasets...")
        
        dfs = []
        for file_path in file_paths:
            if Path(file_path).exists():
                df = pd.read_csv(file_path)
                print(f"  Loaded {len(df)} repos from {file_path}")
                dfs.append(df)
            else:
                print(f"  Warning: {file_path} not found")
        
        if not dfs:
            print("No datasets to merge!")
            return pd.DataFrame()
        
        # Concatenate all DataFrames
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates based on repository URL
        original_count = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset=['url'], keep='first')
        duplicates_removed = original_count - len(merged_df)
        
        print(f"Merged dataset: {len(merged_df)} unique repositories")
        print(f"Removed {duplicates_removed} duplicates")
        
        # Save merged dataset
        merged_df.to_csv(output_path, index=False)
        print(f"Saved to {output_path}")
        
        return merged_df
    
    def filter_dataset(self, df: pd.DataFrame, output_path: str) -> pd.DataFrame:
        """
        Apply quality filters to dataset.
        
        Args:
            df: Input DataFrame
            output_path: Output CSV file path
            
        Returns:
            Filtered DataFrame
        """
        print(f"Filtering dataset with {len(df)} repositories...")
        
        original_count = len(df)
        
        # Convert size_kb to numeric
        df['size_kb'] = pd.to_numeric(df['size_kb'], errors='coerce')
        
        # Filter 1: Size constraints (5K-50K lines)
        size_filter = (df['size_kb'] >= self.min_size_kb) & (df['size_kb'] <= self.max_size_kb)
        df = df[size_filter]
        print(f"  Size filter (5K-50K lines): {len(df)} remaining")
        
        # Filter 2: Language constraints
        if 'language' in df.columns:
            lang_filter = df['language'].isin(self.target_languages)
            df = df[lang_filter]
            print(f"  Language filter (Python/JS/TS): {len(df)} remaining")
        
        # Filter 3: Age constraints (at least 1 year old)
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.tz_localize(None)
            age_filter = (pd.Timestamp.now(tz='UTC').tz_localize(None) - df['created_at']).dt.days >= self.min_age_days
            df = df[age_filter]
            print(f"  Age filter (≥1 year): {len(df)} remaining")
        
        # Filter 4: Remove private repositories
        if 'is_private' in df.columns:
            df = df[~df['is_private'].astype(bool)]
            print(f"  Remove private repos: {len(df)} remaining")
        
        # Filter 5: Basic quality checks
        if 'stars' in df.columns:
            df['stars'] = pd.to_numeric(df['stars'], errors='coerce').fillna(0)
            # Remove repos with 0 stars (likely inactive/abandoned)
            df = df[df['stars'] > 0]
            print(f"  Quality filter (≥1 star): {len(df)} remaining")
        
        filtered_count = len(df)
        print(f"Filtered dataset: {filtered_count} repositories")
        print(f"Removed {original_count - filtered_count} repositories")
        
        # Save filtered dataset
        df.to_csv(output_path, index=False)
        print(f"Saved to {output_path}")
        
        return df
    
    def balance_dataset(self, df: pd.DataFrame, output_path: str) -> pd.DataFrame:
        """
        Balance dataset between AI and Human repositories.
        
        Args:
            df: Input DataFrame
            output_path: Output CSV file path
            
        Returns:
            Balanced DataFrame
        """
        print(f"Balancing dataset with {len(df)} repositories...")
        
        # Classify repositories
        ai_repos = df[df['ai_confidence'].isin(['High', 'Medium'])]
        human_repos = df[df['ai_confidence'].isin(['Low', 'None'])]
        
        print(f"  AI repositories: {len(ai_repos)}")
        print(f"  Human repositories: {len(human_repos)}")
        
        # Target counts
        target_ai = int(self.target_total * self.ai_ratio)
        target_human = self.target_total - target_ai
        
        print(f"  Target AI repos: {target_ai}")
        print(f"  Target Human repos: {target_human}")
        
        # Sample repositories
        balanced_repos = []
        
        # Sample AI repositories
        if len(ai_repos) >= target_ai:
            # Prioritize High confidence repos
            high_conf_ai = ai_repos[ai_repos['ai_confidence'] == 'High']
            medium_conf_ai = ai_repos[ai_repos['ai_confidence'] == 'Medium']
            
            ai_sample = []
            
            # Take all High confidence if available
            if len(high_conf_ai) > 0:
                high_sample = high_conf_ai.sample(min(len(high_conf_ai), target_ai), random_state=42)
                ai_sample.append(high_sample)
                remaining_ai = target_ai - len(high_sample)
            else:
                remaining_ai = target_ai
            
            # Fill remaining with Medium confidence
            if remaining_ai > 0 and len(medium_conf_ai) > 0:
                medium_sample = medium_conf_ai.sample(min(len(medium_conf_ai), remaining_ai), random_state=42)
                ai_sample.append(medium_sample)
            
            if ai_sample:
                ai_final = pd.concat(ai_sample, ignore_index=True)
                balanced_repos.append(ai_final)
        else:
            print(f"  Warning: Only {len(ai_repos)} AI repos available (need {target_ai})")
            balanced_repos.append(ai_repos)
        
        # Sample Human repositories
        if len(human_repos) >= target_human:
            # Stratified sampling by language to ensure diversity
            human_sample = human_repos.groupby('language', group_keys=False).apply(
                lambda x: x.sample(min(len(x), max(1, target_human // len(human_repos['language'].unique()))), random_state=42)
            )
            
            # If still need more, sample randomly
            if len(human_sample) < target_human:
                additional = human_repos[~human_repos.index.isin(human_sample.index)]
                if len(additional) > 0:
                    additional_sample = additional.sample(target_human - len(human_sample), random_state=42)
                    human_sample = pd.concat([human_sample, additional_sample], ignore_index=True)
            
            balanced_repos.append(human_sample.head(target_human))
        else:
            print(f"  Warning: Only {len(human_repos)} Human repos available (need {target_human})")
            balanced_repos.append(human_repos)
        
        # Combine balanced datasets
        if balanced_repos:
            balanced_df = pd.concat(balanced_repos, ignore_index=True)
        else:
            balanced_df = pd.DataFrame()
        
        print(f"Balanced dataset: {len(balanced_df)} repositories")
        
        # Save balanced dataset
        balanced_df.to_csv(output_path, index=False)
        print(f"Saved to {output_path}")
        
        return balanced_df
    
    def validate_dataset(self, df: pd.DataFrame) -> Dict:
        """
        Validate dataset quality and compute statistics.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Validation report
        """
        print("Validating dataset...")
        
        report = {
            'total_repos': len(df),
            'ai_repos': 0,
            'human_repos': 0,
            'language_distribution': {},
            'size_distribution': {},
            'age_distribution': {},
            'confidence_distribution': {},
            'quality_metrics': {}
        }
        
        if df.empty:
            print("Dataset is empty!")
            return report
        
        # AI vs Human classification
        ai_repos = df[df['ai_confidence'].isin(['High', 'Medium'])]
        human_repos = df[df['ai_confidence'].isin(['Low', 'None'])]
        
        report['ai_repos'] = len(ai_repos)
        report['human_repos'] = len(human_repos)
        
        # Language distribution
        if 'language' in df.columns:
            report['language_distribution'] = df['language'].value_counts().to_dict()
        
        # Size distribution
        if 'size_kb' in df.columns:
            df['size_kb'] = pd.to_numeric(df['size_kb'], errors='coerce')
            size_stats = {
                'mean': df['size_kb'].mean(),
                'median': df['size_kb'].median(),
                'min': df['size_kb'].min(),
                'max': df['size_kb'].max(),
                'std': df['size_kb'].std()
            }
            report['size_distribution'] = size_stats
        
        # Age distribution
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.tz_localize(None)
            ages_days = (pd.Timestamp.now(tz='UTC').tz_localize(None) - df['created_at']).dt.days
            age_stats = {
                'mean_days': ages_days.mean(),
                'median_days': ages_days.median(),
                'min_days': ages_days.min(),
                'max_days': ages_days.max()
            }
            report['age_distribution'] = age_stats
        
        # Confidence distribution
        if 'ai_confidence' in df.columns:
            report['confidence_distribution'] = df['ai_confidence'].value_counts().to_dict()
        
        # Quality metrics
        report['quality_metrics'] = {
            'has_stars': (df['stars'] > 0).sum() if 'stars' in df.columns else 0,
            'has_description': df['description'].notna().sum() if 'description' in df.columns else 0,
            'avg_stars': df['stars'].mean() if 'stars' in df.columns else 0,
            'avg_forks': df['forks'].mean() if 'forks' in df.columns else 0
        }
        
        # Print validation report
        print("\n" + "="*60)
        print("Dataset Validation Report")
        print("="*60)
        print(f"Total repositories: {report['total_repos']}")
        print(f"AI repositories: {report['ai_repos']} ({report['ai_repos']/report['total_repos']*100:.1f}%)")
        print(f"Human repositories: {report['human_repos']} ({report['human_repos']/report['total_repos']*100:.1f}%)")
        
        if report['language_distribution']:
            print(f"\nLanguage distribution:")
            for lang, count in report['language_distribution'].items():
                print(f"  {lang}: {count}")
        
        if report['confidence_distribution']:
            print(f"\nAI confidence distribution:")
            for conf, count in report['confidence_distribution'].items():
                print(f"  {conf}: {count}")
        
        if report['size_distribution']:
            size_dist = report['size_distribution']
            print(f"\nSize distribution (KB):")
            print(f"  Mean: {size_dist['mean']:.0f}")
            print(f"  Median: {size_dist['median']:.0f}")
            print(f"  Range: {size_dist['min']:.0f} - {size_dist['max']:.0f}")
        
        if report['age_distribution']:
            age_dist = report['age_distribution']
            print(f"\nAge distribution (days):")
            print(f"  Mean: {age_dist['mean_days']:.0f}")
            print(f"  Median: {age_dist['median_days']:.0f}")
            print(f"  Range: {age_dist['min_days']:.0f} - {age_dist['max_days']:.0f}")
        
        print("="*60)
        
        return report
    
    def create_analysis_plan(self, df: pd.DataFrame, output_path: str):
        """
        Create analysis plan for the dataset.
        
        Args:
            df: Input DataFrame
            output_path: Output JSON file path
        """
        print("Creating analysis plan...")
        
        plan = {
            'dataset_info': {
                'total_repos': len(df),
                'ai_repos': len(df[df['ai_confidence'].isin(['High', 'Medium'])]),
                'human_repos': len(df[df['ai_confidence'].isin(['Low', 'None'])]),
                'languages': df['language'].unique().tolist() if 'language' in df.columns else []
            },
            'research_questions': {
                'rq1': {
                    'question': 'Do AI-generated code segments exhibit higher technical debt than human-written code?',
                    'test': 'Wilcoxon Signed-Rank Test',
                    'hypothesis': 'AI repos will have higher AI-TD scores than Human repos',
                    'alpha': 0.05,
                    'power_analysis': {
                        'effect_size_expected': 0.5,
                        'power_target': 0.8,
                        'sample_size_adequate': len(df) >= 34
                    }
                },
                'rq2': {
                    'question': 'Which dimensions of technical debt are most strongly associated with AI-assisted code generation?',
                    'test': 'Mann-Whitney U + Feature Importance',
                    'dimensions': ['complexity', 'duplication', 'documentation', 'error_handling'],
                    'method': 'Per-dimension analysis + Random Forest feature ranking'
                },
                'rq3': {
                    'question': 'Is there a preliminary association between AI-TD Score and short-term maintainability indicators?',
                    'test': 'Spearman correlation',
                    'indicators': ['GitHub Issues', 'Code Churn'],
                    'status': 'Exploratory - depends on time availability'
                }
            },
            'next_steps': [
                '1. Run AI-TD analysis on all repositories using engine/main.py',
                '2. Extract per-dimension scores for statistical analysis',
                '3. Run statistical tests using scripts/statistical_analysis.py',
                '4. Perform manual verification on 10% sample',
                '5. Calculate inter-annotator agreement (Cohen\'s κ)',
                '6. Write research report and prepare for publication'
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(plan, f, indent=2)
        
        print(f"Analysis plan saved to {output_path}")
        
        return plan


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Dataset Management for AI-TD Research")
    parser.add_argument("--merge", nargs='+', help="Merge multiple CSV files")
    parser.add_argument("--filter", help="Filter dataset CSV file")
    parser.add_argument("--balance", help="Balance dataset CSV file")
    parser.add_argument("--validate", help="Validate dataset CSV file")
    parser.add_argument("--plan", help="Create analysis plan for dataset")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    manager = DatasetManager()
    
    if args.merge:
        df = manager.merge_datasets(args.merge, args.output)
        if args.validate:
            manager.validate_dataset(df)
    
    elif args.filter:
        df = pd.read_csv(args.filter)
        filtered_df = manager.filter_dataset(df, args.output)
        if args.validate:
            manager.validate_dataset(filtered_df)
    
    elif args.balance:
        df = pd.read_csv(args.balance)
        balanced_df = manager.balance_dataset(df, args.output)
        if args.validate:
            manager.validate_dataset(balanced_df)
    
    elif args.validate:
        df = pd.read_csv(args.validate)
        manager.validate_dataset(df)
    
    elif args.plan:
        df = pd.read_csv(args.plan)
        manager.create_analysis_plan(df, args.output)
    
    else:
        print("Please specify an action: --merge, --filter, --balance, --validate, or --plan")
        parser.print_help()


if __name__ == "__main__":
    main()
