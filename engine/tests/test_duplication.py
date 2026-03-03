"""Unit tests for Duplication Analyzer."""

import pytest
from engine.parsers.tree_sitter_parser import parse_file, parse_code
from engine.analyzers.duplication import DuplicationAnalyzer


@pytest.fixture
def analyzer():
    return DuplicationAnalyzer(min_block_size=4, window_size=4)


class TestDuplication:

    def test_no_duplication(self, analyzer):
        """Unique code → 0% duplication."""
        code = '''
def foo():
    x = 1
    y = 2
    z = x + y
    return z

def bar():
    a = "hello"
    b = "world"
    c = a + " " + b
    return c
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.duplication_ratio < 5.0
        assert result.normalized_score < 0.2

    def test_obvious_duplication(self, analyzer):
        """Copy-pasted blocks → detected as duplicates."""
        code = '''
def process_a(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

def process_b(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

def process_c(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
'''
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.duplicated_lines > 0
        assert len(result.duplicate_blocks) > 0

    def test_empty_file(self, analyzer):
        """Empty file → no duplication."""
        result = analyzer.analyze(parse_code("", "python"))
        assert result.duplication_ratio == 0.0
        assert result.normalized_score == 0.0

    def test_short_file(self, analyzer):
        """File shorter than block size → no duplication."""
        code = "x = 1\ny = 2"
        result = analyzer.analyze(parse_code(code, "python"))
        assert result.duplication_ratio == 0.0
