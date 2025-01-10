"""Query parser module for Code Sentinel.

This module is responsible for parsing analysis queries into an intermediate
representation that can be optimized and executed by the query engine.
"""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

class QueryType(Enum):
    """Types of supported queries."""
    PATTERN_MATCH = auto()  # Pattern-based code search
    AST_ANALYSIS = auto()   # Abstract syntax tree analysis
    DATAFLOW = auto()       # Data flow analysis
    SECURITY = auto()       # Security vulnerability detection
    METRICS = auto()        # Code metrics calculation

@dataclass
class QueryNode:
    """Base class for query AST nodes."""
    location: Optional[str] = None  # Source location for error reporting

@dataclass
class PatternNode(QueryNode):
    """Node representing a pattern matching query."""
    pattern: str
    language: Optional[str] = None
    case_sensitive: bool = True
    whole_word: bool = False

@dataclass
class DataflowNode(QueryNode):
    """Node representing a dataflow analysis query."""
    source: str
    sink: str
    sanitizers: List[str] = None

@dataclass
class MetricsNode(QueryNode):
    """Node representing a code metrics query."""
    metric_type: str
    threshold: Optional[float] = None

class QueryParser:
    """Parser for Code Sentinel queries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the query parser.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}

    def parse(self, query_text: str) -> QueryNode:
        """Parse a query string into a query AST.

        Args:
            query_text: The query string to parse.

        Returns:
            A QueryNode representing the parsed query.

        Raises:
            QueryParseError: If the query cannot be parsed.
        """
        query_text = query_text.strip()

        # Try to determine query type from the query text
        query_type = self._determine_query_type(query_text)

        try:
            if query_type == QueryType.PATTERN_MATCH:
                return self._parse_pattern_query(query_text)
            elif query_type == QueryType.DATAFLOW:
                return self._parse_dataflow_query(query_text)
            elif query_type == QueryType.METRICS:
                return self._parse_metrics_query(query_text)
            else:
                raise QueryParseError(f"Unsupported query type: {query_type}")
        except Exception as e:
            raise QueryParseError(f"Failed to parse query: {str(e)}")

    def _determine_query_type(self, query_text: str) -> QueryType:
        """Determine the type of query from its text.

        Args:
            query_text: The query text to analyze.

        Returns:
            The determined QueryType.
        """
        # Simple heuristics for query type detection
        lower_query = query_text.lower()

        if any(kw in lower_query for kw in ['flow', 'from', 'to', 'sink']):
            return QueryType.DATAFLOW
        elif any(kw in lower_query for kw in ['metric', 'count', 'complexity']):
            return QueryType.METRICS
        else:
            return QueryType.PATTERN_MATCH

    def _parse_pattern_query(self, query_text: str) -> PatternNode:
        """Parse a pattern matching query.

        Args:
            query_text: The query text to parse.

        Returns:
            A PatternNode representing the pattern query.
        """
        # Extract language if specified
        language = None
        if 'language:' in query_text:
            parts = query_text.split('language:', 1)
            language = parts[1].split()[0]
            query_text = parts[0] + ' '.join(parts[1].split()[1:])

        # Extract case sensitivity
        case_sensitive = True
        if 'case:' in query_text:
            parts = query_text.split('case:', 1)
            case_value = parts[1].split()[0].lower()
            case_sensitive = case_value not in ('false', 'no', '0')
            query_text = parts[0] + ' '.join(parts[1].split()[1:])

        return PatternNode(
            pattern=query_text.strip(),
            language=language,
            case_sensitive=case_sensitive
        )

    def _parse_dataflow_query(self, query_text: str) -> DataflowNode:
        """Parse a dataflow analysis query.

        Args:
            query_text: The query text to parse.

        Returns:
            A DataflowNode representing the dataflow query.
        """
        # Extract source and sink
        if 'from' not in query_text or 'to' not in query_text:
            raise QueryParseError("Dataflow query must specify 'from' and 'to'")

        parts = query_text.split('from', 1)[1].split('to', 1)
        source = parts[0].strip()
        sink_part = parts[1]

        # Extract sanitizers if specified
        sanitizers = []
        if 'sanitize' in sink_part:
            sink_parts = sink_part.split('sanitize', 1)
            sink = sink_parts[0].strip()
            sanitizers = [s.strip() for s in sink_parts[1].split(',')]
        else:
            sink = sink_part.strip()

        return DataflowNode(
            source=source,
            sink=sink,
            sanitizers=sanitizers
        )

    def _parse_metrics_query(self, query_text: str) -> MetricsNode:
        """Parse a code metrics query.

        Args:
            query_text: The query text to parse.

        Returns:
            A MetricsNode representing the metrics query.
        """
        # Extract metric type
        parts = query_text.split()
        metric_type = parts[0].lower()

        # Extract threshold if specified
        threshold = None
        if len(parts) > 1 and parts[1].replace('.', '').isdigit():
            threshold = float(parts[1])

        return MetricsNode(
            metric_type=metric_type,
            threshold=threshold
        )

class QueryParseError(Exception):
    """Exception raised for query parsing errors."""
    pass
