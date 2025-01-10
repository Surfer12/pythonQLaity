import ast
from pathlib import Path
from typing import Any

from .base_extractor import BaseExtractor

class PythonExtractor(BaseExtractor):
    """Python-specific code extractor.

    This extractor handles Python source files, using Python's built-in ast
    module to parse code into an abstract syntax tree.
    """

    def supports_file(self, filepath: Path) -> bool:
        """Check if the file is a Python source file.

        Args:
            filepath: Path to check for support.

        Returns:
            True if the file has a .py extension, False otherwise.
        """
        return filepath.suffix.lower() == '.py'

    def extract(self, filepath: Path) -> Any:
        """Extract Python code into an AST representation.

        Args:
            filepath: Path to the Python source file to analyze.

        Returns:
            ast.AST: The AST representation of the Python code.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            PermissionError: If the file cannot be accessed.
            ValueError: If the file is not a valid Python file.
            SyntaxError: If the Python code contains syntax errors.
        """
        if not self.supports_file(filepath):
            raise ValueError(f"File {filepath} is not a Python file")

        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} does not exist")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            return ast.parse(source, filename=str(filepath))
        except SyntaxError as e:
            # Re-raise syntax errors with more context
            raise SyntaxError(
                f"Syntax error in {filepath}: {str(e)}"
            ) from e
        except Exception as e:
            # Convert other errors to ValueError with context
            raise ValueError(
                f"Failed to parse {filepath}: {str(e)}"
            ) from e
