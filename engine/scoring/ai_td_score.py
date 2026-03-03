"""
AI-TD Score Calculator

Composite metric: AI-TD Score = 0.30·C + 0.25·D + 0.20·Doc + 0.25·(1−E)

Weights based on Bayesian framing (Literature-driven Prior):
  - Complexity (C):     30%  — McCabe (1976) + Herbold et al. (2022)
  - Duplication (D):    25%  — Roy & Cordy (2007)
  - Documentation (Doc): 20% — Aghajani et al. (2020)
  - Error Handling (E):  25% — Perry et al. (2023)

Weights will be recalibrated via PCA from Pilot Dataset (month 8–10).
"""

from dataclasses import dataclass, field

from engine.analyzers.complexity import ComplexityResult
from engine.analyzers.duplication import DuplicationResult
from engine.analyzers.documentation import DocumentationResult
from engine.analyzers.error_handling import ErrorHandlingResult


# Default weights (Literature-driven Prior)
DEFAULT_WEIGHTS = {
    "complexity": 0.30,
    "duplication": 0.25,
    "documentation": 0.20,
    "error_handling": 0.25,
}

# Severity thresholds
SEVERITY_THRESHOLDS = {
    "low": (0.0, 0.30),
    "medium": (0.30, 0.60),
    "high": (0.60, 1.0),
}


@dataclass
class AITDScore:
    """Complete AI-TD Score with per-dimension breakdown."""
    file_path: str
    language: str

    # Per-dimension normalized scores (0.0–1.0)
    complexity_score: float
    duplication_score: float
    documentation_score: float
    error_handling_score: float  # Higher = better handling

    # Weights used
    weights: dict[str, float]

    # Composite score
    total_score: float = 0.0
    severity: str = "low"

    # Raw results for detailed inspection
    complexity_result: ComplexityResult = None
    duplication_result: DuplicationResult = None
    documentation_result: DocumentationResult = None
    error_handling_result: ErrorHandlingResult = None

    def __post_init__(self):
        self.total_score = self._calculate_total()
        self.severity = self._classify_severity()

    def _calculate_total(self) -> float:
        """
        AI-TD Score = w_C·C + w_D·D + w_Doc·Doc + w_E·(1−E)
        Note: (1−E) because higher E means BETTER handling = LESS debt
        """
        score = (
            self.weights["complexity"] * self.complexity_score
            + self.weights["duplication"] * self.duplication_score
            + self.weights["documentation"] * self.documentation_score
            + self.weights["error_handling"] * (1 - self.error_handling_score)
        )
        return round(min(max(score, 0.0), 1.0), 4)

    def _classify_severity(self) -> str:
        """Classify total score into severity level."""
        for level, (low, high) in SEVERITY_THRESHOLDS.items():
            if low <= self.total_score < high:
                return level
        return "high"

    def to_dict(self) -> dict:
        """Export as dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "total_score": self.total_score,
            "severity": self.severity,
            "dimensions": {
                "complexity": {
                    "score": self.complexity_score,
                    "weight": self.weights["complexity"],
                    "weighted": round(self.weights["complexity"] * self.complexity_score, 4),
                },
                "duplication": {
                    "score": self.duplication_score,
                    "weight": self.weights["duplication"],
                    "weighted": round(self.weights["duplication"] * self.duplication_score, 4),
                },
                "documentation": {
                    "score": self.documentation_score,
                    "weight": self.weights["documentation"],
                    "weighted": round(self.weights["documentation"] * self.documentation_score, 4),
                },
                "error_handling": {
                    "score": self.error_handling_score,
                    "weight": self.weights["error_handling"],
                    "weighted": round(self.weights["error_handling"] * (1 - self.error_handling_score), 4),
                },
            },
            "weights": self.weights,
        }

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"═══ AI-TD Score Report: {self.file_path} ═══",
            f"Language:    {self.language}",
            f"Total Score: {self.total_score:.4f} [{self.severity.upper()}]",
            f"",
            f"  Complexity (C):      {self.complexity_score:.4f}  × {self.weights['complexity']:.2f} = {self.weights['complexity'] * self.complexity_score:.4f}",
            f"  Duplication (D):     {self.duplication_score:.4f}  × {self.weights['duplication']:.2f} = {self.weights['duplication'] * self.duplication_score:.4f}",
            f"  Documentation (Doc): {self.documentation_score:.4f}  × {self.weights['documentation']:.2f} = {self.weights['documentation'] * self.documentation_score:.4f}",
            f"  Error Handling (E):  {self.error_handling_score:.4f}  × {self.weights['error_handling']:.2f} = {self.weights['error_handling'] * (1 - self.error_handling_score):.4f}  (inverted: 1−E)",
            f"{'═' * 50}",
        ]
        return "\n".join(lines)


class AITDScoreCalculator:
    """Orchestrates all analyzers and computes composite AI-TD Score."""

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self._validate_weights()

    def _validate_weights(self):
        """Ensure weights sum to 1.0."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def calculate(
        self,
        complexity: ComplexityResult,
        duplication: DuplicationResult,
        documentation: DocumentationResult,
        error_handling: ErrorHandlingResult,
    ) -> AITDScore:
        """Calculate composite AI-TD Score from analyzer results."""
        return AITDScore(
            file_path=complexity.file_path,
            language=complexity.language,
            complexity_score=complexity.normalized_score,
            duplication_score=duplication.normalized_score,
            documentation_score=documentation.normalized_score,
            error_handling_score=error_handling.normalized_score,
            weights=self.weights,
            complexity_result=complexity,
            duplication_result=duplication,
            documentation_result=documentation,
            error_handling_result=error_handling,
        )
