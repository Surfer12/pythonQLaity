"""Tests for the analysis tool."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from anthropic.tools import AnalysisTool
from anthropic.tools.analysis import SecurityError

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp:
        yield Path(temp)

@pytest.fixture
def analysis_tool() -> AnalysisTool:
    """Create an analysis tool for testing."""
    return AnalysisTool()

@pytest.fixture
def sample_code(temp_dir: Path) -> Path:
    """Create a sample Python file for testing."""
    file_path = temp_dir / 'test.py'
    code = '''
def dangerous_function():
    user_input = input("Enter command: ")
    eval(user_input)  # Security issue

def calculate_sum(a, b):
    return a + b

def complex_function():
    result = calculate_sum(1, 2)
    dangerous_function()  # Calls dangerous function
    return result

class TestClass:
    def test_method(self):
        complex_function()  # Creates call chain
    '''
    file_path.write_text(code)
    return file_path

@pytest.fixture
def large_file(temp_dir: Path) -> Path:
    """Create a large Python file for testing size limits."""
    file_path = temp_dir / 'large.py'
    # Create a file larger than 10MB
    code = 'x = 1\n' * (1024 * 1024)  # Roughly 10MB of text
    file_path.write_text(code)
    return file_path

def test_analyze_directory_security(
    analysis_tool: AnalysisTool,
    temp_dir: Path,
    sample_code: Path
):
    """Test security analysis of a directory."""
    results = analysis_tool.analyze_directory(
        temp_dir,
        query_type='security',
        pattern='dangerous_calls'
    )

    assert results['directory'] == str(temp_dir)
    assert results['query_type'] == 'security'
    assert len(results['results']) == 1

    issue = results['results'][0]
    assert issue['filepath'] == str(sample_code)
    assert 'eval' in issue['context']

    # Check call chain information
    assert 'call_chain' in issue
    if issue['call_chain']:  # Call chain might be None if function detection fails
        assert issue['call_chain']['depth'] > 0
        assert 'complex_function' in issue['call_chain']['called_by']

def test_analyze_directory_metrics(
    analysis_tool: AnalysisTool,
    temp_dir: Path,
    sample_code: Path
):
    """Test metrics analysis of a directory."""
    results = analysis_tool.analyze_directory(
        temp_dir,
        query_type='metrics',
        pattern='count:FunctionDef'
    )

    assert results['directory'] == str(temp_dir)
    assert results['query_type'] == 'metrics'
    assert len(results['results']) > 0

def test_calculate_metrics(
    analysis_tool: AnalysisTool,
    temp_dir: Path,
    sample_code: Path
):
    """Test calculating metrics for a file."""
    results = analysis_tool.calculate_metrics(sample_code)

    assert results['filepath'] == str(sample_code)
    assert 'metrics' in results
    metrics = results['metrics']
    assert metrics['num_functions'] == 3  # dangerous_function, calculate_sum, complex_function
    assert metrics['num_classes'] == 1
    assert metrics['num_methods'] == 1

def test_calculate_metrics_directory(
    analysis_tool: AnalysisTool,
    temp_dir: Path,
    sample_code: Path
):
    """Test calculating metrics for a directory."""
    results = analysis_tool.calculate_metrics(temp_dir)

    assert results['path'] == str(temp_dir)
    assert 'total_metrics' in results
    assert 'file_metrics' in results
    assert len(results['file_metrics']) == 1

    total = results['total_metrics']
    assert total['num_functions'] == 3
    assert total['num_classes'] == 1
    assert total['num_methods'] == 1

def test_invalid_directory(analysis_tool: AnalysisTool, temp_dir: Path):
    """Test handling of invalid directory."""
    invalid_dir = temp_dir / 'nonexistent'
    with pytest.raises(ValueError):
        analysis_tool.analyze_directory(invalid_dir)

def test_invalid_file_metrics(analysis_tool: AnalysisTool, temp_dir: Path):
    """Test handling of invalid file for metrics."""
    invalid_file = temp_dir / 'nonexistent.py'
    with pytest.raises(ValueError):
        analysis_tool.calculate_metrics(invalid_file)

def test_unsafe_path(analysis_tool: AnalysisTool, temp_dir: Path):
    """Test handling of unsafe paths."""
    unsafe_dir = temp_dir / '..' / '..' / 'etc'
    with pytest.raises(SecurityError):
        analysis_tool.analyze_directory(unsafe_dir)

def test_large_file_handling(
    analysis_tool: AnalysisTool,
    temp_dir: Path,
    large_file: Path,
    caplog
):
    """Test handling of files exceeding size limit."""
    results = analysis_tool.analyze_directory(
        temp_dir,
        query_type='metrics',
        max_file_size=1024  # 1KB limit
    )

    assert len(results['results']) == 0
    assert any('Skipping large file' in record.message for record in caplog.records)

def test_metrics_caching(
    analysis_tool: AnalysisTool,
    temp_dir: Path,
    sample_code: Path
):
    """Test that metrics are properly cached."""
    # First call should calculate metrics
    results1 = analysis_tool.calculate_metrics(sample_code, use_cache=True)

    # Modify the file but keep cache
    sample_code.write_text('def new_function(): pass')

    # Second call should return cached results
    results2 = analysis_tool.calculate_metrics(sample_code, use_cache=True)

    assert results1 == results2

    # Third call with cache disabled should reflect new content
    results3 = analysis_tool.calculate_metrics(sample_code, use_cache=False)
    assert results3 != results1
    assert results3['metrics']['num_functions'] == 1

def test_dangerous_patterns_detection(
    analysis_tool: AnalysisTool,
    temp_dir: Path
):
    """Test detection of various dangerous patterns."""
    file_path = temp_dir / 'dangerous.py'
    code = '''
import os
import subprocess
import pickle
import yaml

def multiple_dangers():
    os.system("rm -rf /")  # Dangerous system call
    subprocess.call("echo 'hello'", shell=True)  # Shell injection risk
    pickle.loads(b"data")  # Deserialization vulnerability
    yaml.load("data")  # YAML parsing vulnerability
    '''
    file_path.write_text(code)

    results = analysis_tool.analyze_directory(
        temp_dir,
        query_type='security'
    )

    dangerous_calls = {r['context'] for r in results['results']}
    assert 'os.system' in dangerous_calls
    assert 'subprocess.call' in dangerous_calls
    assert 'pickle.loads' in dangerous_calls
    assert 'yaml.load' in dangerous_calls

def test_call_graph_depth(
    analysis_tool: AnalysisTool,
    temp_dir: Path
):
    """Test call graph depth calculation."""
    file_path = temp_dir / 'deep_calls.py'
    code = '''
def level3():
    eval("1 + 1")  # Security issue

def level2():
    level3()

def level1():
    level2()

def entry_point():
    level1()
    '''
    file_path.write_text(code)

    results = analysis_tool.analyze_directory(
        temp_dir,
        query_type='security'
    )

    issue = next(r for r in results['results'] if 'eval' in r['context'])
    assert issue['call_chain']['depth'] >= 3  # Should detect the deep call chain
