import ast
from typing import Any, Dict, List, Optional, Set

from .base_model import BaseModel, CodeLocation, CodeSymbol

class PythonModel(BaseModel):
    """Python-specific implementation of the code model.

    This class provides Python-specific implementations for symbol extraction,
    dependency analysis, and metrics calculation.
    """

    def extract_symbols(self, ast_node: ast.AST) -> List[CodeSymbol]:
        """Extract symbols from a Python AST.

        Args:
            ast_node: The Python AST to analyze.

        Returns:
            A list of CodeSymbol objects representing Python symbols.
        """
        symbols = []
        for node in ast.walk(ast_node):
            if isinstance(node, ast.FunctionDef):
                symbols.append(self._extract_function(node))
            elif isinstance(node, ast.ClassDef):
                symbols.append(self._extract_class(node))
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.append(self._extract_async_function(node))
        return symbols

    def analyze_dependencies(self, ast_node: ast.AST) -> Dict[str, List[str]]:
        """Analyze dependencies between Python symbols.

        Args:
            ast_node: The Python AST to analyze.

        Returns:
            A dictionary mapping symbol names to their dependencies.
        """
        deps = {}
        imports = set()

        # First pass: collect all imports
        for node in ast.walk(ast_node):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for name in node.names:
                    imports.add(f"{module}.{name.name}")

        # Second pass: analyze function and class dependencies
        for node in ast.walk(ast_node):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                deps[node.name] = self._analyze_function_deps(node, imports)
            elif isinstance(node, ast.ClassDef):
                deps[node.name] = self._analyze_class_deps(node, imports)

        return deps

    def calculate_metrics(self, ast_node: ast.AST) -> Dict[str, Any]:
        """Calculate Python code metrics.

        Args:
            ast_node: The Python AST to analyze.

        Returns:
            A dictionary of metric names to their values.
        """
        metrics = {
            'num_functions': 0,
            'num_classes': 0,
            'num_methods': 0,
            'num_imports': 0,
            'cyclomatic_complexity': 0,
            'max_nesting_depth': 0
        }

        for node in ast.walk(ast_node):
            if isinstance(node, ast.FunctionDef):
                metrics['num_functions'] += 1
            elif isinstance(node, ast.ClassDef):
                metrics['num_classes'] += 1
                metrics['num_methods'] += sum(
                    1 for n in ast.walk(node)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics['num_imports'] += len(node.names)

            # Calculate cyclomatic complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                metrics['cyclomatic_complexity'] += 1

        return metrics

    def validate_ast(self, ast_node: ast.AST) -> List[str]:
        """Validate a Python AST.

        Args:
            ast_node: The Python AST to validate.

        Returns:
            A list of validation error messages.
        """
        errors = []

        for node in ast.walk(ast_node):
            # Check for common issues
            if isinstance(node, ast.Try) and not node.handlers:
                errors.append(f"Empty try block at line {node.lineno}")
            elif isinstance(node, ast.ExceptHandler) and node.type is None:
                errors.append(f"Bare except clause at line {node.lineno}")
            elif isinstance(node, ast.Import):
                if any(n.asname == '*' for n in node.names):
                    errors.append(f"Star import at line {node.lineno}")

        return errors

    def _extract_function(self, node: ast.FunctionDef) -> CodeSymbol:
        """Extract information about a function definition."""
        return CodeSymbol(
            name=node.name,
            type='function',
            location=CodeLocation(
                filepath=getattr(node, 'filename', '<unknown>'),
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                start_col=node.col_offset,
                end_col=node.end_col_offset
            ),
            attributes={
                'args': [arg.arg for arg in node.args.args],
                'decorators': [ast.unparse(d) for d in node.decorator_list],
                'is_async': False
            }
        )

    def _extract_async_function(self, node: ast.AsyncFunctionDef) -> CodeSymbol:
        """Extract information about an async function definition."""
        symbol = self._extract_function(node)
        symbol.attributes['is_async'] = True
        return symbol

    def _extract_class(self, node: ast.ClassDef) -> CodeSymbol:
        """Extract information about a class definition."""
        return CodeSymbol(
            name=node.name,
            type='class',
            location=CodeLocation(
                filepath=getattr(node, 'filename', '<unknown>'),
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                start_col=node.col_offset,
                end_col=node.end_col_offset
            ),
            attributes={
                'bases': [ast.unparse(base) for base in node.bases],
                'decorators': [ast.unparse(d) for d in node.decorator_list],
                'methods': [
                    method.name for method in ast.walk(node)
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
            }
        )

    def _analyze_function_deps(self, node: ast.FunctionDef, imports: Set[str]) -> List[str]:
        """Analyze dependencies of a function."""
        deps = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in imports:
                deps.add(child.id)
            elif isinstance(child, ast.Attribute):
                # Handle attribute access (e.g., os.path)
                full_name = []
                current = child
                while isinstance(current, ast.Attribute):
                    full_name.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    full_name.append(current.id)
                    full_name.reverse()
                    full_path = '.'.join(full_name)
                    if any(full_path.startswith(imp) for imp in imports):
                        deps.add(full_path)
        return sorted(deps)

    def _analyze_class_deps(self, node: ast.ClassDef, imports: Set[str]) -> List[str]:
        """Analyze dependencies of a class."""
        deps = set()

        # Add base class dependencies
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in imports:
                deps.add(base.id)

        # Add dependencies from methods
        for child in ast.walk(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                deps.update(self._analyze_function_deps(child, imports))

        return sorted(deps)
