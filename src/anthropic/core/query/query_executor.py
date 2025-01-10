import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Union

from .query_parser import Query

@dataclass
class QueryResult:
    """Represents a single result from a query execution.

    Attributes:
        filepath: Path to the file containing the match.
        line_number: Line number where the match was found.
        match_type: Type of match (e.g., 'ast_node', 'metric', 'security_issue').
        match_value: The actual matched value or node.
        context: Additional context about the match.
    """
    filepath: Path
    line_number: int
    match_type: str
    match_value: Any
    context: Optional[str] = None

class QueryExecutor:
    """Executes queries against ASTs and other code representations.

    This class handles the execution of different types of queries,
    including AST pattern matching, metrics calculation, and security checks.
    """

    def execute(self, ast_node: ast.AST, query: Query, filepath: Path) -> List[QueryResult]:
        """Execute a query against an AST.

        Args:
            ast_node: The AST to query.
            query: The query to execute.
            filepath: Path to the source file (for result reporting).

        Returns:
            A list of QueryResult objects representing matches.

        Raises:
            ValueError: If the query type is unsupported or execution fails.
        """
        if query.type == 'ast_pattern':
            return self._execute_ast_pattern(ast_node, query.pattern, filepath)
        elif query.type == 'metrics':
            return self._execute_metrics(ast_node, query.pattern, filepath)
        elif query.type == 'security':
            return self._execute_security(ast_node, query.pattern, filepath)
        else:
            raise ValueError(f"Unsupported query type: {query.type}")

    def _execute_ast_pattern(
        self, node: ast.AST, pattern: str, filepath: Path
    ) -> List[QueryResult]:
        """Execute an AST pattern matching query.

        Args:
            node: The AST node to search.
            pattern: The pattern to match.
            filepath: Path to the source file.

        Returns:
            List of matching nodes as QueryResults.
        """
        results = []
        for child in ast.walk(node):
            if isinstance(child, getattr(ast, pattern, None)):
                results.append(
                    QueryResult(
                        filepath=filepath,
                        line_number=getattr(child, 'lineno', 0),
                        match_type='ast_node',
                        match_value=child,
                        context=self._get_node_context(child)
                    )
                )
        return results

    def _execute_metrics(
        self, node: ast.AST, pattern: str, filepath: Path
    ) -> List[QueryResult]:
        """Execute a metrics calculation query.

        Args:
            node: The AST node to analyze.
            pattern: The metrics pattern to calculate.
            filepath: Path to the source file.

        Returns:
            List of metric results as QueryResults.
        """
        # Basic implementation - count specific node types
        if pattern.startswith('count:'):
            node_type = pattern.split(':', 1)[1]
            count = sum(1 for n in ast.walk(node) if isinstance(n, getattr(ast, node_type, None)))
            return [
                QueryResult(
                    filepath=filepath,
                    line_number=0,  # Metrics are file-wide
                    match_type='metric',
                    match_value=count,
                    context=f"Count of {node_type} nodes"
                )
            ]
        return []

    def _execute_security(
        self, node: ast.AST, pattern: str, filepath: Path
    ) -> List[QueryResult]:
        """Execute a security check query.

        Args:
            node: The AST node to check.
            pattern: The security pattern to check.
            filepath: Path to the source file.

        Returns:
            List of security issues as QueryResults.
        """
        # Basic implementation - check for potentially dangerous functions
        results = []
        if pattern == 'dangerous_calls':
            dangerous_functions = {'eval', 'exec', 'os.system', 'subprocess.call'}
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call) and
                    isinstance(child.func, ast.Name) and
                    child.func.id in dangerous_functions
                ):
                    results.append(
                        QueryResult(
                            filepath=filepath,
                            line_number=child.lineno,
                            match_type='security_issue',
                            match_value=child,
                            context=f"Potentially dangerous function call: {child.func.id}"
                        )
                    )
        return results

    def _get_node_context(self, node: ast.AST) -> Optional[str]:
        """Get a string representation of an AST node for context.

        Args:
            node: The AST node.

        Returns:
            A string representation of the node, or None if not available.
        """
        try:
            return ast.unparse(node)
        except Exception:
            return None
