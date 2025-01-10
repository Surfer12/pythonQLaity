# Code Sentinel Integration with Anthropic Computer Use Demo

This project integrates Code Sentinel's static analysis capabilities with the Anthropic Computer Use Demo, enabling automated code quality, security, and maintainability analysis through LLM-based interactions.

## Features

- Pre-execution code analysis for security and quality checks
- Runtime monitoring of system events and file accesses
- Comprehensive metrics calculation and reporting
- Integration with the agentic sampling loop
- Interactive code analysis through LLM commands
- Security policy enforcement and anomaly detection

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

2. Install the package:
```bash
pip install -e .
```

## Usage

1. Start the Streamlit UI:
```bash
python -m computer_use_demo.streamlit
```

2. Use natural language commands to analyze code:
```
Analyze the security of files in the src directory
Calculate metrics for the project
Generate a report of the last session
```

## Project Structure

```
src/
├── anthropic/
│   ├── core/
│   │   ├── computer/       # Base computer interaction
│   │   └── utils/          # Utility functions
│   └── tools/
│       ├── analysis.py     # Code Sentinel integration
│       ├── computer.py     # Computer interaction tools
│       └── edit.py         # Code editing tools
└── tests/
    └── unit/
        └── tools/
            └── test_analysis.py  # Analysis tool tests
```

## License

This project is dual-licensed:
- Code Sentinel Integration components are licensed under the MIT License
- CodeQL components are licensed under the Apache License 2.0

See the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Security

Please report security issues to security@anthropic.com
