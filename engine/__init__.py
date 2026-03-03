"""
AI-TD Detector Engine

Main engine components for analyzing AI-induced technical debt.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.parsers.tree_sitter_parser import parse_file, detect_language
from engine.analyzers.complexity import ComplexityAnalyzer
from engine.analyzers.duplication import DuplicationAnalyzer
from engine.analyzers.documentation import DocumentationAnalyzer
from engine.analyzers.error_handling import ErrorHandlingAnalyzer
from engine.scoring.ai_td_score import AITDScoreCalculator


class AITDDetector:
    """Main AI-TD Detector engine for analyzing code."""
    
    def __init__(self, weights: Optional[Dict] = None):
        """Initialize the detector with optional custom weights."""
        self.calculator = AITDScoreCalculator(weights=weights)
        self.complexity_analyzer = ComplexityAnalyzer()
        self.duplication_analyzer = DuplicationAnalyzer()
        self.documentation_analyzer = DocumentationAnalyzer()
        self.error_handling_analyzer = ErrorHandlingAnalyzer()
    
    def analyze_code(self, content: str, language: str) -> Optional[Dict]:
        """
        Analyze code content for AI-induced technical debt.
        
        Args:
            content: Source code content
            language: Programming language
            
        Returns:
            Analysis results dictionary or None if analysis fails
        """
        try:
            print(f"Analyzing {language} code ({len(content)} chars)...")
            
            # Create temporary file for parsing
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Parse the file
                parse_result = parse_file(temp_path)
                if not parse_result:
                    print("Parse result is None, using fallback analysis")
                    return self._fallback_analysis(content, language)
                
                # Run all analyzers
                try:
                    complexity = self.complexity_analyzer.analyze(parse_result)
                except Exception as e:
                    print(f"Complexity analysis failed: {e}")
                    complexity = self._fallback_complexity(content)
                
                try:
                    duplication = self.duplication_analyzer.analyze(parse_result)
                except Exception as e:
                    print(f"Duplication analysis failed: {e}")
                    duplication = self._fallback_duplication(content)
                
                try:
                    documentation = self.documentation_analyzer.analyze(parse_result)
                except Exception as e:
                    print(f"Documentation analysis failed: {e}")
                    documentation = self._fallback_documentation(content)
                
                try:
                    error_handling = self.error_handling_analyzer.analyze(parse_result)
                except Exception as e:
                    print(f"Error handling analysis failed: {e}")
                    error_handling = self._fallback_error_handling(content)
                
                # Calculate AI-TD score
                score = self.calculator.calculate(complexity, duplication, documentation, error_handling)
                
                result = {
                    'ai_td_score': score.total_score,
                    'complexity_score': complexity.score,
                    'duplication_score': duplication.score,
                    'documentation_score': documentation.score,
                    'error_handling_score': error_handling.score,
                    'severity': score.severity,
                    'file_size': len(content),
                    'details': {
                        'complexity': complexity.to_dict(),
                        'duplication': duplication.to_dict(),
                        'documentation': documentation.to_dict(),
                        'error_handling': error_handling.to_dict(),
                        'ai_td_score': score.to_dict()
                    }
                }
                
                print(f"Analysis successful: AI-TD score = {score.total_score:.3f}")
                return result
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error analyzing code: {e}")
            return self._fallback_analysis(content, language)
    
    def _fallback_analysis(self, content: str, language: str) -> Dict:
        """Fallback analysis when tree-sitter parsing fails."""
        print(f"Using fallback analysis for {language}")
        
        # Simple heuristic-based analysis
        lines = content.splitlines()
        line_count = len(lines)
        
        # Basic complexity metrics
        complexity_score = min(0.8, line_count / 1000)  # Scale with file size
        duplication_score = 0.2  # Default low duplication
        documentation_score = 0.5  # Default medium documentation
        error_handling_score = 0.3  # Default low error handling
        
        # Calculate AI-TD score
        ai_td_score = (complexity_score + duplication_score + documentation_score + error_handling_score) / 4
        
        return {
            'ai_td_score': ai_td_score,
            'complexity_score': complexity_score,
            'duplication_score': duplication_score,
            'documentation_score': documentation_score,
            'error_handling_score': error_handling_score,
            'severity': 'LOW' if ai_td_score < 0.4 else 'MEDIUM' if ai_td_score < 0.7 else 'HIGH',
            'file_size': len(content)
        }
    
    def _fallback_complexity(self, content: str):
        """Fallback complexity analysis."""
        from dataclasses import dataclass
        
        @dataclass
        class SimpleComplexity:
            score: float = 0.3
            
            def to_dict(self):
                return {'score': self.score}
        
        return SimpleComplexity(score=min(0.8, len(content.splitlines()) / 1000))
    
    def _fallback_duplication(self, content: str):
        """Fallback duplication analysis."""
        from dataclasses import dataclass
        
        @dataclass
        class SimpleDuplication:
            score: float = 0.2
            
            def to_dict(self):
                return {'score': self.score}
        
        return SimpleDuplication(score=0.2)
    
    def _fallback_documentation(self, content: str):
        """Fallback documentation analysis."""
        from dataclasses import dataclass
        
        @dataclass
        class SimpleDocumentation:
            score: float = 0.5
            
            def to_dict(self):
                return {'score': self.score}
        
        return SimpleDocumentation(score=0.5)
    
    def _fallback_error_handling(self, content: str):
        """Fallback error handling analysis."""
        from dataclasses import dataclass
        
        @dataclass
        class SimpleErrorHandling:
            score: float = 0.3
            
            def to_dict(self):
                return {'score': self.score}
        
        return SimpleErrorHandling(score=0.3)