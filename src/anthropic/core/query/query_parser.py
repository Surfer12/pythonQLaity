from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class Query:
    """Represents a parsed and validated query.

    Attributes:
        type: The type of query (e.g., 'ast_pattern', 'metrics', 'security').
        pattern: The query pattern to match against the code.
        options: Additional options for query execution.
    """
    type: str
    pattern: Any
    options: Optional[Dict[str, Any]] = None

class QueryParser:
    """Parser for Code Sentinel queries.

    This class handles parsing and validation of queries used to analyze code.
    It supports different query types and ensures queries are well-formed
    before execution.
    """

    VALID_QUERY_TYPES = {'ast_pattern', 'metrics', 'security'}

    def parse(self, query_str: str) -> Query:
        """Parse a query string into a structured Query object.

        Args:
            query_str: The query string to parse.

        Returns:
            A validated Query object.

        Raises:
            ValueError: If the query is malformed or invalid.
        """
        # Basic validation
        if not query_str or not isinstance(query_str, str):
            raise ValueError("Query must be a non-empty string")

        # Split into type and pattern
        try:
            query_type, pattern = query_str.split(':', 1)
        except ValueError:
            raise ValueError(
                "Query must be in format 'type:pattern' (e.g., 'ast_pattern:FunctionDef')"
            )

        # Validate query type
        query_type = query_type.strip().lower()
        if query_type not in self.VALID_QUERY_TYPES:
            raise ValueError(
                f"Invalid query type '{query_type}'. Must be one of: {self.VALID_QUERY_TYPES}"
            )

        # Parse pattern based on query type
        parsed_pattern = self._parse_pattern(query_type, pattern.strip())

        return Query(type=query_type, pattern=parsed_pattern)

    def _parse_pattern(self, query_type: str, pattern: str) -> Any:
        """Parse the pattern portion of the query based on its type.

        Args:
            query_type: The type of query being parsed.
            pattern: The pattern string to parse.

        Returns:
            The parsed pattern in an appropriate format for the query type.

        Raises:
            ValueError: If the pattern is invalid for the query type.
        """
        if query_type == 'ast_pattern':
            return self._parse_ast_pattern(pattern)
        elif query_type == 'metrics':
            return self._parse_metrics_pattern(pattern)
        elif query_type == 'security':
            return self._parse_security_pattern(pattern)
        else:
            raise ValueError(f"Unsupported query type: {query_type}")

    def _parse_ast_pattern(self, pattern: str) -> str:
        """Parse an AST pattern query.

        Args:
            pattern: The AST pattern string.

        Returns:
            The validated AST pattern.

        Raises:
            ValueError: If the pattern is invalid.
        """
        # For now, just validate it's not empty
        if not pattern:
            raise ValueError("AST pattern cannot be empty")
        return pattern

    def _parse_metrics_pattern(self, pattern: str) -> str:
        """Parse a metrics query pattern.

        Args:
            pattern: The metrics pattern string.

        Returns:
            The validated metrics pattern.

        Raises:
            ValueError: If the pattern is invalid.
        """
        # For now, just validate it's not empty
        if not pattern:
            raise ValueError("Metrics pattern cannot be empty")
        return pattern

    def _parse_security_pattern(self, pattern: str) -> str:
        """Parse a security query pattern.

        Args:
            pattern: The security pattern string.

        Returns:
            The validated security pattern.

        Raises:
            ValueError: If the pattern is invalid.
        """
        # For now, just validate it's not empty
        if not pattern:
            raise ValueError("Security pattern cannot be empty")
        return pattern
