from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

class BaseExtractor(ABC):
    """Base class for all language-specific code extractors.

    This abstract base class defines the interface that all language-specific
    extractors must implement. It provides the foundation for extracting code
    into an abstract syntax tree (AST) representation.
    """

    @abstractmethod
    def extract(self, filepath: Path) -> Any:
        """Extract code from a file into an AST representation.

        Args:
            filepath: Path to the source code file to analyze.

        Returns:
            The AST representation of the code.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            PermissionError: If the file cannot be accessed.
            ValueError: If the file is not valid for this extractor.
        """
        pass

    @abstractmethod
    def supports_file(self, filepath: Path) -> bool:
        """Check if this extractor supports the given file.

        Args:
            filepath: Path to check for support.

        Returns:
            True if this extractor can handle the file, False otherwise.
        """
        pass
