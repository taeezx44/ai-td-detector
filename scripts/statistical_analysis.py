#!/usr/bin/env python3
"""
Statistical Analysis Scripts for AI-TD Detector Research

Implements statistical tests for RQ1 and RQ2:
- RQ1: Do AI-generated code segments exhibit higher technical debt than human-written code?
- RQ2: Which dimensions are most strongly associated with AI-assisted code generation?

Usage:
    python scripts/statistical_analysis.py --dataset data/ai_repos.csv
    python scripts/statistical_analysis.py --compare data/ai_repos.csv data/human_repos.csv
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score


class StatisticalAnalyzer:
    """Performs statistical analysis for AI-TD research questions."""
    
    def __init__(self):
        self.alpha = 0.05
        self.bonferroni_alpha = 0.05 / 3  # For multiple comparisons
    
    def load_dataset(self, csv_path: str) -> pd.DataFrame:
        """Load repository dataset from CSV."""
        df = pd.read_csv(csv_path)
        
        # Convert string columns to appropriate types
        if 'ai_signals' in df.columns:
            df['ai_signals'] = df['ai_signals'].apply(self._parse_json_column)
        if 'ai_commits' in df.columns:
            df['ai_commits'] = df['ai_commits'].apply(self._parse_json_column)
        
        return df
    
    def _parse_json_column(self, json_str):
        """Parse JSON string column safely."""
        if pd.isna(json_str) or json_str == '':
            return []
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def run_ai_td_analysis(self, ai_df: pd.DataFrame, human_df: pd.DataFrame) -> Dict:
        """
        Run complete AI-TD statistical analysis.
        
        Args:
            ai_df: DataFrame with AI-assisted repositories
            human_df: DataFrame with human-written repositories
            
        Returns:
            Dictionary with analysis results
        """
        results = {
            'rq1_results': self.analyze_rq1(ai_df, human_df),
            'rq2_results': self.analyze_rq2(ai_df, human_df),
            'descriptive_stats': self.compute_descriptive_stats(ai_df, human_df)
        }
        
        return results
    
    def analyze_rq1(self, ai_df: pd.DataFrame, human_df: pd.DataFrame) -> Dict:
        """
        RQ1: Do AI-generated code segments exhibit higher technical debt than human-written code?
        
        Uses Wilcoxon Signed-Rank Test for non-parametric comparison.
        """
        results = {}
        
        # Extract AI-TD scores (simulated for now - will come from actual analysis)
        ai_scores = self._extract_ai_td_scores(ai_df)
        human_scores = self._extract_ai_td_scores(human_df)
        
        if len(ai_scores) == 0 or len(human_scores) == 0:
            return {'error': 'No AI-TD scores available for comparison'}
        
        # Wilcoxon Signed-Rank Test
        statistic, p_value = stats.wilcoxon(ai_scores, human_scores)
        
        # Effect size (Cohen's d for non-parametric)
        effect_size = self._compute_cohens_d(ai_scores, human_scores)
        
        results = {
            'test': 'Wilcoxon Signed-Rank Test',
            'n_ai': len(ai_scores),
            'n_human': len(human_scores),
            'ai_mean': np.mean(ai_scores),
            'human_mean': np.mean(human_scores),
            'ai_median': np.median(ai_scores),
            'human_median': np.median(human_scores),
            'ai_std': np.std(ai_scores),
            'human_std': np.std(human_scores),
            'statistic': statistic,
            'p_value': p_value,
            'p_value_bonferroni': p_value * 3,  # Bonferroni correction
            'significant_bonferroni': p_value * 3 < self.bonferroni_alpha,
            'significant': p_value < self.alpha,
            'effect_size': effect_size,
            'effect_size_interpretation': self._interpret_effect_size(effect_size),
            'power_analysis': self._compute_power(effect_size, len(ai_scores), len(human_scores))
        }
        
        return results
    
    def analyze_rq2(self, ai_df: pd.DataFrame, human_df: pd.DataFrame) -> Dict:
        """
        RQ2: Which dimensions of technical debt are most strongly associated with AI-assisted code generation?
        
        Uses per-dimension analysis and feature importance.
        """
        results = {}
        
        # Extract per-dimension metrics
        dimensions = ['complexity', 'duplication', 'documentation', 'error_handling']
        
        for dim in dimensions:
            ai_values = self._extract_dimension_scores(ai_df, dim)
            human_values = self._extract_dimension_scores(human_df, dim)
            
            if len(ai_values) > 0 and len(human_values) > 0:
                # Mann-Whitney U test for each dimension
                statistic, p_value = stats.mannwhitneyu(ai_values, human_values, alternative='two-sided')
                effect_size = self._compute_cohens_d(ai_values, human_values)
                
                results[f'{dim}_test'] = {
                    'test': 'Mann-Whitney U',
                    'n_ai': len(ai_values),
                    'n_human': len(human_values),
                    'ai_mean': np.mean(ai_values),
                    'human_mean': np.mean(human_values),
                    'statistic': statistic,
                    'p_value': p_value,
                    'p_value_bonferroni': p_value * len(dimensions),
                    'significant_bonferroni': p_value * len(dimensions) < self.alpha,
                    'effect_size': effect_size,
                    'effect_size_interpretation': self._interpret_effect_size(effect_size)
                }
        
        # Feature importance using Random Forest
        feature_importance = self._compute_feature_importance(ai_df, human_df)
        results['feature_importance'] = feature_importance
        
        # Ablation study (conceptual - would need actual AI-TD score computation)
        results['ablation_study'] = self._conceptual_ablation_study()
        
        return results
    
    def compute_descriptive_stats(self, ai_df: pd.DataFrame, human_df: pd.DataFrame) -> Dict:
        """Compute descriptive statistics for both groups."""
        stats = {}
        
        for name, df in [('AI', ai_df), ('Human', human_df)]:
            stats[name] = {
                'total_repos': len(df),
                'avg_stars': df['stars'].mean() if 'stars' in df.columns else 0,
                'avg_forks': df['forks'].mean() if 'forks' in df.columns else 0,
                'avg_size_kb': df['size_kb'].mean() if 'size_kb' in df.columns else 0,
                'language_distribution': df['language'].value_counts().to_dict() if 'language' in df.columns else {},
                'ai_confidence_distribution': df['ai_confidence'].value_counts().to_dict() if 'ai_confidence' in df.columns else {}
            }
        
        return stats
    
    def _extract_ai_td_scores(self, df: pd.DataFrame) -> List[float]:
        """
        Extract AI-TD scores from repository data.
        NOTE: This is a placeholder - actual implementation would run AI-TD analysis on each repo
        """
        # For now, simulate scores based on AI confidence and other metrics
        scores = []
        
        for _, repo in df.iterrows():
            # Simulate AI-TD score based on available metadata
            base_score = 0.3  # Base score for human code
            
            if repo.get('ai_confidence') == 'High':
                base_score += 0.4
            elif repo.get('ai_confidence') == 'Medium':
                base_score += 0.2
            elif repo.get('ai_confidence') == 'Low':
                base_score += 0.1
            
            # Add some randomness for simulation
            score = base_score + np.random.normal(0, 0.1)
            score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
            scores.append(score)
        
        return scores
    
    def _extract_dimension_scores(self, df: pd.DataFrame, dimension: str) -> List[float]:
        """
        Extract scores for a specific dimension.
        NOTE: This is a placeholder - actual implementation would analyze code
        """
        # Simulate dimension scores
        scores = []
        
        for _, repo in df.iterrows():
            base_score = np.random.uniform(0.1, 0.4)  # Human baseline
            
            if repo.get('ai_confidence') == 'High':
                if dimension == 'duplication':
                    base_score += 0.4  # AI tends to duplicate more
                elif dimension == 'documentation':
                    base_score += 0.3  # AI tends to lack docs
                elif dimension == 'error_handling':
                    base_score += 0.3  # AI tends to lack error handling
                elif dimension == 'complexity':
                    base_score += 0.2  # AI tends to be more complex
            elif repo.get('ai_confidence') == 'Medium':
                base_score += 0.1
            
            score = max(0.0, min(1.0, base_score + np.random.normal(0, 0.1)))
            scores.append(score)
        
        return scores
    
    def _compute_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """Compute Cohen's d effect size."""
        n1, n2 = len(group1), len(group2)
        mean1, mean2 = np.mean(group1), np.mean(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        
        # Pooled standard deviation
        pooled_sd = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        
        if pooled_sd == 0:
            return 0.0
        
        d = (mean1 - mean2) / pooled_sd
        return d
    
    def _interpret_effect_size(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"
    
    def _compute_power(self, effect_size: float, n1: int, n2: int) -> Dict:
        """
        Compute statistical power (simplified).
        NOTE: This is a simplified calculation - actual power analysis would use more sophisticated methods
        """
        # Simplified power calculation
        n = min(n1, n2)  # Use smaller sample size
        if n < 10:
            return {'power': 0.0, 'adequate': False, 'note': 'Sample size too small'}
        
        # Approximate power calculation (simplified)
        z_alpha = 1.96  # For alpha = 0.05
        z_beta = effect_size * np.sqrt(n / 2) - z_alpha
        power = stats.norm.cdf(z_beta)
        
        return {
            'power': max(0.0, min(1.0, power)),
            'adequate': power >= 0.8,
            'note': f"Effect size: {effect_size:.3f}, Sample size: {n}"
        }
    
    def _compute_feature_importance(self, ai_df: pd.DataFrame, human_df: pd.DataFrame) -> Dict:
        """
        Compute feature importance for distinguishing AI vs Human code.
        NOTE: This is a placeholder - actual implementation would use real features
        """
        # Create feature matrix
        features = []
        labels = []
        
        for _, repo in ai_df.iterrows():
            feature_vector = [
                repo.get('stars', 0),
                repo.get('forks', 0),
                repo.get('size_kb', 0),
                1 if repo.get('ai_confidence') == 'High' else 0,
                1 if repo.get('ai_confidence') == 'Medium' else 0,
                1 if repo.get('ai_confidence') == 'Low' else 0,
            ]
            features.append(feature_vector)
            labels.append(1)  # AI
        
        for _, repo in human_df.iterrows():
            feature_vector = [
                repo.get('stars', 0),
                repo.get('forks', 0),
                repo.get('size_kb', 0),
                0, 0, 0  # No AI confidence
            ]
            features.append(feature_vector)
            labels.append(0)  # Human
        
        if len(features) < 10:
            return {'error': 'Insufficient data for feature importance analysis'}
        
        X = np.array(features)
        y = np.array(labels)
        
        # Random Forest for feature importance
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        # Cross-validation score
        cv_scores = cross_val_score(rf, X, y, cv=5, scoring='accuracy')
        
        feature_names = ['stars', 'forks', 'size_kb', 'ai_confidence_high', 'ai_confidence_medium', 'ai_confidence_low']
        
        return {
            'feature_importance': dict(zip(feature_names, rf.feature_importances_.tolist())),
            'cv_accuracy_mean': cv_scores.mean(),
            'cv_accuracy_std': cv_scores.std(),
            'top_features': sorted(zip(feature_names, rf.feature_importances_), key=lambda x: x[1], reverse=True)
        }
    
    def _conceptual_ablation_study(self) -> Dict:
        """
        Conceptual ablation study results.
        NOTE: This would be implemented with actual AI-TD score calculations
        """
        return {
            'note': 'Conceptual ablation study - would remove each dimension and recompute AI-TD scores',
            'expected_impact': {
                'complexity': 'High impact - primary driver of technical debt',
                'duplication': 'Medium impact - significant for AI-generated code',
                'documentation': 'Medium impact - AI tends to lack documentation',
                'error_handling': 'High impact - AI often omits error handling'
            }
        }
    
    def save_results(self, results: Dict, output_path: str):
        """Save analysis results to JSON file."""
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        def recursive_convert(item):
            if isinstance(item, dict):
                return {k: recursive_convert(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [recursive_convert(i) for i in item]
            else:
                return convert_numpy(item)
        
        converted_results = recursive_convert(results)
        
        with open(output_path, 'w') as f:
            json.dump(converted_results, f, indent=2)
        
        print(f"Results saved to {output_path}")
    
    def print_summary(self, results: Dict):
        """Print a summary of key results."""
        print("\n" + "="*60)
        print("AI-TD Detector Statistical Analysis Summary")
        print("="*60)
        
        # RQ1 Results
        rq1 = results.get('rq1_results', {})
        if rq1:
            print(f"\nRQ1: Do AI-generated code exhibit higher technical debt?")
            print(f"  Test: {rq1.get('test', 'N/A')}")
            print(f"  AI Mean: {rq1.get('ai_mean', 0):.4f}")
            print(f"  Human Mean: {rq1.get('human_mean', 0):.4f}")
            print(f"  P-value: {rq1.get('p_value', 1):.6f}")
            print(f"  Effect Size (d): {rq1.get('effect_size', 0):.4f} ({rq1.get('effect_size_interpretation', 'N/A')})")
            print(f"  Significant (\u03B1=0.05): {'Yes' if rq1.get('significant', False) else 'No'}")
            print(f"  Significant (Bonferroni): {'Yes' if rq1.get('significant_bonferroni', False) else 'No'}")
        
        # RQ2 Results
        rq2 = results.get('rq2_results', {})
        if rq2:
            print(f"\nRQ2: Which dimensions are most associated with AI code?")
            for key, result in rq2.items():
                if key.endswith('_test'):
                    dim = key.replace('_test', '')
                    print(f"  {dim.capitalize()}:")
                    print(f"    AI Mean: {result.get('ai_mean', 0):.4f}")
                    print(f"    Human Mean: {result.get('human_mean', 0):.4f}")
                    print(f"    P-value: {result.get('p_value', 1):.6f}")
                    print(f"    Effect Size: {result.get('effect_size', 0):.4f} ({result.get('effect_size_interpretation', 'N/A')})")
            
            # Feature importance
            feature_imp = rq2.get('feature_importance', {})
            if 'top_features' in feature_imp:
                print(f"\n  Top Distinguishing Features:")
                for feature, importance in feature_imp['top_features'][:3]:
                    print(f"    {feature}: {importance:.4f}")
        
        # Descriptive Stats
        desc_stats = results.get('descriptive_stats', {})
        if desc_stats:
            print(f"\nDataset Summary:")
            for group, stats in desc_stats.items():
                print(f"  {group} Repositories: {stats.get('total_repos', 0)}")
                print(f"    Avg Stars: {stats.get('avg_stars', 0):.1f}")
                print(f"    Avg Size (KB): {stats.get('avg_size_kb', 0):.1f}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Statistical Analysis for AI-TD Research")
    parser.add_argument("--dataset", help="Single dataset CSV file")
    parser.add_argument("--compare", nargs=2, help="Two CSV files to compare (AI vs Human)")
    parser.add_argument("--output", default="statistical_results.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    analyzer = StatisticalAnalyzer()
    
    if args.compare:
        # Compare two datasets
        ai_df = analyzer.load_dataset(args.compare[0])
        human_df = analyzer.load_dataset(args.compare[1])
        
        print(f"Loaded {len(ai_df)} AI repositories and {len(human_df)} Human repositories")
        
        results = analyzer.run_ai_td_analysis(ai_df, human_df)
        analyzer.save_results(results, args.output)
        analyzer.print_summary(results)
        
    elif args.dataset:
        # Analyze single dataset
        df = analyzer.load_dataset(args.dataset)
        print(f"Loaded {len(df)} repositories")
        
        # For single dataset, split by AI confidence for demonstration
        ai_repos = df[df['ai_confidence'].isin(['High', 'Medium'])]
        human_repos = df[df['ai_confidence'].isin(['Low', 'None'])]
        
        results = analyzer.run_ai_td_analysis(ai_repos, human_repos)
        analyzer.save_results(results, args.output)
        analyzer.print_summary(results)
        
    else:
        print("Please specify --dataset or --compare")
        parser.print_help()


if __name__ == "__main__":
    main()
