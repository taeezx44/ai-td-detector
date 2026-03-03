"""
AI-TD Detector — Main Entry Point

Usage:
    python main.py --file <path>          Analyze a single file
    python main.py --dir <path>           Analyze all supported files in directory
    python main.py --repo <owner/repo>    Analyze GitHub repo commits (requires token)

Examples:
    python main.py --file example.py
    python main.py --dir ./src --output results.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'engine' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.parsers.tree_sitter_parser import parse_file, detect_language, SUPPORTED_LANGUAGES
from engine.analyzers.complexity import ComplexityAnalyzer
from engine.analyzers.duplication import DuplicationAnalyzer
from engine.analyzers.documentation import DocumentationAnalyzer
from engine.analyzers.error_handling import ErrorHandlingAnalyzer
from engine.scoring.ai_td_score import AITDScoreCalculator, AITDScore


def analyze_file(file_path: str, calculator: AITDScoreCalculator) -> AITDScore:
    """Analyze a single file and return AI-TD Score."""
    parse_result = parse_file(file_path)

    complexity = ComplexityAnalyzer().analyze(parse_result)
    duplication = DuplicationAnalyzer().analyze(parse_result)
    documentation = DocumentationAnalyzer().analyze(parse_result)
    error_handling = ErrorHandlingAnalyzer().analyze(parse_result)

    return calculator.calculate(complexity, duplication, documentation, error_handling)


def analyze_directory(dir_path: str, calculator: AITDScoreCalculator) -> list[AITDScore]:
    """Analyze all supported files in a directory."""
    results = []
    path = Path(dir_path)

    supported_files = []
    for ext in SUPPORTED_LANGUAGES:
        supported_files.extend(path.rglob(f"*{ext}"))

    # Skip common non-project directories
    skip_dirs = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}

    for file_path in sorted(supported_files):
        if any(skip in file_path.parts for skip in skip_dirs):
            continue
        try:
            score = analyze_file(str(file_path), calculator)
            results.append(score)
            print(f"  [{score.severity.upper():6s}] {score.total_score:.4f}  {file_path}")
        except Exception as e:
            print(f"  [ERROR] {file_path}: {e}", file=sys.stderr)

    return results


def print_summary(results: list[AITDScore]):
    """Print aggregate summary of analysis results."""
    if not results:
        print("No files analyzed.")
        return

    scores = [r.total_score for r in results]
    avg = sum(scores) / len(scores)
    high_count = sum(1 for r in results if r.severity == "high")
    med_count = sum(1 for r in results if r.severity == "medium")
    low_count = sum(1 for r in results if r.severity == "low")

    print(f"\n{'═' * 60}")
    print(f"  AI-TD Score Summary")
    print(f"{'═' * 60}")
    print(f"  Files analyzed:  {len(results)}")
    print(f"  Average score:   {avg:.4f}")
    print(f"  Max score:       {max(scores):.4f}")
    print(f"  Min score:       {min(scores):.4f}")
    print(f"")
    print(f"  Severity Distribution:")
    print(f"    HIGH:   {high_count:3d} files")
    print(f"    MEDIUM: {med_count:3d} files")
    print(f"    LOW:    {low_count:3d} files")
    print(f"{'═' * 60}")


def export_results(results: list[AITDScore], output_path: str):
    """Export results to JSON file."""
    data = {
        "tool": "AI-TD Detector v1.0",
        "files_analyzed": len(results),
        "average_score": round(sum(r.total_score for r in results) / len(results), 4) if results else 0,
        "results": [r.to_dict() for r in results],
    }
    Path(output_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AI-TD Detector — Automated Detection of AI-Induced Technical Debt"
    )
    parser.add_argument("--file", type=str, help="Path to a single file to analyze")
    parser.add_argument("--dir", type=str, help="Path to directory to analyze")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    parser.add_argument(
        "--weights", type=str, default=None,
        help='Custom weights as JSON string, e.g. \'{"complexity":0.3,"duplication":0.25,"documentation":0.2,"error_handling":0.25}\''
    )

    args = parser.parse_args()

    if not args.file and not args.dir:
        parser.print_help()
        sys.exit(1)

    # Initialize calculator
    weights = json.loads(args.weights) if args.weights else None
    calculator = AITDScoreCalculator(weights=weights)

    results = []

    if args.file:
        print(f"Analyzing file: {args.file}")
        score = analyze_file(args.file, calculator)
        print(score.summary())
        results = [score]

    elif args.dir:
        print(f"Analyzing directory: {args.dir}\n")
        results = analyze_directory(args.dir, calculator)
        print_summary(results)

    # Export if requested
    if args.output and results:
        export_results(results, args.output)


if __name__ == "__main__":
    main()
