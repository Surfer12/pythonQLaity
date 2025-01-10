from .query_parser import Query, QueryParser
from .query_executor import QueryResult, QueryExecutor
from .query_optimizer import QueryOptimizer

__all__ = [
    'Query',
    'QueryParser',
    'QueryResult',
    'QueryExecutor',
    'QueryOptimizer',
    'create_optimized_executor'
]

def create_optimized_executor() -> QueryExecutor:
    """Create and return a QueryExecutor with an optimizing pipeline.

    This factory function sets up a complete query execution pipeline
    that includes parsing, optimization, and execution.

    Returns:
        A configured QueryExecutor instance.
    """
    return QueryExecutor()
