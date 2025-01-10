"""Base extractor module defining the interface for code extraction."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

class BaseExtractor(ABC):
    """Abstract base class for code extractors.

    This class defines the interface that all language-specific extractors must implement.
    It provides the foundation for extracting code elements and relationships from source files.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the extractor with optional configuration.

        Args:
            config: Optional configuration dictionary for customizing extraction behavior
        """
        self.config = config or {}
        self._extracted_files: Set[Path] = set()

    @abstractmethod
    def extract_file(self, file_path: Path) -> Dict[str, Any]:
        """Extract code elements from a single file.

        Args:
            file_path: Path to the source file

        Returns:
            Dictionary containing extracted code elements and relationships

        Raises:
            FileNotFoundError: If the file does not exist
            ExtractionError: If extraction fails
        """
        pass

    @abstractmethod
    def supports_file(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file.

        Args:
            file_path: Path to check

        Returns:
            True if this extractor can handle the file, False otherwise
        """
        pass

    def extract_directory(self, dir_path: Path, recursive: bool = True) -> List[Dict[str, Any]]:
        """Extract code elements from all supported files in a directory.

        Args:
            dir_path: Path to the directory
            recursive: Whether to recursively process subdirectories

        Returns:
            List of dictionaries containing extracted code elements and relationships

        Raises:
            NotADirectoryError: If dir_path is not a directory
        """
        if not dir_path.is_dir():
            raise NotADirectoryError(f"{dir_path} is not a directory")

        results = []
        pattern = "**/*" if recursive else "*"

        for file_path in dir_path.glob(pattern):
            if file_path.is_file() and self.supports_file(file_path):
                try:
                    result = self.extract_file(file_path)
                    results.append(result)
                    self._extracted_files.add(file_path)
                except Exception as e:
                    # Log error but continue processing other files
                    print(f"Error extracting {file_path}: {e}")

        return results

    def get_extracted_files(self) -> Set[Path]:
        """Get the set of files that have been processed.

        Returns:
            Set of Path objects for files that have been extracted
        """
        return self._extracted_files.copy()

    def clear_extracted_files(self) -> None:
        """Clear the set of extracted files."""
        self._extracted_files.clear()
