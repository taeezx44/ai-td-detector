"""
Documentation Analyzer (Dimension Doc — Weight 20%)

Measures docstring/comment coverage relative to functions and classes.
Based on Aghajani et al. (2020): documentation affects onboarding and maintainability.
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
class DocCoverage:
    """Documentation coverage for a single entity."""
    name: str
    entity_type: str  # "function", "class", "module"
    has_docstring: bool
    start_line: int


@dataclass
class DocumentationResult:
    """Aggregate documentation metrics for a file."""
    file_path: str
    language: str
    total_functions: int
    documented_functions: int
    total_classes: int
    documented_classes: int
    has_module_docstring: bool
    comment_line_count: int
    total_lines: int
    doc_coverage_ratio: float  # 0.0–1.0
    comment_density: float  # comments per LOC
    entities: list[DocCoverage]
    normalized_score: float = 0.0  # 0.0–1.0

    def __post_init__(self):
        self.normalized_score = self._normalize()

    def _normalize(self) -> float:
        """
        Normalize documentation DEFICIT to 0.0–1.0 scale.
        Lower coverage → higher debt score.
        Thresholds:
          - coverage ≥ 80% → 0.0 (good)
          - coverage ≤ 10% → 1.0 (severe)
        """
        deficit = 1.0 - self.doc_coverage_ratio
        return round(min(max((deficit - 0.2) / 0.7, 0.0), 1.0), 4)


class DocumentationAnalyzer:
    """Analyzes documentation coverage from AST."""

    def analyze(self, parse_result: ParseResult) -> DocumentationResult:
        """Analyze documentation coverage in parsed file."""
        language = parse_result.language
        source = parse_result.content
        root = parse_result.root_node

        entities = []

        # Check module-level docstring
        has_module_doc = self._check_module_docstring(root, language, source)

        # Check function docstrings
        functions = find_functions(parse_result)
        documented_funcs = 0
        for func in functions:
            name = self._get_name(func['node'], source)
            has_doc = self._check_function_docstring(func['node'], language, source)
            if has_doc:
                documented_funcs += 1
            entities.append(DocCoverage(
                name=name,
                entity_type="function",
                has_docstring=has_doc,
                start_line=func['start_line'],
            ))

        # Check class docstrings
        classes = find_nodes_by_type(parse_result, "class_definition" if language == "python" else "class_declaration")
        documented_classes = 0
        for cls in classes:
            name = self._get_name(cls, source)
            has_doc = self._check_class_docstring(cls, language, source)
            if has_doc:
                documented_classes += 1
            entities.append(DocCoverage(
                name=name,
                entity_type="class",
                has_docstring=has_doc,
                start_line=cls.start_point[0] + 1,
            ))

        # Count comment lines
        comment_lines = self._count_comment_lines(root, language)
        total_lines = parse_result.line_count

        # Calculate coverage ratio
        total_entities = len(functions) + len(classes) + (1 if total_lines > 0 else 0)
        documented = documented_funcs + documented_classes + (1 if has_module_doc else 0)
        coverage = documented / total_entities if total_entities > 0 else 1.0

        return DocumentationResult(
            file_path=parse_result.file_path,
            language=language,
            total_functions=len(functions),
            documented_functions=documented_funcs,
            total_classes=len(classes),
            documented_classes=documented_classes,
            has_module_docstring=has_module_doc,
            comment_line_count=comment_lines,
            total_lines=total_lines,
            doc_coverage_ratio=round(coverage, 4),
            comment_density=round(comment_lines / total_lines, 4) if total_lines > 0 else 0.0,
            entities=entities,
        )

    def _get_name(self, node: Node, source: str) -> str:
        """Get entity name from AST node."""
        for child in node.children:
            if child.type in ("identifier", "property_identifier"):
                return get_node_text(child, source)
        return "<anonymous>"

    def _check_module_docstring(self, root: Node, language: str, source: str) -> bool:
        """Check if file has a module-level docstring."""
        if language == "python":
            for child in root.children:
                if child.type == "comment":
                    continue
                if child.type == "expression_statement":
                    for sub in child.children:
                        if sub.type == "string":
                            text = get_node_text(sub, source)
                            if text.startswith(('"""', "'''")):
                                return True
                break
        else:
            # JS/TS: check for leading block comment
            for child in root.children:
                if child.type == "comment":
                    text = get_node_text(child, source)
                    if text.startswith("/**") or text.startswith("/*"):
                        return True
                elif child.type != "comment":
                    break
        return False

    def _check_function_docstring(self, func_node: Node, language: str, source: str) -> bool:
        """Check if function has a docstring."""
        if language == "python":
            return self._check_python_docstring(func_node, source)
        else:
            return self._check_jsdoc(func_node, source)

    def _check_class_docstring(self, cls_node: Node, language: str, source: str) -> bool:
        """Check if class has a docstring."""
        if language == "python":
            return self._check_python_docstring(cls_node, source)
        else:
            return self._check_jsdoc(cls_node, source)

    def _check_python_docstring(self, node: Node, source: str) -> bool:
        """Check for Python triple-quoted docstring as first statement in body."""
        body = None
        for child in node.children:
            if child.type == "block":
                body = child
                break
        if body is None:
            return False

        for child in body.children:
            if child.type == "comment":
                continue
            if child.type == "expression_statement":
                for sub in child.children:
                    if sub.type == "string":
                        text = get_node_text(sub, source)
                        if text.startswith(('"""', "'''")):
                            return True
            break
        return False

    def _check_jsdoc(self, node: Node, source: str) -> bool:
        """Check for JSDoc comment preceding the node."""
        prev = node.prev_sibling
        if prev and prev.type == "comment":
            text = get_node_text(prev, source)
            return text.strip().startswith("/**")
        return False

    def _count_comment_lines(self, root: Node, language: str) -> int:
        """Count total comment lines in the file."""
        count = 0
        
        def count_comments(node):
            nonlocal count
            if node.type == "comment":
                count += node.end_point[0] - node.start_point[0] + 1
        
        traverse_tree(root, count_comments)
        return count
