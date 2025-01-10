# Code Sentinel

A powerful static analysis tool for code quality and security.

## Features

- Advanced code analysis using custom query language
- Support for multiple programming languages (currently Python)
- Extensible architecture for adding new language support
- Rich command-line interface with progress tracking
- Configurable analysis rules and patterns
- Database storage for analysis results
- Integration with development workflows

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/code-sentinel.git
cd code-sentinel

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package with development dependencies
pip install -e ".[dev]"
```

## Usage

Basic usage:

```bash
# Analyze a project
code-sentinel analyze /path/to/project

# Run a specific query
code-sentinel query "find-security-issues" /path/to/project

# Configure settings
code-sentinel config set extractors.python.enabled true
```

For more detailed usage instructions, see the [User Guide](docs/user_guide.md).

## Development

### Setting up the development environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linters
flake8
black .
isort .
```

### Project Structure

```
code-sentinel/
├── core/                 # Core analysis engine
├── cli/                  # Command-line interface
├── config/              # Configuration management
├── db/                  # Database management
├── tests/              # Test suite
└── tools/              # Development tools
```

For more details about the project structure and development guidelines, see [Contributing](docs/contributing.md).

## Documentation

- [User Guide](docs/user_guide.md)
- [API Reference](docs/api_reference.md)
- [Contributing](docs/contributing.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](docs/contributing.md) first.
