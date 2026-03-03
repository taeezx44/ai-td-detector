"""Unit tests for Complexity Analyzer."""

import pytest
from engine.parsers.tree_sitter_parser import parse_file, parse_code
from engine.analyzers.complexity import ComplexityAnalyzer


@pytest.fixture
def analyzer():
    return ComplexityAnalyzer()


# ─── Python Tests ────────────────────────────────────────────────────

class TestPythonComplexity:

    def test_simple_function(self, analyzer):
        """Simple function → CC = 1 (base only)."""
        code = '''
def greet(name):
    return f"Hello, {name}"
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.function_count == 1
        assert result.functions[0].cyclomatic == 1
        assert result.normalized_score < 0.1

    def test_if_else(self, analyzer):
        """Single if/else → CC = 2."""
        code = '''
def check(x):
    if x > 0:
        return "positive"
    else:
        return "non-positive"
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.functions[0].cyclomatic == 2

    def test_multiple_conditions(self, analyzer):
        """Multiple if/elif → CC = 4."""
        code = '''
def classify(x):
    if x > 100:
        return "high"
    elif x > 50:
        return "medium"
    elif x > 0:
        return "low"
    else:
        return "none"
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.functions[0].cyclomatic == 4

    def test_for_loop(self, analyzer):
        """For loop adds 1 to CC."""
        code = '''
def sum_list(items):
    total = 0
    for item in items:
        total += item
    return total
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.functions[0].cyclomatic == 2

    def test_nested_loops(self, analyzer):
        """Nested loops → higher cognitive complexity."""
        code = '''
def matrix_sum(matrix):
    total = 0
    for row in matrix:
        for cell in row:
            if cell > 0:
                total += cell
    return total
'''
        result = analyzer.analyze(parse_code(code, "python"))
        func = result.functions[0]
        assert func.cyclomatic >= 3
        assert func.cognitive > func.cyclomatic  # Nesting penalty

    def test_try_except(self, analyzer):
        """Except clause counts as decision point."""
        code = '''
def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return 0
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.functions[0].cyclomatic == 2

    def test_complex_ai_style_function(self, analyzer):
        """Simulated AI-generated complex function → high score."""
        code = '''
def process_data(data, config, options):
    result = []
    for item in data:
        if item.get("type") == "A":
            if item.get("status") == "active":
                for sub in item.get("children", []):
                    if sub.get("valid"):
                        if sub.get("score") > config.get("threshold", 0):
                            try:
                                processed = transform(sub)
                                result.append(processed)
                            except ValueError:
                                if options.get("strict"):
                                    raise
                                else:
                                    result.append(None)
        elif item.get("type") == "B":
            for sub in item.get("children", []):
                if sub.get("valid") and sub.get("score") > 0:
                    result.append(sub)
    return result
'''
        result = analyzer.analyze(parse_code(code, "python"))
        func = result.functions[0]
        assert func.cyclomatic >= 10
        assert result.normalized_score > 0.2  # Should flag as concerning

    def test_empty_file(self, analyzer):
        """Empty file → no functions → score 0."""
        result = analyzer.analyze(parse_code("", "python"))
        assert result.function_count == 0
        assert result.normalized_score == 0.0

    def test_multiple_functions(self, analyzer):
        """Multiple functions → aggregate metrics."""
        code = '''
def foo(x):
    if x:
        return 1
    return 0

def bar(x, y):
    for i in range(x):
        if i > y:
            return i
    return -1
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.function_count == 2
        assert result.total_cyclomatic >= 4


# ─── JavaScript Tests ────────────────────────────────────────────────

class TestJavaScriptComplexity:

    def test_simple_function(self, analyzer):
        """Simple JS function → CC = 1."""
        code = '''
function greet(name) {
    return `Hello, ${name}`;
}
'''
        result = analyzer.analyze(parse_code(code, "javascript"))
        assert result.function_count == 1
        assert result.functions[0].cyclomatic == 1

    def test_if_else_js(self, analyzer):
        """JS if/else → CC = 2."""
        code = '''
function check(x) {
    if (x > 0) {
        return "positive";
    } else {
        return "non-positive";
    }
}
'''
        result = analyzer.analyze(parse_code(code, "javascript"))
        assert result.functions[0].cyclomatic == 2

    def test_switch_case(self, analyzer):
        """Switch cases add to CC."""
        code = '''
function getDay(num) {
    switch(num) {
        case 1: return "Mon";
        case 2: return "Tue";
        case 3: return "Wed";
        default: return "Unknown";
    }
}
'''
        result = analyzer.analyze(parse_code(code, "javascript"))
        assert result.functions[0].cyclomatic >= 4
