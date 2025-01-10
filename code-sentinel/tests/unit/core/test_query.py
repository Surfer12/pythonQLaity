"""Tests for the query engine components."""

import pytest
from pathlib import Path
from typing import List

from core.extractors.base_extractor import BaseExtractor
from core.query.query_parser import (
    DataflowNode,
    MetricsNode,
    PatternNode,
    QueryParser,
    QueryParseError,
    QueryType
)
from core.query.query_optimizer import QueryOptimizer, QueryOptimizationError
from core.query.query_executor import QueryExecutor, QueryResult

class MockExtractor(BaseExtractor):
    """Mock extractor for testing."""
    def extract(self, file_path: Path):
        return {}

    def supports_file(self, file_path: Path) -> bool:
        return file_path.suffix in ['.py', '.java']

    def get_supported_extensions(self) -> List[str]:
        return ['.py', '.java']

@pytest.fixture
def query_parser():
    """Create a QueryParser instance for testing."""
    return QueryParser()

@pytest.fixture
def query_optimizer():
    """Create a QueryOptimizer instance for testing."""
    return QueryOptimizer()

@pytest.fixture
def query_executor():
    """Create a QueryExecutor instance for testing."""
    return QueryExecutor([MockExtractor()])

@pytest.fixture
def sample_file(tmp_path):
    """Create a sample Python file for testing."""
    content = '''
def process_input(user_input):
    """Process user input."""
    # Potential security issue: direct use of input
    cmd = user_input
    os.system(cmd)  # Sink: command injection

def calculate_score(data):
    """Calculate a score."""
    if data > 0:
        if data < 10:
            if data % 2 == 0:
                return data * 2
    return 0
'''
    file_path = tmp_path / "sample.py"
    file_path.write_text(content)
    return file_path

# Parser Tests
def test_parse_pattern_query(query_parser):
    """Test parsing pattern matching queries."""
    # Basic pattern
    query = query_parser.parse('os.system')
    assert isinstance(query, PatternNode)
    assert query.pattern == 'os.system'
    assert query.case_sensitive is True

    # Pattern with language
    query = query_parser.parse('language:python os.system')
    assert query.pattern == 'os.system'
    assert query.language == 'python'

    # Pattern with case sensitivity
    query = query_parser.parse('case:false os.system')
    assert query.pattern == 'os.system'
    assert query.case_sensitive is False

def test_parse_dataflow_query(query_parser):
    """Test parsing dataflow analysis queries."""
    query = query_parser.parse('flow from user_input to os.system')
    assert isinstance(query, DataflowNode)
    assert query.source == 'user_input'
    assert query.sink == 'os.system'
    assert query.sanitizers is None

    # With sanitizers
    query = query_parser.parse('flow from user_input to os.system sanitize escape_shell, validate_input')
    assert query.sanitizers == ['escape_shell', 'validate_input']

def test_parse_metrics_query(query_parser):
    """Test parsing metrics calculation queries."""
    query = query_parser.parse('complexity 10')
    assert isinstance(query, MetricsNode)
    assert query.metric_type == 'complexity'
    assert query.threshold == 10.0

    query = query_parser.parse('loc')
    assert query.metric_type == 'loc'
    assert query.threshold is None

def test_parse_invalid_query(query_parser):
    """Test handling of invalid queries."""
    with pytest.raises(QueryParseError):
        query_parser.parse('')

    with pytest.raises(QueryParseError):
        query_parser.parse('flow from')  # Incomplete dataflow query

# Optimizer Tests
def test_optimize_pattern_query(query_optimizer):
    """Test optimizing pattern matching queries."""
    # Test wildcard optimization
    query = PatternNode(pattern='.*test.*')
    optimized = query_optimizer.optimize(query)
    assert optimized.pattern == 'test'

    # Test character class optimization
    query = PatternNode(pattern='[0-9]+')
    optimized = query_optimizer.optimize(query)
    assert optimized.pattern == '\\d+'

def test_optimize_dataflow_query(query_optimizer):
    """Test optimizing dataflow analysis queries."""
    query = DataflowNode(
        source='input',
        sink='output',
        sanitizers=['escape.shell', 'basic_check', 'complex.validation.check']
    )
    optimized = query_optimizer.optimize(query)

    # Check if sanitizers are sorted by complexity
    assert optimized.sanitizers[0] == 'basic_check'  # Simplest
    assert optimized.sanitizers[-1] == 'complex.validation.check'  # Most complex

def test_optimize_metrics_query(query_optimizer):
    """Test optimizing metrics calculation queries."""
    query = MetricsNode(metric_type='COMPLEXITY', threshold=10.12345)
    optimized = query_optimizer.optimize(query)
    assert optimized.metric_type == 'complexity'
    assert optimized.threshold == 10.123  # Rounded to 3 decimal places

def test_optimizer_caching(query_optimizer):
    """Test query optimization caching."""
    query = PatternNode(pattern='test')

    # First optimization
    query_optimizer.optimize(query)
    assert len(query_optimizer._pattern_cache) == 1

    # Same query should use cache
    query_optimizer.optimize(query)
    assert len(query_optimizer._pattern_cache) == 1

# Executor Tests
def test_execute_pattern_query(query_executor, sample_file):
    """Test executing pattern matching queries."""
    query = PatternNode(pattern='os\\.system')
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1
    assert results[0].snippet.strip() == 'os.system(cmd)  # Sink: command injection'

def test_execute_dataflow_query(query_executor, sample_file):
    """Test executing dataflow analysis queries."""
    query = DataflowNode(
        source='user_input',
        sink='os.system'
    )
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1
    assert 'user_input' in results[0].metadata['source']
    assert 'os.system' in results[0].metadata['sink']

def test_execute_metrics_query(query_executor, sample_file):
    """Test executing metrics calculation queries."""
    # Test complexity metric
    query = MetricsNode(metric_type='complexity')
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1
    assert results[0].metadata['value'] > 1  # Should have some complexity

    # Test LOC metric
    query = MetricsNode(metric_type='loc')
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1
    assert results[0].metadata['value'] > 0

def test_execute_with_language_filter(query_executor, tmp_path):
    """Test query execution with language filtering."""
    # Create Python and text files
    py_file = tmp_path / "test.py"
    py_file.write_text("test = 123")

    txt_file = tmp_path / "test.txt"
    txt_file.write_text("test = 123")

    query = PatternNode(
        pattern='test',
        language='python'
    )

    results = list(query_executor.execute(query, [py_file, txt_file]))
    assert len(results) == 1  # Only Python file should be processed
    assert results[0].file_path == py_file

def test_execute_with_invalid_files(query_executor, tmp_path):
    """Test query execution with invalid files."""
    # Non-existent file
    bad_file = tmp_path / "nonexistent.py"

    query = PatternNode(pattern='test')
    results = list(query_executor.execute(query, [bad_file]))
    assert len(results) == 0  # Should handle gracefully

def test_parallel_execution(query_executor, tmp_path):
    """Test parallel execution of queries."""
    # Create multiple files
    files = []
    for i in range(5):
        file_path = tmp_path / f"test{i}.py"
        file_path.write_text(f"value_{i} = {i}")
        files.append(file_path)

    query = PatternNode(pattern='value_[0-9]')
    results = list(query_executor.execute(query, files))
    assert len(results) == 5  # Should find all values
