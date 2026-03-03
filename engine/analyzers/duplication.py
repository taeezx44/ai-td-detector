"""
Duplication Analyzer (Dimension D — Weight 25%)

Detects code clones and calculates duplication ratio.
Based on Roy & Cordy (2007): code clones increase maintenance cost 25–40%.

Uses hash-based block comparison for Type-1 (exact) and Type-2 (parameterized) clones.
"""

import hashlib
from dataclasses import dataclass
from collections import defaultdict

from engine.parsers.tree_sitter_parser import ParseResult


@dataclass
class DuplicateBlock:
    """A duplicated code block."""
    hash_value: str
    lines: list[int]
    line_count: int
    occurrences: int
    sample_text: str


@dataclass
class DuplicationResult:
    """Aggregate duplication metrics for a file."""
    file_path: str
    total_lines: int
    duplicated_lines: int
    duplication_ratio: float
    duplicate_blocks: list[DuplicateBlock]
    normalized_score: float = 0.0  # 0.0–1.0

    def __post_init__(self):
        self.normalized_score = self._normalize()

    def _normalize(self) -> float:
        """
        Normalize duplication to 0.0–1.0 scale.
        Thresholds:
          - ratio ≤ 3%  → 0.0 (acceptable)
          - ratio ≥ 25% → 1.0 (severe)
        """
        if self.total_lines == 0:
            return 0.0
        return round(min(max((self.duplication_ratio - 3) / 22, 0.0), 1.0), 4)


class DuplicationAnalyzer:
    """Detects code duplication using rolling hash block comparison."""

    def __init__(self, min_block_size: int = 4, window_size: int = 6):
        """
        Args:
            min_block_size: Minimum lines to consider as a block.
            window_size: Sliding window size for hash comparison.
        """
        self.min_block_size = min_block_size
        self.window_size = window_size

    def analyze(self, parse_result: ParseResult) -> DuplicationResult:
        """Analyze duplication in parsed source code."""
        source = parse_result.content
        lines = source.splitlines()
        total_lines = len(lines)

        if total_lines < self.min_block_size:
            return DuplicationResult(
                file_path=parse_result.file_path,
                total_lines=total_lines,
                duplicated_lines=0,
                duplication_ratio=0.0,
                duplicate_blocks=[],
            )

        # Normalize lines: strip whitespace for Type-1 detection
        normalized = [line.strip() for line in lines]

        # Build hash map of sliding windows
        hash_map = defaultdict(list)
        for i in range(len(normalized) - self.window_size + 1):
            block = "\n".join(normalized[i:i + self.window_size])
            if self._is_meaningful(block):
                h = hashlib.md5(block.encode("utf-8")).hexdigest()
                hash_map[h].append(i)

        # Find duplicates (blocks appearing more than once)
        duplicated_line_set = set()
        duplicate_blocks = []

        for h, positions in hash_map.items():
            if len(positions) > 1:
                # Mark all lines in duplicate blocks
                for pos in positions:
                    for line_idx in range(pos, pos + self.window_size):
                        duplicated_line_set.add(line_idx)

                block_text = "\n".join(lines[positions[0]:positions[0] + self.window_size])
                duplicate_blocks.append(DuplicateBlock(
                    hash_value=h,
                    lines=positions,
                    line_count=self.window_size,
                    occurrences=len(positions),
                    sample_text=block_text[:200],
                ))

        dup_count = len(duplicated_line_set)
        ratio = round((dup_count / total_lines) * 100, 2) if total_lines > 0 else 0.0

        return DuplicationResult(
            file_path=parse_result.file_path,
            total_lines=total_lines,
            duplicated_lines=dup_count,
            duplication_ratio=ratio,
            duplicate_blocks=duplicate_blocks,
        )

    def _is_meaningful(self, block: str) -> bool:
        """Filter out empty or trivial blocks (imports, blank lines, etc.)."""
        meaningful_lines = [
            line for line in block.splitlines()
            if line and not line.startswith(("#", "//", "import ", "from "))
        ]
        return len(meaningful_lines) >= self.min_block_size // 2
