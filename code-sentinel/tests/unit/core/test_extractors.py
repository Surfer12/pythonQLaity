import pytest
from pathlib import Path
from typing import Dict, Any

from core.extractors.python_extractor import PythonExtractor

@pytest.fixture
def python_extractor():
    """Create a PythonExtractor instance for testing."""
    return PythonExtractor()

@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file for testing."""
    content = '''
import os
from typing import List, Optional

CONSTANT = 42

class MyClass:
    """A sample class."""

    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"

def main(args: List[str]) -> Optional[int]:
    """Main function."""
    if not args:
        return None
    return len(args)

if __name__ == "__main__":
    main([])
'''
    file_path = tmp_path / "sample.py"
    file_path.write_text(content)
    return file_path

def test_supports_file(python_extractor):
    """Test file support detection."""
    assert python_extractor.supports_file(Path("test.py"))
    assert python_extractor.supports_file(Path("test.pyi"))
    assert not python_extractor.supports_file(Path("test.txt"))
    assert not python_extractor.supports_file(Path("test.js"))

def test_get_supported_extensions(python_extractor):
    """Test supported extensions list."""
    extensions = python_extractor.get_supported_extensions()
    assert ".py" in extensions
    assert ".pyi" in extensions
    assert len(extensions) == 2

def test_extract_imports(python_extractor, sample_python_file):
    """Test import statement extraction."""
    result = python_extractor.extract(sample_python_file)
    imports = result["imports"]

    assert len(imports) == 3
    assert any(imp["type"] == "import" and imp["name"] == "os" for imp in imports)
    assert any(imp["type"] == "import_from" and imp["name"] == "List" for imp in imports)
    assert any(imp["type"] == "import_from" and imp["name"] == "Optional" for imp in imports)

def test_extract_classes(python_extractor, sample_python_file):
    """Test class definition extraction."""
    result = python_extractor.extract(sample_python_file)
    classes = result["classes"]

    assert len(classes) == 1
    class_info = classes[0]
    assert class_info["name"] == "MyClass"
    assert len(class_info["methods"]) == 2

    method_names = {method["name"] for method in class_info["methods"]}
    assert "__init__" in method_names
    assert "greet" in method_names

def test_extract_functions(python_extractor, sample_python_file):
    """Test function definition extraction."""
    result = python_extractor.extract(sample_python_file)
    functions = result["functions"]

    assert len(functions) == 1
    function_info = functions[0]
    assert function_info["name"] == "main"
    assert function_info["returns"] == "Optional[int]"
    assert "args" in function_info["args"]

def test_extract_global_variables(python_extractor, sample_python_file):
    """Test global variable extraction."""
    result = python_extractor.extract(sample_python_file)
    variables = result["global_variables"]

    assert len(variables) == 1
    assert variables[0]["name"] == "CONSTANT"

def test_invalid_python_file(python_extractor, tmp_path):
    """Test handling of invalid Python files."""
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text("class Invalid:")  # Missing required pass statement

    with pytest.raises(SyntaxError):
        python_extractor.extract(invalid_file)

def test_missing_file(python_extractor):
    """Test handling of missing files."""
    with pytest.raises(FileNotFoundError):
        python_extractor.extract(Path("nonexistent.py"))

def test_non_python_file(python_extractor, tmp_path):
    """Test handling of non-Python files."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("Not a Python file")

    with pytest.raises(ValueError):
        python_extractor.extract(text_file)
