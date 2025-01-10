"""Tool for code analysis using Code Sentinel."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Union

from ..core.extractors import create_extractor
from ..core.models import create_model
from ..core.query import Query, QueryParser, QueryExecutor, QueryOptimizer
from ..core.utils.logging_utils import setup_logger
from ..core.utils.path_utils import collect_python_files, is_safe_path
from .base import BaseTool

logger = setup_logger('anthropic.tools.analysis')

@dataclass
class CallGraphNode:
    """Represents a node in the call graph."""
    name: str
    module: str
    calls: Set[str]  # Names of functions this node calls
    called_by: Set[str]  # Names of functions that call this node
    depth: int = 0  # Call chain depth

@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    allowed_paths: List[str]
    blocked_commands: List[str]
    max_file_size: int
    required_permissions: List[str]

@dataclass
class AnomalyThresholds:
    """Thresholds for anomaly detection."""
    max_file_operations_per_minute: int
    max_failed_commands_per_minute: int
    suspicious_pattern_threshold: float

class RuntimeMonitor:
    """Monitors runtime events for security issues."""

    def __init__(self, policy: SecurityPolicy, thresholds: AnomalyThresholds):
        self.policy = policy
        self.thresholds = thresholds
        self.active = True
        self.events: List[Dict[str, Any]] = []

    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single event and check for security issues."""
        if not self.active:
            raise RuntimeError("Monitor is not active")

        self.events.append(event)
        return self._analyze_event(event)

    def _analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an event for security issues."""
        warnings = []
        is_safe = True

        if event['type'] == 'command':
            cmd = event['command']
            for blocked in self.policy.blocked_commands:
                if blocked in cmd:
                    warnings.append(f"dangerous_command: {blocked}")
                    is_safe = False

        elif event['type'] == 'file_access':
            path = event['path']
            if not any(path.startswith(allowed) for allowed in self.policy.allowed_paths):
                warnings.append(f"path_not_allowed: {path}")
                is_safe = False

        # Check thresholds
        recent_events = [e for e in self.events[-60:]]  # Last minute
        if event['type'] == 'file_access':
            ops_per_minute = sum(1 for e in recent_events if e['type'] == 'file_access')
            if ops_per_minute > self.thresholds.max_file_operations_per_minute:
                warnings.append("file_operations_threshold_exceeded")
                is_safe = False

        return {
            'is_safe': is_safe,
            'warnings': warnings,
            'timestamp': datetime.utcnow().isoformat()
        }

    def stop(self):
        """Stop the monitor."""
        self.active = False

class AnalysisTool(BaseTool):
    """Tool for analyzing code using Code Sentinel.

    This tool provides functionality to analyze code for quality, security,
    and maintainability issues using Code Sentinel's static analysis capabilities.
    It integrates call graph analysis for deeper insights.
    """

    # Known dangerous patterns to check in security analysis
    DANGEROUS_PATTERNS = {
        'eval', 'exec', 'os.system', 'subprocess.call',
        'pickle.loads', 'yaml.load', 'input', 'rm -rf',
        'chmod -R', ':(){ :|:& };:', 'dd if=/dev/random'
    }

    def __init__(self):
        """Initialize the analysis tool."""
        self.query_parser = QueryParser()
        self.query_optimizer = QueryOptimizer()
        self.query_executor = QueryExecutor()
        self._ast_cache: Dict[str, Any] = {}
        self._metrics_cache: Dict[str, Dict[str, Any]] = {}
        self._security_policy = SecurityPolicy(
            allowed_paths=['/home', '/tmp'],
            blocked_commands=['rm -rf', 'chmod -R'],
            max_file_size=10 * 1024 * 1024,  # 10MB
            required_permissions=['read', 'write']
        )
        self._anomaly_thresholds = AnomalyThresholds(
            max_file_operations_per_minute=10,
            max_failed_commands_per_minute=5,
            suspicious_pattern_threshold=0.8
        )
        self._runtime_events: List[Dict[str, Any]] = []

    def set_security_policy(self, policy: Dict[str, Any]) -> None:
        """Set the security policy configuration.

        Args:
            policy: Dictionary containing security policy settings.
        """
        self._security_policy = SecurityPolicy(
            allowed_paths=policy['allowed_paths'],
            blocked_commands=policy['blocked_commands'],
            max_file_size=policy['max_file_size'],
            required_permissions=policy['required_permissions']
        )

    def set_anomaly_thresholds(self, thresholds: Dict[str, Any]) -> None:
        """Set the anomaly detection thresholds.

        Args:
            thresholds: Dictionary containing threshold settings.
        """
        self._anomaly_thresholds = AnomalyThresholds(
            max_file_operations_per_minute=thresholds['max_file_operations_per_minute'],
            max_failed_commands_per_minute=thresholds['max_failed_commands_per_minute'],
            suspicious_pattern_threshold=thresholds['suspicious_pattern_threshold']
        )

    def analyze_command(self, command: str) -> Dict[str, Any]:
        """Analyze a shell command for security issues.

        Args:
            command: The shell command to analyze.

        Returns:
            Dictionary containing analysis results.
        """
        warnings = []
        is_safe = True
        risk_level = 'low'

        # Check against dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in command:
                warnings.append(f"dangerous_pattern_detected: {pattern}")
                is_safe = False
                risk_level = 'high'

        # Check against blocked commands
        for blocked in self._security_policy.blocked_commands:
            if blocked in command:
                warnings.append(f"blocked_by_policy: {blocked}")
                is_safe = False
                risk_level = 'high'

        return {
            'is_safe': is_safe,
            'risk_level': risk_level,
            'warnings': warnings,
            'command': command
        }

    def analyze_file_content(
        self,
        filepath: Union[str, Path],
        content: str
    ) -> Dict[str, Any]:
        """Analyze file content for security issues.

        Args:
            filepath: Path to the file.
            content: The content to analyze.

        Returns:
            Dictionary containing analysis results.
        """
        warnings = []
        is_safe = True

        try:
            # Parse the content as AST if it's a Python file
            if str(filepath).endswith('.py'):
                extractor = create_extractor(content)
                ast = extractor.extract_from_string(content)

                # Look for dangerous patterns in AST
                dangerous_nodes = self.query_executor.execute(
                    ast,
                    self.query_parser.parse('security:dangerous_calls'),
                    filepath
                )

                if dangerous_nodes:
                    warnings.extend(f"dangerous_pattern: {node.match_type}" for node in dangerous_nodes)
                    is_safe = False

            # Check file size
            if len(content.encode('utf-8')) > self._security_policy.max_file_size:
                warnings.append("file_size_exceeds_limit")
                is_safe = False

        except Exception as e:
            warnings.append(f"analysis_error: {str(e)}")
            is_safe = False

        return {
            'is_safe': is_safe,
            'warnings': warnings,
            'filepath': str(filepath)
        }

    def analyze_file_access(
        self,
        filepath: Union[str, Path],
        operation: str
    ) -> Dict[str, Any]:
        """Analyze file access for security issues.

        Args:
            filepath: Path to the file.
            operation: The operation being performed (read/write).

        Returns:
            Dictionary containing analysis results.
        """
        warnings = []
        is_safe = True

        # Check if path is allowed
        if not any(str(filepath).startswith(allowed) for allowed in self._security_policy.allowed_paths):
            warnings.append("path_not_allowed")
            is_safe = False

        # Check if operation is allowed
        if operation not in self._security_policy.required_permissions:
            warnings.append(f"operation_not_allowed: {operation}")
            is_safe = False

        return {
            'is_safe': is_safe,
            'warnings': warnings,
            'filepath': str(filepath),
            'operation': operation
        }

    def analyze_runtime_events(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze a sequence of runtime events for security issues.

        Args:
            events: List of event dictionaries to analyze.

        Returns:
            Dictionary containing analysis results.
        """
        warnings = []
        is_safe = True

        # Add events to history
        self._runtime_events.extend(events)

        # Analyze each event
        for event in events:
            if event['type'] == 'command':
                cmd_result = self.analyze_command(event['command'])
                if not cmd_result['is_safe']:
                    warnings.extend(cmd_result['warnings'])
                    is_safe = False

            elif event['type'] == 'file_access':
                access_result = self.analyze_file_access(
                    event['path'],
                    event['operation']
                )
                if not access_result['is_safe']:
                    warnings.extend(access_result['warnings'])
                    is_safe = False

        # Check thresholds
        recent_events = self._runtime_events[-60:]  # Last minute
        file_ops = sum(1 for e in recent_events if e['type'] == 'file_access')
        if file_ops > self._anomaly_thresholds.max_file_operations_per_minute:
            warnings.append("file_operations_threshold_exceeded")
            is_safe = False

        return {
            'is_safe': is_safe,
            'warnings': warnings,
            'events_analyzed': len(events)
        }

    def generate_session_report(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a report summarizing the session's security analysis.

        Args:
            events: List of session events to analyze.

        Returns:
            Dictionary containing the session report.
        """
        total_events = len(events)
        blocked_actions = []
        risk_level = 'low'
        warnings = []

        # Analyze events
        command_count = 0
        file_access_count = 0
        blocked_count = 0

        for event in events:
            if event['type'] == 'command':
                command_count += 1
                if event.get('result') == 'blocked':
                    blocked_count += 1
                    blocked_actions.append(event)
            elif event['type'] == 'file_access':
                file_access_count += 1

        # Determine risk level
        if blocked_count > 0:
            risk_level = 'high' if blocked_count > 5 else 'medium'

        # Generate summary
        summary = {
            'total_events': total_events,
            'command_count': command_count,
            'file_access_count': file_access_count,
            'blocked_count': blocked_count
        }

        return {
            'summary': summary,
            'blocked_actions': blocked_actions,
            'risk_assessment': {
                'overall_risk_level': risk_level,
                'warnings': warnings
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    def start_continuous_monitoring(self) -> RuntimeMonitor:
        """Start continuous monitoring of events.

        Returns:
            A RuntimeMonitor instance for processing events.
        """
        return RuntimeMonitor(self._security_policy, self._anomaly_thresholds)

    def analyze_directory(
        self,
        directory: Union[str, Path],
        query_type: str = 'security',
        pattern: Optional[str] = None,
        recursive: bool = True,
        max_file_size: int = 10 * 1024 * 1024  # 10MB
    ) -> Dict[str, Any]:
        """Analyze a directory for code issues.

        Args:
            directory: Path to the directory to analyze.
            query_type: Type of analysis ('security', 'metrics', 'ast_pattern').
            pattern: Optional specific pattern to search for.
            recursive: Whether to analyze subdirectories.
            max_file_size: Maximum file size to analyze in bytes.

        Returns:
            Dictionary containing analysis results.

        Raises:
            ValueError: If the directory is invalid or unsafe.
            SecurityError: If a security constraint is violated.
        """
        directory = Path(directory).resolve()

        # Security checks
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        if not is_safe_path(directory):
            raise SecurityError(f"Unsafe directory path: {directory}")

        # Build query
        if pattern is None:
            if query_type == 'security':
                pattern = 'dangerous_calls'
            elif query_type == 'metrics':
                pattern = 'count:all'
            else:
                pattern = 'FunctionDef'

        query_str = f"{query_type}:{pattern}"
        query = self.query_parser.parse(query_str)
        optimized_query = self.query_optimizer.optimize(query)

        # Collect files
        files = collect_python_files(directory) if recursive else [
            f for f in directory.glob('*.py') if f.is_file()
        ]

        # Build call graph first if doing security analysis
        call_graph = None
        if query_type == 'security':
            call_graph = self._build_call_graph(files)

        # Analyze files
        results = []
        for file in files:
            try:
                # Check file size
                if file.stat().st_size > max_file_size:
                    logger.warning(f"Skipping large file {file} ({file.stat().st_size} bytes)")
                    continue

                # Get or create AST
                file_hash = self._get_file_hash(file)
                if file_hash in self._ast_cache:
                    ast = self._ast_cache[file_hash]
                else:
                    extractor = create_extractor(file)
                    ast = extractor.extract(file)
                    self._ast_cache[file_hash] = ast

                # Execute query
                file_results = self.query_executor.execute(ast, optimized_query, file)

                # Enhance security results with call graph data if available
                if query_type == 'security' and call_graph and file_results:
                    self._enhance_security_results(file_results, call_graph)

                if file_results:
                    results.extend(file_results)
            except Exception as e:
                logger.error(f"Failed to analyze {file}: {str(e)}")

        return {
            'directory': str(directory),
            'query_type': query_type,
            'pattern': pattern,
            'results': [
                {
                    'filepath': str(r.filepath),
                    'line_number': r.line_number,
                    'match_type': r.match_type,
                    'context': r.context,
                    'call_chain': getattr(r, 'call_chain', None)
                }
                for r in results
            ]
        }

    def calculate_metrics(
        self,
        path: Union[str, Path],
        recursive: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Calculate code metrics for a file or directory.

        Args:
            path: Path to analyze.
            recursive: Whether to analyze subdirectories.
            use_cache: Whether to use cached results.

        Returns:
            Dictionary containing metrics results.

        Raises:
            ValueError: If the path is invalid or unsafe.
        """
        path = Path(path).resolve()

        # Security check
        if not is_safe_path(path):
            raise SecurityError(f"Unsafe path: {path}")

        if path.is_file():
            return self._calculate_file_metrics(path, use_cache)
        elif path.is_dir():
            files = collect_python_files(path) if recursive else [
                f for f in path.glob('*.py') if f.is_file()
            ]

            results = []
            total_metrics = {}

            for file in files:
                try:
                    file_metrics = self._calculate_file_metrics(file, use_cache)
                    results.append(file_metrics)
                    self._update_total_metrics(total_metrics, file_metrics['metrics'])
                except Exception as e:
                    logger.error(f"Failed to calculate metrics for {file}: {str(e)}")

            return {
                'path': str(path),
                'total_metrics': total_metrics,
                'file_metrics': results
            }
        else:
            raise ValueError(f"Path does not exist: {path}")

    def _calculate_file_metrics(
        self,
        filepath: Path,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Calculate metrics for a single file.

        Args:
            filepath: Path to the file.
            use_cache: Whether to use cached results.

        Returns:
            Dictionary containing the metrics results.
        """
        if use_cache:
            file_hash = self._get_file_hash(filepath)
            if file_hash in self._metrics_cache:
                return self._metrics_cache[file_hash]

        extractor = create_extractor(filepath)
        model = create_model(filepath)

        # Get or create AST
        file_hash = self._get_file_hash(filepath)
        if file_hash in self._ast_cache:
            ast = self._ast_cache[file_hash]
        else:
            ast = extractor.extract(filepath)
            self._ast_cache[file_hash] = ast

        metrics = model.calculate_metrics(ast)
        result = {
            'filepath': str(filepath),
            'metrics': metrics
        }

        if use_cache:
            self._metrics_cache[file_hash] = result

        return result

    def _build_call_graph(self, files: List[Path]) -> Dict[str, CallGraphNode]:
        """Build a call graph from a list of Python files.

        Args:
            files: List of Python files to analyze.

        Returns:
            Dictionary mapping function names to CallGraphNode objects.
        """
        graph: Dict[str, CallGraphNode] = {}

        # First pass: collect all function definitions and calls
        for file in files:
            try:
                extractor = create_extractor(file)
                ast = extractor.extract(file)
                model = create_model(file)

                # Extract symbols (functions, methods)
                symbols = model.extract_symbols(ast)

                # Extract dependencies between symbols
                deps = model.analyze_dependencies(ast)

                # Add to graph
                for symbol in symbols:
                    if symbol.type in ('function', 'method'):
                        name = f"{symbol.module}.{symbol.name}" if hasattr(symbol, 'module') else symbol.name
                        if name not in graph:
                            graph[name] = CallGraphNode(
                                name=symbol.name,
                                module=getattr(symbol, 'module', ''),
                                calls=set(),
                                called_by=set()
                            )

                # Add dependencies
                for name, calls in deps.items():
                    if name in graph:
                        graph[name].calls.update(calls)
                        for called in calls:
                            if called in graph:
                                graph[called].called_by.add(name)

            except Exception as e:
                logger.error(f"Failed to build call graph for {file}: {str(e)}")

        # Second pass: calculate depths
        self._calculate_call_depths(graph)

        return graph

    def _calculate_call_depths(self, graph: Dict[str, CallGraphNode]) -> None:
        """Calculate the maximum call depth for each node in the graph.

        Args:
            graph: The call graph to analyze.
        """
        def calculate_depth(node: CallGraphNode, visited: Set[str]) -> int:
            if node.name in visited:
                return 0  # Prevent infinite recursion

            visited.add(node.name)
            max_depth = 0

            for called in node.calls:
                if called in graph:
                    depth = calculate_depth(graph[called], visited) + 1
                    max_depth = max(max_depth, depth)

            visited.remove(node.name)
            node.depth = max_depth
            return max_depth

        for node in graph.values():
            if node.depth == 0:  # Only calculate if not already done
                calculate_depth(node, set())

    def _enhance_security_results(
        self,
        results: List[Any],
        call_graph: Dict[str, CallGraphNode]
    ) -> None:
        """Enhance security results with call graph information.

        Args:
            results: List of query results to enhance.
            call_graph: The call graph to use for enhancement.
        """
        for result in results:
            if hasattr(result, 'match_value'):
                # Get the function containing this result
                containing_func = self._find_containing_function(result.match_value)
                if containing_func and containing_func in call_graph:
                    # Add call chain information
                    node = call_graph[containing_func]
                    result.call_chain = {
                        'depth': node.depth,
                        'called_by': list(node.called_by),
                        'calls': list(node.calls)
                    }

    def _find_containing_function(self, node: Any) -> Optional[str]:
        """Find the name of the function containing an AST node.

        Args:
            node: The AST node to find the containing function for.

        Returns:
            The function name if found, None otherwise.
        """
        # This is a simplified version - in practice, you'd need to
        # traverse up the AST to find the containing function
        return getattr(node, 'name', None)

    def _get_file_hash(self, filepath: Path) -> str:
        """Calculate a hash of a file's contents.

        Args:
            filepath: Path to the file.

        Returns:
            A string hash of the file contents.
        """
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _update_total_metrics(self, total: Dict, metrics: Dict) -> None:
        """Update total metrics with metrics from a single file.

        Args:
            total: Dictionary of total metrics to update.
            metrics: Metrics from a single file.
        """
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                total[key] = total.get(key, 0) + value
            elif isinstance(value, dict):
                if key not in total:
                    total[key] = {}
                self._update_total_metrics(total[key], value)

class SecurityError(Exception):
    """Raised when a security constraint is violated."""
    pass
