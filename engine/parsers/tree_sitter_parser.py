"""
Tree-sitter based code parser for AI-TD Detector

Supports multiple programming languages and provides AST-based analysis.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Tree-sitter imports
try:
    import tree_sitter
except ImportError:
    print("Warning: tree_sitter not installed. Some features may not work.")
    tree_sitter = None

# Language mappings
SUPPORTED_LANGUAGES = {
    '.py': 'python',
    '.js': 'javascript', 
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
}

# Language parser mappings
LANGUAGE_PARSERS = {
    'python': 'tree_sitter_python',
    'javascript': 'tree_sitter_javascript',
    'typescript': 'tree_sitter_typescript',
    'java': 'tree_sitter_java',
    'c': 'tree_sitter_c',
    'cpp': 'tree_sitter_cpp',
    'go': 'tree_sitter_go',
    'rust': 'tree_sitter_rust',
    'ruby': 'tree_sitter_ruby',
    'php': 'tree_sitter_php',
}


class ParseResult:
    """Result of parsing a file."""
    
    def __init__(self, file_path: str, language: str, tree: Any, content: str):
        self.file_path = file_path
        self.language = language
        self.tree = tree
        self.content = content
        self.root_node = tree.root_node if tree else None
    
    @property
    def lines(self) -> List[str]:
        """Get lines of code."""
        return self.content.splitlines()
    
    @property
    def line_count(self) -> int:
        """Get number of lines."""
        return len(self.lines)


def detect_language(file_path: str) -> Optional[str]:
    """
    Detect programming language from file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language string or None if unsupported
    """
    ext = Path(file_path).suffix.lower()
    return SUPPORTED_LANGUAGES.get(ext)


def get_parser(language: str) -> Optional[Any]:
    """
    Get tree-sitter parser for a language.
    
    Args:
        language: Programming language
        
    Returns:
        Parser instance or None if not available
    """
    if not tree_sitter:
        return None
    
    try:
        parser_module_name = LANGUAGE_PARSERS.get(language)
        if not parser_module_name:
            return None
        
        # Try to import the language module
        parser_module = sys.modules.get(parser_module_name)
        if not parser_module:
            try:
                exec(f"import {parser_module_name}")
                parser_module = sys.modules[parser_module_name]
            except ImportError:
                print(f"Warning: {parser_module_name} not available")
                return None
        
        # Get the language object
        language_obj = getattr(parser_module, 'language()', None) or getattr(parser_module, 'language', None)
        if callable(language_obj):
            language_obj = language_obj()
        
        if not language_obj:
            return None
        
        # Convert PyCapsule to Language object if needed
        if hasattr(language_obj, '__class__') and language_obj.__class__.__name__ == 'PyCapsule':
            language_obj = tree_sitter.Language(language_obj)
        
        # Create parser
        parser = tree_sitter.Parser()
        parser.language = language_obj
        return parser
        
    except Exception as e:
        print(f"Error creating parser for {language}: {e}")
        return None


def parse_code(code: str, language: str) -> Optional[ParseResult]:
    """
    Parse code from string (for testing).
    
    Args:
        code: Source code string
        language: Programming language
        
    Returns:
        ParseResult or None if parsing fails
    """
    if not tree_sitter:
        return None
    
    try:
        parser = get_parser(language)
        if not parser:
            return None
        
        # Parse the code
        tree = parser.parse(bytes(code, 'utf8'))
        
        return ParseResult(
            file_path="<string>",
            language=language,
            tree=tree,
            content=code
        )
    except Exception as e:
        print(f"Error parsing code: {e}")
        return None


def parse_file(file_path: str) -> Optional[ParseResult]:
    """
    Parse a source code file.
    
    Args:
        file_path: Path to the file to parse
        
    Returns:
        ParseResult or None if parsing fails
    """
    try:
        # Detect language
        language = detect_language(file_path)
        if not language:
            return None
        
        # Read file content with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        if not content.strip():
            return None
        
        # Get parser
        parser = get_parser(language)
        if not parser:
            # Fallback: create a basic parse result without tree
            return ParseResult(file_path, language, None, content)
        
        # Parse the content
        tree = parser.parse(bytes(content, 'utf-8'))
        
        return ParseResult(file_path, language, tree, content)
        
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None


def traverse_tree(node: Any, callback) -> None:
    """
    Traverse tree-sitter AST and call callback for each node.
    
    Args:
        node: Tree-sitter node
        callback: Function to call for each node
    """
    if not node:
        return
    
    callback(node)
    
    for child in node.children:
        traverse_tree(child, callback)


def get_functions(result: ParseResult) -> List[Dict]:
    """Extract function definitions from parse result."""
    functions = []
    
    if not result.tree:
        return functions
    
    def visit_node(node):
        if node.type == 'function_definition' or node.type == 'function_declaration':
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Try to extract function name
            name = "unnamed"
            for child in node.children:
                if child.type == 'identifier':
                    name = result.lines[child.start_point[0]][child.start_point[0]:child.end_point[0]]
                    break
            
            functions.append({
                'name': name,
                'start_line': start_line,
                'end_line': end_line,
                'line_count': end_line - start_line + 1,
                'node': node
            })
    
    traverse_tree(result.root_node, visit_node)
    return functions


def get_classes(result: ParseResult) -> List[Dict]:
    """Extract class definitions from parse result."""
    classes = []
    
    if not result.tree:
        return classes
    
    def visit_node(node):
        if node.type == 'class_definition':
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Try to extract class name
            name = "unnamed"
            for child in node.children:
                if child.type == 'identifier':
                    name = result.lines[child.start_point[0]][child.start_point[0]:child.end_point[0]]
                    break
            
            classes.append({
                'name': name,
                'start_line': start_line,
                'end_line': end_line,
                'line_count': end_line - start_line + 1,
                'node': node
            })
    
    traverse_tree(result.root_node, visit_node)
    return classes


def get_imports(result: ParseResult) -> List[Dict]:
    """Extract import statements from parse result."""
    imports = []
    
    if not result.tree:
        return imports
    
    def visit_node(node):
        if node.type in ['import_statement', 'import_from_statement', 'import']:
            start_line = node.start_point[0] + 1
            
            # Extract import text
            import_text = result.lines[start_line - 1].strip()
            
            imports.append({
                'text': import_text,
                'line': start_line,
                'node': node
            })
    
    traverse_tree(result.root_node, visit_node)
    return imports


def get_comments(result: ParseResult) -> List[Dict]:
    """Extract comments from parse result."""
    comments = []
    
    # Simple regex-based comment extraction as fallback
    import re
    
    lines = result.lines
    for i, line in enumerate(lines):
        # Python-style comments
        if '#' in line:
            comment_start = line.find('#')
            comment_text = line[comment_start:].strip()
            if comment_text:
                comments.append({
                    'text': comment_text,
                    'line': i + 1,
                    'type': 'line_comment'
                })
        
        # C-style comments (simplified)
        elif '//' in line:
            comment_start = line.find('//')
            comment_text = line[comment_start:].strip()
            if comment_text:
                comments.append({
                    'text': comment_text,
                    'line': i + 1,
                    'type': 'line_comment'
                })
    
    return comments


def find_nodes_by_type(result: ParseResult, node_type: str) -> List[Any]:
    """Find all nodes of a specific type."""
    nodes = []
    
    if not result.tree:
        return nodes
    
    def visit_node(node):
        if node.type == node_type:
            nodes.append(node)
    
    traverse_tree(result.root_node, visit_node)
    return nodes


def get_node_text(node: Any, content: str) -> str:
    """Get text content of a node."""
    if not node:
        return ""
    
    start_byte = node.start_byte
    end_byte = node.end_byte
    return content[start_byte:end_byte]


def walk_tree(node: Any, callback) -> None:
    """Alias for traverse_tree function."""
    traverse_tree(node, callback)


def find_functions(result: ParseResult) -> List[Dict]:
    """Alias for get_functions function."""
    return get_functions(result)


def get_complexity_metrics(result: ParseResult) -> Dict:
    """Calculate basic complexity metrics."""
    metrics = {
        'line_count': result.line_count,
        'function_count': 0,
        'class_count': 0,
        'import_count': 0,
        'comment_count': 0,
        'max_function_length': 0,
        'max_class_length': 0,
    }
    
    if result.tree:
        functions = get_functions(result)
        classes = get_classes(result)
        imports = get_imports(result)
        comments = get_comments(result)
        
        metrics.update({
            'function_count': len(functions),
            'class_count': len(classes),
            'import_count': len(imports),
            'comment_count': len(comments),
            'max_function_length': max([f['line_count'] for f in functions], default=0),
            'max_class_length': max([c['line_count'] for c in classes], default=0),
        })
    
    return metrics


if __name__ == "__main__":
    # Test the parser
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = parse_file(file_path)
        
        if result:
            print(f"Parsed {file_path} ({result.language})")
            print(f"Lines: {result.line_count}")
            
            metrics = get_complexity_metrics(result)
            print("Metrics:", metrics)
        else:
            print(f"Failed to parse {file_path}")
    else:
        print("Usage: python tree_sitter_parser.py <file_path>")
