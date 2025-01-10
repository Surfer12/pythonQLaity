from typing import Dict, Optional, Set

from .query_parser import Query

class QueryOptimizer:
    """Optimizes queries for more efficient execution.

    This class analyzes queries and applies optimizations to improve
    their execution performance. It can rewrite patterns, add caching
    hints, and suggest execution strategies.
    """

    # Node types that are typically more expensive to process
    EXPENSIVE_NODES = {
        'FunctionDef',
        'ClassDef',
        'AsyncFunctionDef',
        'For',
        'While',
        'If',
        'Try'
    }

    # Node types that are good candidates for caching
    CACHEABLE_NODES = {
        'Import',
        'ImportFrom',
        'ClassDef',
        'FunctionDef'
    }

    def optimize(self, query: Query) -> Query:
        """Optimize a query for better performance.

        Args:
            query: The query to optimize.

        Returns:
            An optimized version of the query.
        """
        if query.type == 'ast_pattern':
            return self._optimize_ast_pattern(query)
        elif query.type == 'metrics':
            return self._optimize_metrics(query)
        elif query.type == 'security':
            return self._optimize_security(query)
        return query

    def _optimize_ast_pattern(self, query: Query) -> Query:
        """Optimize an AST pattern matching query.

        Args:
            query: The AST pattern query to optimize.

        Returns:
            An optimized version of the query.
        """
        pattern = query.pattern
        options = dict(query.options or {})

        # Add caching hint if the pattern matches cacheable nodes
        if pattern in self.CACHEABLE_NODES:
            options['use_cache'] = True

        # Add traversal hint for expensive nodes
        if pattern in self.EXPENSIVE_NODES:
            options['traversal'] = 'bottom_up'

        return Query(
            type=query.type,
            pattern=pattern,
            options=options
        )

    def _optimize_metrics(self, query: Query) -> Query:
        """Optimize a metrics calculation query.

        Args:
            query: The metrics query to optimize.

        Returns:
            An optimized version of the query.
        """
        pattern = query.pattern
        options = dict(query.options or {})

        # For count queries, add parallel processing hint if counting expensive nodes
        if pattern.startswith('count:'):
            node_type = pattern.split(':', 1)[1]
            if node_type in self.EXPENSIVE_NODES:
                options['parallel'] = True

        return Query(
            type=query.type,
            pattern=pattern,
            options=options
        )

    def _optimize_security(self, query: Query) -> Query:
        """Optimize a security check query.

        Args:
            query: The security query to optimize.

        Returns:
            An optimized version of the query.
        """
        pattern = query.pattern
        options = dict(query.options or {})

        # Security checks often benefit from caching import information
        if pattern == 'dangerous_calls':
            options['cache_imports'] = True

        return Query(
            type=query.type,
            pattern=pattern,
            options=options
        )
