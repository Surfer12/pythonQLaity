# Code Sentinel Integration for Anthropic Computer Use Demo

This project integrates Code Sentinel's static analysis capabilities with the Anthropic Computer Use Demo, providing enhanced security, code quality, and maintainability analysis for Python codebases.

## Features

- **Pre-execution Analysis**
  - Shell command security validation
  - File content analysis
  - Path safety checks
  - AST-based code analysis

- **Runtime Monitoring**
  - Continuous event monitoring
  - Anomaly detection
  - Security policy enforcement
  - Rate limiting and threshold checks

- **Security Policies**
  - Configurable allowed paths
  - Blocked command patterns
  - File size limits
  - Permission controls

- **Call Graph Analysis**
  - Function dependency tracking
  - Call chain depth analysis
  - Cross-function vulnerability detection

- **Reporting**
  - Session analysis reports
  - Security incident tracking
  - Risk assessment
  - Metrics aggregation

## Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows

# Install the package
pip install -e .
```

## Usage

### Basic Usage

```python
from anthropic.tools import AnalysisTool

# Create an analysis tool instance
tool = AnalysisTool()

# Analyze a shell command
result = tool.analyze_command('rm -rf /tmp/test')
if not result['is_safe']:
    print(f"Warning: {result['warnings']}")

# Analyze file content
with open('script.py', 'r') as f:
    content = f.read()
    result = tool.analyze_file_content('script.py', content)
    if not result['is_safe']:
        print(f"Security issues found: {result['warnings']}")
```

### Continuous Monitoring

```python
# Start continuous monitoring
monitor = tool.start_continuous_monitoring()

try:
    # Process events as they occur
    for event in event_stream:
        result = monitor.process_event(event)
        if not result['is_safe']:
            print(f"Security alert: {result['warnings']}")
finally:
    monitor.stop()
```

### Custom Security Policies

```python
# Configure security policy
policy = {
    'allowed_paths': ['/home/user', '/tmp'],
    'blocked_commands': ['rm -rf', 'chmod -R'],
    'max_file_size': 1024 * 1024,  # 1MB
    'required_permissions': ['read', 'write']
}
tool.set_security_policy(policy)
```

## Testing

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest src/anthropic/tests/unit/tools/test_analysis.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project uses dual licensing:

- The Code Sentinel Integration components are licensed under the MIT License
- The CodeQL components are licensed under the Apache License 2.0

See the [LICENSE](LICENSE) file for full details.

## Acknowledgments

- Anthropic Computer Use Demo team
- Code Sentinel developers
- GitHub CodeQL team
- Contributors to the Python AST and static analysis tools
