"""Unit tests for Error Handling Analyzer."""

import pytest
from engine.parsers.tree_sitter_parser import parse_file, parse_code
from engine.analyzers.error_handling import ErrorHandlingAnalyzer


@pytest.fixture
def analyzer():
    return ErrorHandlingAnalyzer()


class TestPythonErrorHandling:

    def test_proper_error_handling(self, analyzer):
        """Function with specific exception handling → high coverage."""
        code = '''
def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except PermissionError:
        raise
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.functions_with_handling == 1
        assert result.functions[0].has_specific_except is True
        assert result.functions[0].has_bare_except is False
        assert result.normalized_score > 0.5  # Good handling

    def test_no_error_handling(self, analyzer):
        """Function without any try/except → low score."""
        code = '''
def read_file(path):
    with open(path, "r") as f:
        return f.read()
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.functions_with_handling == 0
        assert result.normalized_score < 0.5

    def test_bare_except(self, analyzer):
        """Bare except is detected and penalized."""
        code = '''
def risky_func():
    try:
        data = open("file.txt").read()
    except:
        pass
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.bare_except_count >= 1
        func = result.functions[0]
        assert func.has_bare_except is True

    def test_multiple_functions_mixed(self, analyzer):
        """Mix of handled and unhandled functions."""
        code = '''
def safe_func():
    try:
        result = open("data.json").read()
        return result
    except FileNotFoundError:
        return "{}"

def unsafe_func():
    data = open("data.json").read()
    return data

def another_safe():
    try:
        connect("db://localhost")
    except Exception as e:
        print(f"Connection failed: {e}")
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.total_functions == 3
        assert result.functions_with_handling == 2

    def test_empty_file(self, analyzer):
        """Empty file → neutral score."""
        result = analyzer.analyze(parse_code("", "python"))
        assert result.total_functions == 0
        assert result.normalized_score == 0.5


class TestJavaScriptErrorHandling:

    def test_try_catch(self, analyzer):
        """JS try/catch is detected."""
        code = '''
function fetchData(url) {
    try {
        const response = fetch(url);
        return response.json();
    } catch (error) {
        console.error("Fetch failed:", error);
        return null;
    }
}
'''
        result = analyzer.analyze(parse_code(code, "javascript"))
        assert result.functions_with_handling == 1
        assert result.functions[0].has_specific_except is True

    def test_no_try_catch(self, analyzer):
        """JS function without error handling."""
        code = '''
function fetchData(url) {
    const response = fetch(url);
    return response.json();
}
'''
        result = analyzer.analyze(parse_code(code, "javascript"))
        assert result.functions_with_handling == 0
