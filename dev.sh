#!/bin/bash

# Set the ANTHROPIC_API_KEY environment variable
export ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Set project root to the analysis-of-prompts-v0.2 directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add paths to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT:$PYTHONPATH"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Function to display usage
usage() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Development Modes:"
    echo "  setup           - Set up development environment"
    echo "  clean          - Clean up generated files and caches"
    echo "  format         - Format code using black and isort"
    echo ""
    echo "Testing Modes:"
    echo "  test           - Run all tests"
    echo "  test-tools     - Run tool-specific tests"
    echo "  test-unit      - Run unit tests only"
    echo "  test-int       - Run integration tests only"
    echo ""
    echo "Anthropic Tools:"
    echo "  claude         - Run Claude interface (Streamlit)"
    echo "  claude-ref     - Run reference Claude implementation"
    echo "  tools          - List available Claude tools"
    echo ""
    echo "Environment:"
    echo "  docker         - Build and run Docker environment"
    echo "  docker-dev     - Run development Docker environment"
    echo "  help           - Show this help message"
}

# Function to set up Python virtual environment
setup_venv() {
    echo "Setting up Python virtual environment..."
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        python3 -m venv "$PROJECT_ROOT/.venv"
    fi
    source "$PROJECT_ROOT/.venv/bin/activate"

    # Install requirements
    pip install -r "$PROJECT_ROOT/requirements.txt"
    pip install -r "$PROJECT_ROOT/requirements-dev.txt"

    # Install pre-commit hooks
    if [ -f "$PROJECT_ROOT/utils/pre-commit" ]; then
        pip install -r "$PROJECT_ROOT/utils/pre-commit"
        pre-commit install
    fi

    # Run setup.sh if it exists
    if [ -f "$PROJECT_ROOT/setup.sh" ]; then
        echo "Running setup.sh..."
        bash "$PROJECT_ROOT/setup.sh"
    fi
}

# Function to clean up generated files
clean() {
    echo "Cleaning up generated files..."
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type d -name "*.egg-info" -exec rm -r {} +
    find . -type d -name ".pytest_cache" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type f -name ".coverage" -delete
    find . -type d -name "htmlcov" -exec rm -r {} +
}

# Function to format code
format_code() {
    echo "Formatting code..."
    source "$PROJECT_ROOT/.venv/bin/activate"
    black src tests
    isort src tests
}

# Function to run tests
run_tests() {
    local test_path="$1"
    local test_type="$2"
    echo "Running tests in $test_path..."

    source "$PROJECT_ROOT/.venv/bin/activate"

    if [ -n "$test_type" ]; then
        PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH" pytest "$test_path" -v -k "$test_type"
    else
        PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH" pytest "$test_path" -v
    fi
}

# Function to build and run Docker
setup_docker() {
    local env="$1"
    echo "Setting up Docker environment..."

    if [ "$env" = "dev" ]; then
        docker-compose -f docker-compose.dev.yml up --build
    else
        docker build -t analysis-of-prompts:latest -f Dockerfile .
        docker run -it \
            -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
            -v "$PROJECT_ROOT":/app \
            -v "$HOME/.anthropic":/root/.anthropic \
            -p 8888:8888 \
            analysis-of-prompts:latest
    fi
}

# Function to run Claude interface
run_claude() {
    echo "Starting Claude interface..."
    source "$PROJECT_ROOT/.venv/bin/activate"

    if [ "$1" = "ref" ]; then
        echo "Running reference implementation..."
        streamlit run "$PROJECT_ROOT/references/anthropic-quickstarts/computer-use-demo/computer_use_demo/streamlit.py"
    else
        echo "Running project implementation..."
        streamlit run "$PROJECT_ROOT/src/anthropic/interfaces/streamlit_app.py"
    fi
}

# Function to list available Claude tools
list_tools() {
    echo "Available Claude tools:"
    echo "----------------------"
    ls -1 "$PROJECT_ROOT/src/anthropic/tools"
}

# Main setup function
setup() {
    setup_venv
    echo "Environment setup complete"
}

# Main script logic
case "$1" in
    setup)
        setup
        ;;
    clean)
        clean
        ;;
    format)
        format_code
        ;;
    test)
        run_tests "$PROJECT_ROOT/tests"
        ;;
    test-tools)
        run_tests "$PROJECT_ROOT/tests/test_tools"
        ;;
    test-unit)
        run_tests "$PROJECT_ROOT/tests" "unit"
        ;;
    test-int)
        run_tests "$PROJECT_ROOT/tests" "integration"
        ;;
    claude)
        run_claude
        ;;
    claude-ref)
        run_claude ref
        ;;
    tools)
        list_tools
        ;;
    docker)
        setup_docker
        ;;
    docker-dev)
        setup_docker dev
        ;;
    help|*)
        usage
        ;;
esac
