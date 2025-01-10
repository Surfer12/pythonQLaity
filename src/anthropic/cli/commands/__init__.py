"""CLI commands for Code Sentinel.

This module provides the command-line interface commands for analyzing code,
executing queries, and calculating metrics.
"""

from .analyze import analyze
from .metrics import metrics
from .query import query

__all__ = ['analyze', 'metrics', 'query']
