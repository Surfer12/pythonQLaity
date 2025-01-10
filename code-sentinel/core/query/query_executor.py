"""Query executor module for Code Sentinel.

This module is responsible for executing optimized queries against source code
and returning the results. It handles different types of queries and manages
execution resources efficiently.
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Union

from ..extractors.base_extractor import BaseExtractor
from .query_parser import (
    DataflowNode,
    MetricsNode,
    PatternNode,
    QueryNode,
    QueryType
)

@dataclass
class QueryResult:
    """Represents a single query result."""
    file_path: Path
    line_number: int
    column: int
    snippet: str
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

class QueryExecutor:
    """Executor for Code Sentinel queries."""

    def __init__(
        self,
        extractors: List[BaseExtractor],
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the query executor.

        Args:
            extractors: List of code extractors to use.
            config: Optional configuration dictionary.
        """
        self.extractors = extractors
        self.config = config or {}
        self.max_workers = self.config.get("max_workers", 4)
        self.timeout = self.config.get("timeout_seconds", 300)
        self._result_cache: Dict[str, List[QueryResult]] = {}

    def execute(
        self,
        query: QueryNode,
        target_paths: List[Path]
    ) -> Generator[QueryResult, None, None]:
        """Execute a query against the target paths.

        Args:
            query: The query to execute.
            target_paths: List of paths to analyze.

        Yields:
            QueryResult objects representing matches.

        Raises:
            QueryExecutionError: If execution fails.
            TimeoutError: If execution exceeds the timeout.
        """
        try:
            if isinstance(query, PatternNode):
                yield from self._execute_pattern_query(query, target_paths)
            elif isinstance(query, DataflowNode):
                yield from self._execute_dataflow_query(query, target_paths)
            elif isinstance(query, MetricsNode):
                yield from self._execute_metrics_query(query, target_paths)
            else:
                raise QueryExecutionError(f"Unsupported query type: {type(query)}")
        except Exception as e:
            raise QueryExecutionError(f"Query execution failed: {str(e)}")

    def _execute_pattern_query(
        self,
        query: PatternNode,
        target_paths: List[Path]
    ) -> Generator[QueryResult, None, None]:
        """Execute a pattern matching query.

        Args:
            query: The pattern query to execute.
            target_paths: List of paths to analyze.

        Yields:
            QueryResult objects for pattern matches.
        """
        # Compile regex pattern
        flags = 0 if query.case_sensitive else re.IGNORECASE
        if query.whole_word:
            pattern = f"\\b{query.pattern}\\b"
        else:
            pattern = query.pattern
        regex = re.compile(pattern, flags)

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self._search_file, path, regex): path
                for path in target_paths
                if self._should_process_file(path, query.language)
            }

            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results = future.result()
                    for result in results:
                        yield result
                except Exception as e:
                    print(f"Error processing {path}: {str(e)}")

    def _execute_dataflow_query(
        self,
        query: DataflowNode,
        target_paths: List[Path]
    ) -> Generator[QueryResult, None, None]:
        """Execute a dataflow analysis query.

        Args:
            query: The dataflow query to execute.
            target_paths: List of paths to analyze.

        Yields:
            QueryResult objects for dataflow findings.
        """
        # First, find all potential sources
        source_results = list(self._find_pattern(query.source, target_paths))

        # Then find all potential sinks
        sink_results = list(self._find_pattern(query.sink, target_paths))

        # Analyze dataflow between sources and sinks
        for source in source_results:
            for sink in sink_results:
                if self._check_dataflow(source, sink, query.sanitizers):
                    # Found a dataflow path
                    yield QueryResult(
                        file_path=source.file_path,
                        line_number=source.line_number,
                        column=source.column,
                        snippet=f"Dataflow from {source.snippet} to {sink.snippet}",
                        confidence=0.8,  # Dataflow analysis has some uncertainty
                        metadata={
                            "source": source.snippet,
                            "sink": sink.snippet,
                            "sink_line": sink.line_number
                        }
                    )

    def _execute_metrics_query(
        self,
        query: MetricsNode,
        target_paths: List[Path]
    ) -> Generator[QueryResult, None, None]:
        """Execute a metrics calculation query.

        Args:
            query: The metrics query to execute.
            target_paths: List of paths to analyze.

        Yields:
            QueryResult objects for metric findings.
        """
        for path in target_paths:
            if not self._should_process_file(path):
                continue

            try:
                # Calculate the requested metric
                metric_value = self._calculate_metric(
                    path,
                    query.metric_type
                )

                # Check threshold if specified
                if (query.threshold is None or
                    metric_value > query.threshold):
                    yield QueryResult(
                        file_path=path,
                        line_number=1,  # Metrics apply to whole file
                        column=1,
                        snippet=f"{query.metric_type}: {metric_value}",
                        metadata={"value": metric_value}
                    )
            except Exception as e:
                print(f"Error calculating metrics for {path}: {str(e)}")

    def _search_file(
        self,
        file_path: Path,
        pattern: re.Pattern
    ) -> List[QueryResult]:
        """Search a file for regex pattern matches.

        Args:
            file_path: Path to the file to search.
            pattern: Compiled regex pattern.

        Returns:
            List of QueryResult objects for matches.
        """
        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    for match in pattern.finditer(line):
                        results.append(QueryResult(
                            file_path=file_path,
                            line_number=i,
                            column=match.start() + 1,
                            snippet=line.strip(),
                            metadata={"match": match.group(0)}
                        ))
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
        return results

    def _find_pattern(
        self,
        pattern: str,
        target_paths: List[Path]
    ) -> Generator[QueryResult, None, None]:
        """Find all occurrences of a pattern.

        Args:
            pattern: The pattern to search for.
            target_paths: List of paths to search.

        Yields:
            QueryResult objects for matches.
        """
        regex = re.compile(pattern)
        for path in target_paths:
            if not self._should_process_file(path):
                continue
            yield from self._search_file(path, regex)

    def _check_dataflow(
        self,
        source: QueryResult,
        sink: QueryResult,
        sanitizers: Optional[List[str]]
    ) -> bool:
        """Check if there is a dataflow path between source and sink.

        Args:
            source: The source result.
            sink: The sink result.
            sanitizers: Optional list of sanitizer functions.

        Returns:
            True if there is a dataflow path, False otherwise.
        """
        # Simple heuristic: check if sink appears after source in same file
        if (source.file_path == sink.file_path and
            source.line_number < sink.line_number):
            # Check if any sanitizers are applied
            if sanitizers:
                for sanitizer in sanitizers:
                    if self._is_sanitized(source, sink, sanitizer):
                        return False
            return True
        return False

    def _is_sanitized(
        self,
        source: QueryResult,
        sink: QueryResult,
        sanitizer: str
    ) -> bool:
        """Check if data is sanitized between source and sink.

        Args:
            source: The source result.
            sink: The sink result.
            sanitizer: The sanitizer function name/pattern.

        Returns:
            True if the data is sanitized, False otherwise.
        """
        # Simple check: look for sanitizer between source and sink
        try:
            with open(source.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[source.line_number-1:sink.line_number]
                return any(sanitizer in line for line in lines)
        except Exception:
            return False

    def _calculate_metric(self, file_path: Path, metric_type: str) -> float:
        """Calculate a specific metric for a file.

        Args:
            file_path: Path to the file.
            metric_type: Type of metric to calculate.

        Returns:
            The calculated metric value.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if metric_type == "complexity":
                # Simple cyclomatic complexity estimation
                decision_points = len(re.findall(
                    r'\b(if|while|for|and|or)\b',
                    content
                ))
                return 1 + decision_points

            elif metric_type == "loc":
                # Lines of code (excluding comments and blank lines)
                lines = content.split('\n')
                return len([l for l in lines if l.strip() and not l.strip().startswith('#')])

            else:
                raise ValueError(f"Unsupported metric type: {metric_type}")
        except Exception as e:
            raise QueryExecutionError(f"Error calculating metric: {str(e)}")

    def _should_process_file(
        self,
        file_path: Path,
        required_language: Optional[str] = None
    ) -> bool:
        """Check if a file should be processed.

        Args:
            file_path: Path to the file.
            required_language: Optional required programming language.

        Returns:
            True if the file should be processed, False otherwise.
        """
        # Check if any extractor supports this file
        supported = any(
            ext.supports_file(file_path)
            for ext in self.extractors
        )

        if not supported:
            return False

        # Check language requirement if specified
        if required_language:
            extension = file_path.suffix.lower()
            language_map = {
                ".py": "python",
                ".js": "javascript",
                ".java": "java",
                ".cpp": "cpp",
                ".c": "c",
            }
            return language_map.get(extension) == required_language.lower()

        return True

    def clear_cache(self) -> None:
        """Clear the result cache."""
        self._result_cache.clear()

class QueryExecutionError(Exception):
    """Exception raised for query execution errors."""
    pass
