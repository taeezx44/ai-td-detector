"""Unit tests for AI-TD Score Calculator."""

import pytest
from engine.parsers.tree_sitter_parser import parse_file, parse_code
from engine.analyzers.complexity import ComplexityAnalyzer
from engine.analyzers.duplication import DuplicationAnalyzer
from engine.analyzers.documentation import DocumentationAnalyzer
from engine.analyzers.error_handling import ErrorHandlingAnalyzer
from engine.scoring.ai_td_score import AITDScoreCalculator, DEFAULT_WEIGHTS


@pytest.fixture
def calculator():
    return AITDScoreCalculator()


@pytest.fixture
def analyzers():
    return {
        "complexity": ComplexityAnalyzer(),
        "duplication": DuplicationAnalyzer(),
        "documentation": DocumentationAnalyzer(),
        "error_handling": ErrorHandlingAnalyzer(),
    }


def _full_analysis(code: str, language: str, analyzers, calculator):
    """Helper: run all 4 analyzers + scoring on a code snippet."""
    pr = parse_code(code, language)
    return calculator.calculate(
        complexity=analyzers["complexity"].analyze(pr),
        duplication=analyzers["duplication"].analyze(pr),
        documentation=analyzers["documentation"].analyze(pr),
        error_handling=analyzers["error_handling"].analyze(pr),
    )


class TestAITDScore:

    def test_well_written_code_low_score(self, calculator, analyzers):
        """Well-documented, simple code → low AI-TD score."""
        code = '''
"""Module for greeting users."""

def greet(name: str) -> str:
    """Return a greeting message for the given name."""
    try:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        return f"Hello, {name}!"
    except TypeError as e:
        return f"Error: {e}"
'''
        score = _full_analysis(code, "python", analyzers, calculator)
        assert score.total_score < 0.4
        assert score.severity in ("low", "medium")

    def test_ai_style_code_higher_score(self, calculator, analyzers):
        """Typical AI-generated pattern: no docs, no error handling, complex."""
        code = '''
def process(data, config, opts):
    result = []
    for item in data:
        if item.get("type") == "A":
            if item.get("active"):
                for sub in item.get("children", []):
                    if sub.get("valid"):
                        if sub.get("score") > config.get("t", 0):
                            result.append(transform(sub))
        elif item.get("type") == "B":
            for sub in item.get("children", []):
                if sub.get("valid") and sub.get("score") > 0:
                    result.append(sub)
    return result

def transform(item):
    x = item["value"] * 2 + item["offset"]
    if x > 100:
        x = 100
    if x < 0:
        x = 0
    return {"result": x, "id": item["id"]}
'''
        score = _full_analysis(code, "python", analyzers, calculator)
        assert score.total_score > 0.2  # Should be noticeably higher
        assert score.documentation_score > 0  # No docs → high doc debt

    def test_score_between_0_and_1(self, calculator, analyzers):
        """Score must always be in [0.0, 1.0]."""
        codes = [
            "",
            "x = 1",
            "def f(): pass",
            "def f():\n    for i in range(100):\n        if i > 50:\n            print(i)",
        ]
        for code in codes:
            score = _full_analysis(code, "python", analyzers, calculator)
            assert 0.0 <= score.total_score <= 1.0

    def test_weights_sum_validation(self):
        """Custom weights must sum to 1.0."""
        with pytest.raises(ValueError, match="sum to 1.0"):
            AITDScoreCalculator(weights={
                "complexity": 0.5,
                "duplication": 0.5,
                "documentation": 0.5,
                "error_handling": 0.5,
            })

    def test_custom_weights(self, analyzers):
        """Custom weights change the score."""
        code = '''
def complex_func(data):
    for item in data:
        if item > 0:
            for sub in range(item):
                if sub % 2 == 0:
                    print(sub)
'''
        # Heavy complexity weight
        calc_heavy_c = AITDScoreCalculator(weights={
            "complexity": 0.70, "duplication": 0.10,
            "documentation": 0.10, "error_handling": 0.10,
        })
        # Light complexity weight
        calc_light_c = AITDScoreCalculator(weights={
            "complexity": 0.10, "duplication": 0.30,
            "documentation": 0.30, "error_handling": 0.30,
        })

        score_heavy = _full_analysis(code, "python", analyzers, calc_heavy_c)
        score_light = _full_analysis(code, "python", analyzers, calc_light_c)

        # Different weights must produce different scores
        assert score_heavy.total_score != score_light.total_score

    def test_to_dict(self, calculator, analyzers):
        """to_dict() returns valid structure."""
        code = "def f(): pass"
        score = _full_analysis(code, "python", analyzers, calculator)
        d = score.to_dict()

        assert "total_score" in d
        assert "severity" in d
        assert "dimensions" in d
        assert set(d["dimensions"].keys()) == {"complexity", "duplication", "documentation", "error_handling"}
        for dim in d["dimensions"].values():
            assert "score" in dim
            assert "weight" in dim
            assert "weighted" in dim

    def test_summary_string(self, calculator, analyzers):
        """summary() returns formatted string."""
        code = "def f(): pass"
        score = _full_analysis(code, "python", analyzers, calculator)
        summary = score.summary()
        assert "AI-TD Score Report" in summary
        assert "Complexity" in summary
        assert "Duplication" in summary
