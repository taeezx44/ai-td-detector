"""
Error Handling Analyzer (Dimension E — Weight 25%)

Measures error handling coverage in functions.
Based on Perry et al. (2023): AI-generated code often lacks proper error handling,
increasing security vulnerabilities by 2x.

Evaluates: try/except coverage, bare except usage, error propagation patterns.
"""

from dataclasses import dataclass
from tree_sitter import Node

from engine.parsers.tree_sitter_parser import (
    ParseResult,
    find_functions,
    find_nodes_by_type,
    get_node_text,
    traverse_tree,
)


@dataclass
class FunctionErrorHandling:
    """Error handling assessment for a single function."""
    name: str
    start_line: int
    has_try_except: bool
    has_bare_except: bool
    has_specific_except: bool
    has_finally: bool
    risky_calls_count: int  # file I/O, network, etc.
    handled_calls_count: int
    coverage_ratio: float


@dataclass
class ErrorHandlingResult:
    """Aggregate error handling metrics for a file."""
    file_path: str
    language: str
    total_functions: int
    functions_with_handling: int
    bare_except_count: int
    total_try_blocks: int
    total_risky_calls: int
    handled_risky_calls: int
    coverage_ratio: float  # 0.0–1.0
    functions: list[FunctionErrorHandling]
    normalized_score: float = 0.0  # 0.0–1.0 (HIGHER = better handling)

    def __post_init__(self):
        self.normalized_score = self._normalize()

    def _normalize(self) -> float:
        """
        Normalize error handling QUALITY to 0.0–1.0 scale.
        HIGHER score = BETTER error handling.
        Note: In AI-TD formula, we use (1 - E) so higher handling = lower debt.
        Thresholds:
          - coverage ≥ 80% + no bare except → 1.0 (excellent)
          - coverage ≤ 10% → 0.0 (poor)
        """
        if self.total_functions == 0:
            return 0.5  # Neutral for files with no functions

        base_score = self.coverage_ratio

        # Penalty for bare except (bad practice)
        if self.bare_except_count > 0:
            penalty = min(self.bare_except_count * 0.1, 0.3)
            base_score = max(base_score - penalty, 0.0)

        return round(base_score, 4)


# Risky call patterns that should be wrapped in try/except
RISKY_PATTERNS = {
    "python": {
        "open", "read", "write", "connect", "request", "get", "post",
        "execute", "cursor", "load", "dump", "loads", "dumps",
        "urlopen", "fetch", "send", "recv", "close",
    },
    "javascript": {
        "fetch", "axios", "request", "readFile", "writeFile",
        "connect", "query", "execute", "parse", "stringify",
        "open", "send", "createElement",
    },
    "typescript": {
        "fetch", "axios", "request", "readFile", "writeFile",
        "connect", "query", "execute", "parse", "stringify",
        "open", "send", "createElement",
    },
}


class ErrorHandlingAnalyzer:
    """Analyzes error handling coverage from AST."""

    def analyze(self, parse_result: ParseResult) -> ErrorHandlingResult:
        """Analyze error handling in parsed file."""
        language = parse_result.language
        source = parse_result.content
        root = parse_result.root_node
        functions = find_functions(parse_result)

        func_results = []
        total_bare = 0
        total_try = 0
        total_risky = 0
        total_handled = 0
        funcs_with_handling = 0

        for func in functions:
            fr = self._analyze_function(func['node'], language, source)
            func_results.append(fr)
            if fr.has_try_except:
                funcs_with_handling += 1
            if fr.has_bare_except:
                total_bare += 1
            total_try += 1 if fr.has_try_except else 0
            total_risky += fr.risky_calls_count
            total_handled += fr.handled_calls_count

        coverage = funcs_with_handling / len(functions) if functions else 0.0

        return ErrorHandlingResult(
            file_path=parse_result.file_path,
            language=language,
            total_functions=len(functions),
            functions_with_handling=funcs_with_handling,
            bare_except_count=total_bare,
            total_try_blocks=total_try,
            total_risky_calls=total_risky,
            handled_risky_calls=total_handled,
            coverage_ratio=round(coverage, 4),
            functions=func_results,
        )

    def _analyze_function(self, func_node: Node, language: str, source: str) -> FunctionErrorHandling:
        """Analyze error handling for a single function."""
        name = self._get_name(func_node, source)

        # Find try blocks within this function
        try_type = "try_statement" if language == "python" else "try_statement"
        try_nodes = []
        
        def find_try_nodes(node):
            if node.type == try_type:
                try_nodes.append(node)
        
        traverse_tree(func_node, find_try_nodes)

        has_try = len(try_nodes) > 0
        has_bare = False
        has_specific = False
        has_finally = False

        for try_node in try_nodes:
            has_bare_local = False
            has_specific_local = False
            has_finally_local = False
            
            def check_except_clauses(node):
                nonlocal has_bare_local, has_specific_local, has_finally_local
                if language == "python":
                    if node.type == "except_clause":
                        # Check if it's bare except (no exception type specified)
                        if len(node.children) == 2:  # just 'except' + ':'
                            has_bare_local = True
                        else:
                            has_specific_local = True
                    elif node.type == "finally_clause":
                        has_finally_local = True
                else:  # JavaScript
                    if node.type == "catch_clause":
                        has_specific_local = True
                    elif node.type == "finally_clause":
                        has_finally_local = True
            
            traverse_tree(try_node, check_except_clauses)
            
            # Merge results
            has_bare = has_bare or has_bare_local
            has_specific = has_specific or has_specific_local
            has_finally = has_finally or has_finally_local

        # Count risky calls
        risky_patterns = RISKY_PATTERNS.get(language, set())
        risky_count, handled_count = self._count_risky_calls(
            func_node, try_nodes, language, source, risky_patterns
        )

        cov = handled_count / risky_count if risky_count > 0 else (1.0 if has_try else 0.0)

        return FunctionErrorHandling(
            name=name,
            start_line=func_node.start_point[0] + 1,
            has_try_except=has_try,
            has_bare_except=has_bare,
            has_specific_except=has_specific,
            has_finally=has_finally,
            risky_calls_count=risky_count,
            handled_calls_count=handled_count,
            coverage_ratio=round(cov, 4),
        )

    def _get_name(self, node: Node, source: str) -> str:
        for child in node.children:
            if child.type in ("identifier", "property_identifier"):
                return get_node_text(child, source)
        return "<anonymous>"

    def _count_risky_calls(
        self, func_node: Node, try_nodes: list[Node],
        language: str, source: str, patterns: set
    ) -> tuple[int, int]:
        """Count risky calls and how many are inside try blocks."""
        # Build set of byte ranges covered by try blocks
        try_ranges = set()
        for tn in try_nodes:
            for byte_pos in range(tn.start_byte, tn.end_byte):
                try_ranges.add(byte_pos)

        risky = 0
        handled = 0

        call_type = "call" if language == "python" else "call_expression"
        
        def count_calls(node):
            nonlocal risky, handled
            if node.type == call_type:
                call_text = get_node_text(node, source)
                func_name = call_text.split("(")[0].split(".")[-1].strip()
                
                if func_name in patterns:
                    risky += 1
                    # Check if this call is inside a try block
                    for try_node in try_nodes:
                        if (node.start_point[0] >= try_node.start_point[0] and 
                            node.end_point[0] <= try_node.end_point[0]):
                            handled += 1
                            break
        
        traverse_tree(func_node, count_calls)

        return risky, handled
