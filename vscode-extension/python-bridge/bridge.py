#!/usr/bin/env python3
"""
AI-TD VS Code Bridge (python-bridge/bridge.py)

เรียกใช้โดย extension.ts ผ่าน child_process.spawn:
    python bridge.py --file <path>
    python bridge.py --dir  <path>
    python bridge.py --file <path> --weights '{"complexity":0.3,...}'

Output: JSON เดียวพิมพ์ไปที่ stdout เสมอ
"""

import argparse
import json
import os
import sys
from pathlib import Path


def find_project_root() -> Path:
    """หา project root (ที่มีโฟลเดอร์ engine/) จาก script location."""
    here = Path(__file__).resolve().parent   # python-bridge/
    # vscode-extension/python-bridge/ → ../../ คือ project root
    for candidate in [here.parent.parent, here.parent]:
        if (candidate / "engine" / "main.py").exists():
            return candidate
    raise FileNotFoundError(
        "ไม่พบ engine/main.py — กรุณาตั้งค่า 'aitd.enginePath' ใน VS Code Settings"
    )


def setup_engine_path():
    """เพิ่ม project root เข้า sys.path."""
    root = os.environ.get("AITD_ENGINE_PATH") or str(find_project_root())
    if root not in sys.path:
        sys.path.insert(0, root)


try:
    setup_engine_path()
    from engine.parsers.tree_sitter_parser import (
        parse_file, detect_language, SUPPORTED_LANGUAGES
    )
    from engine.analyzers.complexity import ComplexityAnalyzer
    from engine.analyzers.duplication import DuplicationAnalyzer
    from engine.analyzers.documentation import DocumentationAnalyzer
    from engine.analyzers.error_handling import ErrorHandlingAnalyzer
    from engine.scoring.ai_td_score import AITDScoreCalculator, DEFAULT_WEIGHTS
except ImportError as exc:
    print(json.dumps({"error": f"Engine import failed: {exc}. ตรวจสอบ aitd.enginePath และ aitd.pythonPath"}))
    sys.exit(1)


# ─────────────────────────────────────────────────────────────
# Core analysis functions
# ─────────────────────────────────────────────────────────────

def analyze_single_file(file_path: str, weights: dict) -> dict:
    """วิเคราะห์ไฟล์เดียว → dict พร้อม annotations สำหรับ decorator."""
    try:
        lang = detect_language(file_path)
        if not lang:
            return {"error": f"ไม่รองรับนามสกุล: {Path(file_path).suffix}", "file_path": file_path}

        pr = parse_file(file_path)
        calc = AITDScoreCalculator(weights=weights)

        complexity  = ComplexityAnalyzer().analyze(pr)
        duplication = DuplicationAnalyzer().analyze(pr)
        doc         = DocumentationAnalyzer().analyze(pr)
        err         = ErrorHandlingAnalyzer().analyze(pr)
        score       = calc.calculate(complexity, duplication, doc, err)

        # Function-level annotations (สำหรับ inline decoration ใน editor)
        fn_annotations = []
        for fn in complexity.functions:
            sev = "high" if fn.cyclomatic > 15 else "medium" if fn.cyclomatic > 7 else "low"
            fn_annotations.append({
                "name":       fn.name,
                "start_line": fn.start_line - 1,   # 0-indexed สำหรับ VS Code Range
                "end_line":   fn.end_line - 1,
                "cyclomatic": fn.cyclomatic,
                "cognitive":  fn.cognitive,
                "severity":   sev,
            })

        # Documentation gap annotations
        doc_gaps = [
            {
                "name":       e.name,
                "type":       e.entity_type,
                "start_line": e.start_line - 1,
            }
            for e in doc.entities if not e.has_docstring
        ]

        return {
            "file_path":    file_path,
            "language":     lang,
            "parse_errors": pr.has_errors,
            "total_score":  round(score.total_score, 4),
            "severity":     score.severity,          # "low" | "medium" | "high"
            "dimensions": {
                "complexity": {
                    "score":          round(score.complexity_score, 4),
                    "avg_cyclomatic": complexity.avg_cyclomatic,
                    "max_cyclomatic": complexity.max_cyclomatic,
                    "avg_cognitive":  complexity.avg_cognitive,
                    "function_count": complexity.function_count,
                },
                "duplication": {
                    "score":            round(score.duplication_score, 4),
                    "ratio_pct":        duplication.duplication_ratio,
                    "duplicated_lines": duplication.duplicated_lines,
                    "total_lines":      duplication.total_lines,
                },
                "documentation": {
                    "score":            round(score.documentation_score, 4),
                    "coverage_ratio":   round(doc.doc_coverage_ratio, 4),
                    "documented_funcs": doc.documented_functions,
                    "total_funcs":      doc.total_functions,
                    "has_module_doc":   doc.has_module_docstring,
                },
                "error_handling": {
                    "score":             round(score.error_handling_score, 4),
                    "coverage_ratio":    round(err.coverage_ratio, 4),
                    "bare_except_count": err.bare_except_count,
                    "funcs_handled":     err.functions_with_handling,
                    "total_functions":   err.total_functions,
                },
            },
            "annotations": {
                "functions": fn_annotations,
                "doc_gaps":  doc_gaps,
            },
        }

    except Exception as exc:
        return {"error": str(exc), "file_path": file_path}


def analyze_directory(dir_path: str, weights: dict) -> dict:
    """วิเคราะห์ทุกไฟล์ใน directory → workspace summary + list of file results."""
    skip_dirs = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}
    results, skipped = [], []

    path = Path(dir_path)
    for ext in SUPPORTED_LANGUAGES:
        for f in sorted(path.rglob(f"*{ext}")):
            if any(part in skip_dirs for part in f.parts):
                continue
            r = analyze_single_file(str(f), weights)
            if "error" in r and "file_path" in r and len(r) == 2:
                skipped.append({"file": str(f), "error": r["error"]})
            else:
                results.append(r)

    if not results:
        return {"error": "ไม่พบไฟล์ที่รองรับ (.py / .js / .ts)", "skipped": skipped}

    scores = [r["total_score"] for r in results]
    sev_dist = {"low": 0, "medium": 0, "high": 0}
    for r in results:
        sev_dist[r["severity"]] = sev_dist.get(r["severity"], 0) + 1

    return {
        "directory":             dir_path,
        "files_analyzed":        len(results),
        "files_skipped":         len(skipped),
        "average_score":         round(sum(scores) / len(scores), 4),
        "max_score":             round(max(scores), 4),
        "min_score":             round(min(scores), 4),
        "severity_distribution": sev_dist,
        "files":                 results,
    }


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI-TD Engine Bridge for VS Code")
    parser.add_argument("--file",    help="วิเคราะห์ไฟล์เดียว")
    parser.add_argument("--dir",     help="วิเคราะห์ทั้ง directory")
    parser.add_argument("--weights", help='JSON weights เช่น \'{"complexity":0.3,...}\'')
    args = parser.parse_args()

    # ตั้งค่า weights
    weights = DEFAULT_WEIGHTS.copy()
    if args.weights:
        try:
            weights.update(json.loads(args.weights))
        except json.JSONDecodeError:
            pass  # ใช้ default weights แทน

    # รัน
    if args.file:
        result = analyze_single_file(args.file, weights)
    elif args.dir:
        result = analyze_directory(args.dir, weights)
    else:
        result = {"error": "ต้องระบุ --file หรือ --dir"}

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
