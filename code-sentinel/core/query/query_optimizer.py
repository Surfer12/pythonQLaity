"""Query optimizer module for Code Sentinel.

This module is responsible for optimizing parsed queries for efficient execution.
It applies various optimization strategies based on the query type
and structure.
"""

from typing import Any, Dict, List, Optional, Set

from .query_parser import (
    DataflowNode,
    MetricsNode,
    PatternNode,
    QueryNode,
    QueryType
)

class QueryOptimizer:
    """Optimizer for Code Sentinel queries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the query optimizer.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self._pattern_cache: Dict[str, Set[str]] = {}
        self._dataflow_cache: Dict[str, List[str]] = {}

    def optimize(self, query: QueryNode) -> QueryNode:
        """Optimize a query for better performance.

        Args:
            query: The query to optimize.

        Returns:
            An optimized version of the query.

        Raises:
            QueryOptimizationError: If optimization fails.
        """
        try:
            if isinstance(query, PatternNode):
                return self._optimize_pattern_query(query)
            elif isinstance(query, DataflowNode):
                return self._optimize_dataflow_query(query)
            elif isinstance(query, MetricsNode):
                return self._optimize_metrics_query(query)
            else:
                return query  # No optimization for unknown query types
        except Exception as e:
            raise QueryOptimizationError(f"Failed to optimize query: {str(e)}")

    def _optimize_pattern_query(self, query: PatternNode) -> PatternNode:
        """Optimize a pattern matching query.

        Args:
            query: The pattern query to optimize.

        Returns:
            An optimized version of the pattern query.
        """
        # Check cache first
        cache_key = f"{query.pattern}:{query.language}:{query.case_sensitive}"
        if cache_key in self._pattern_cache:
            # Use cached optimization results
            return query

        # Optimize pattern
        pattern = query.pattern

        # Remove redundant wildcards
        pattern = self._optimize_wildcards(pattern)

        # Optimize character classes
        pattern = self._optimize_char_classes(pattern)

        # Cache the optimized pattern
        self._pattern_cache[cache_key] = set()  # Track pattern usage

        return PatternNode(
            pattern=pattern,
            language=query.language,
            case_sensitive=query.case_sensitive,
            whole_word=query.whole_word,
            location=query.location
        )

    def _optimize_dataflow_query(self, query: DataflowNode) -> DataflowNode:
        """Optimize a dataflow analysis query.

        Args:
            query: The dataflow query to optimize.

        Returns:
            An optimized version of the dataflow query.
        """
        # Check cache
        cache_key = f"{query.source}:{query.sink}"
        if cache_key in self._dataflow_cache:
            # Use cached paths
            return query

        # Optimize sanitizers list
        if query.sanitizers:
            # Remove duplicate sanitizers
            sanitizers = list(dict.fromkeys(query.sanitizers))

            # Sort sanitizers by complexity (simpler ones first)
            sanitizers.sort(key=lambda x: self._estimate_sanitizer_complexity(x))
        else:
            sanitizers = None

        # Cache the optimization
        self._dataflow_cache[cache_key] = sanitizers or []

        return DataflowNode(
            source=query.source,
            sink=query.sink,
            sanitizers=sanitizers,
            location=query.location
        )

    def _optimize_metrics_query(self, query: MetricsNode) -> MetricsNode:
        """Optimize a metrics calculation query.

        Args:
            query: The metrics query to optimize.

        Returns:
            An optimized version of the metrics query.
        """
        # Metrics queries are relatively simple, just normalize the type
        metric_type = query.metric_type.lower()

        # Round threshold to reasonable precision if specified
        threshold = query.threshold
        if threshold is not None:
            threshold = round(threshold, 3)  # 3 decimal places should be enough

        return MetricsNode(
            metric_type=metric_type,
            threshold=threshold,
            location=query.location
        )

    def _optimize_wildcards(self, pattern: str) -> str:
        """Optimize wildcard patterns in a query.

        Args:
            pattern: The pattern to optimize.

        Returns:
            The optimized pattern.
        """
        # Remove redundant .* patterns
        pattern = pattern.replace(".*.*", ".*")

        # Convert .* at start/end to ^ and $ anchors if appropriate
        if pattern.startswith(".*"):
            pattern = pattern[2:]
        if pattern.endswith(".*"):
            pattern = pattern[:-2]

        return pattern

    def _optimize_char_classes(self, pattern: str) -> str:
        """Optimize character class patterns in a query.

        Args:
            pattern: The pattern to optimize.

        Returns:
            The optimized pattern.
        """
        # Replace common character classes with shorter equivalents
        replacements = {
            "[0-9]": "\\d",
            "[^0-9]": "\\D",
            "[a-zA-Z0-9_]": "\\w",
            "[^a-zA-Z0-9_]": "\\W",
            "[ \\t\\n\\r\\f\\v]": "\\s",
            "[^ \\t\\n\\r\\f\\v]": "\\S"
        }

        for old, new in replacements.items():
            pattern = pattern.replace(old, new)

        return pattern

    def _estimate_sanitizer_complexity(self, sanitizer: str) -> int:
        """Estimate the complexity of a sanitizer function.

        Args:
            sanitizer: The sanitizer function name/pattern.

        Returns:
            An integer score representing relative complexity.
        """
        # Simple heuristic based on name length and dots
        base_score = len(sanitizer)
        dots = sanitizer.count(".")
        return base_score + (dots * 2)  # Nested calls are more complex

    def clear_caches(self) -> None:
        """Clear the optimization caches."""
        self._pattern_cache.clear()
        self._dataflow_cache.clear()

class QueryOptimizationError(Exception):
    """Exception raised for query optimization errors."""
    pass
