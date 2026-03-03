"""
Complexity Analyzer (Dimension C — Weight 30%)

Calculates Cyclomatic Complexity and Cognitive Complexity from AST.
Based on McCabe (1976) and Herbold et al. (2022).

Cyclomatic Complexity = Number of decision points + 1 per function
Cognitive Complexity  = Weighted nesting-aware complexity
"""

from dataclasses import dataclass
from tree_sitter import Node

from engine.parsers.tree_sitter_parser import (
    ParseResult,
    find_functions,
    get_node_text,
    traverse_tree,
)

# Decision-point node types per language
DECISION_NODES = {
    "python": {
        "if_statement", "elif_clause", "for_statement", "while_statement",
        "except_clause", "with_statement", "assert_statement",
        "conditional_expression",  # ternary: x if cond else y
    },
    "javascript": {
        "if_statement", "for_statement", "for_in_statement", "while_statement",
        "do_statement", "switch_case", "catch_clause", "ternary_expression",
    },
    "typescript": {
        "if_statement", "for_statement", "for_in_statement", "while_statement",
        "do_statement", "switch_case", "catch_clause", "ternary_expression",
    },
}

# Boolean operators count as additional decision points
BOOLEAN_OPS = {
    "python": {"and", "or"},
    "javascript": {"&&", "||"},
    "typescript": {"&&", "||"},
}

# Nesting-increasing node types (for cognitive complexity)
NESTING_NODES = {
    "python": {
        "if_statement", "for_statement", "while_statement",
        "except_clause", "with_statement", "function_definition",
    },
    "javascript": {
        "if_statement", "for_statement", "for_in_statement", "while_statement",
        "do_statement", "catch_clause", "function_declaration", "arrow_function",
    },
    "typescript": {
        "if_statement", "for_statement", "for_in_statement", "while_statement",
        "do_statement", "catch_clause", "function_declaration", "arrow_function",
    },
}


@dataclass
class FunctionComplexity:
    """Complexity metrics for a single function."""
    name: str
    start_line: int
    end_line: int
    line_count: int
    cyclomatic: int
    cognitive: int


@dataclass
class ComplexityResult:
    """Aggregate complexity metrics for a file."""
    file_path: str
    language: str
    total_cyclomatic: int
    total_cognitive: int
    avg_cyclomatic: float
    avg_cognitive: float
    max_cyclomatic: int
    max_cognitive: int
    function_count: int
    functions: list[FunctionComplexity]
    normalized_score: float = 0.0  # 0.0–1.0

    def __post_init__(self):
        self.normalized_score = self._normalize()

    def _normalize(self) -> float:
        """
        Normalize complexity to 0.0–1.0 scale.
        Thresholds based on McCabe (1976) and industry practice:
          - avg_cyclomatic ≤ 5   → 0.0 (low debt)
          - avg_cyclomatic ≥ 25  → 1.0 (severe debt)
          - max_cyclomatic > 20  → penalty boost
        """
        if self.function_count == 0:
            return 0.0

        # Base score from average cyclomatic
        score = min(max((self.avg_cyclomatic - 5) / 20, 0.0), 1.0)

        # Penalty for any function exceeding threshold
        if self.max_cyclomatic > 20:
            penalty = min((self.max_cyclomatic - 20) / 30, 0.3)
            score = min(score + penalty, 1.0)

        # Cognitive complexity amplifier
        if self.avg_cognitive > 15:
            cognitive_factor = min((self.avg_cognitive - 15) / 30, 0.2)
            score = min(score + cognitive_factor, 1.0)

        return round(score, 4)


class ComplexityAnalyzer:
    """Analyzes Cyclomatic and Cognitive complexity from AST."""

    def analyze(self, parse_result: ParseResult) -> ComplexityResult:
        """Analyze complexity for all functions in parsed file."""
        language = parse_result.language
        functions = find_functions(parse_result)

        func_results = []
        for func_dict in functions:
            func_node = func_dict['node']
            fc = self._analyze_function(func_node, parse_result)
            func_results.append(fc)

        total_cyc = sum(f.cyclomatic for f in func_results)
        total_cog = sum(f.cognitive for f in func_results)
        count = len(func_results)

        return ComplexityResult(
            file_path=parse_result.file_path,
            language=language,
            total_cyclomatic=total_cyc,
            total_cognitive=total_cog,
            avg_cyclomatic=round(total_cyc / count, 2) if count > 0 else 0.0,
            avg_cognitive=round(total_cog / count, 2) if count > 0 else 0.0,
            max_cyclomatic=max((f.cyclomatic for f in func_results), default=0),
            max_cognitive=max((f.cognitive for f in func_results), default=0),
            function_count=count,
            functions=func_results,
        )

    def _analyze_function(self, func_node: Node, pr: ParseResult) -> FunctionComplexity:
        """Calculate complexity for a single function."""
        language = pr.language
        name = self._get_function_name(func_node, pr)

        cyclomatic = self._cyclomatic_complexity(func_node, language, pr.content)
        cognitive = self._cognitive_complexity(func_node, language)

        return FunctionComplexity(
            name=name,
            start_line=func_node.start_point[0] + 1,
            end_line=func_node.end_point[0] + 1,
            line_count=func_node.end_point[0] - func_node.start_point[0] + 1,
            cyclomatic=cyclomatic,
            cognitive=cognitive,
        )

    def _get_function_name(self, func_node: Node, pr: ParseResult) -> str:
        """Extract function name from AST node."""
        for child in func_node.children:
            if child.type == "identifier":
                return get_node_text(child, pr.content)
            if child.type == "property_identifier":
                return get_node_text(child, pr.content)
        return "<anonymous>"

    def _cyclomatic_complexity(self, node: Node, language: str, source: str) -> int:
        """
        McCabe's Cyclomatic Complexity.
        CC = 1 + number_of_decision_points + boolean_operators
        """
        decision_types = DECISION_NODES.get(language, set())
        bool_ops = BOOLEAN_OPS.get(language, set())

        cc = 1  # Base complexity
        
        def count_decision_nodes(node):
            nonlocal cc
            if node.type in decision_types:
                cc += 1
            # Count boolean operators as additional paths
            if node.type in ("boolean_operator", "binary_expression"):
                cc += 0.5
        
        traverse_tree(node, count_decision_nodes)

        return cc

    def _cognitive_complexity(self, func_node: Node, language: str) -> int:
        """
        Cognitive Complexity (SonarSource-inspired).
        Increments for each decision + nesting penalty.
        """
        nesting_types = NESTING_NODES.get(language, set())
        decision_types = DECISION_NODES.get(language, set())

        score = 0
        # Skip the function node itself for nesting calculation
        self._cognitive_walk(func_node, language, nesting_types, decision_types, -1, score_ref=[0])
        return self._cognitive_walk(func_node, language, nesting_types, decision_types, -1, score_ref=[0])

    def _cognitive_walk(
        self, node: Node, language: str,
        nesting_types: set, decision_types: set,
        depth: int, score_ref: list[int]
    ) -> int:
        """Recursive walk computing cognitive complexity with nesting depth."""
        for child in node.children:
            is_nesting = child.type in nesting_types
            is_decision = child.type in decision_types

            current_depth = depth + 1 if is_nesting else depth

            if is_decision:
                # +1 for the decision itself + nesting level penalty
                score_ref[0] += 1 + max(current_depth, 0)

            self._cognitive_walk(child, language, nesting_types, decision_types, current_depth, score_ref)

        return score_ref[0]
