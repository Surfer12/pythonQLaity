from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

class BaseExtractor(ABC):
    """Abstract base class for language-specific code extractors."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the extractor with optional configuration.

        Args:
            config: Optional configuration dictionary for the extractor.
        """
        self.config = config or {}
        self.max_file_size = self.config.get("max_file_size", 10 * 1024 * 1024)  # 10MB default
        self.exclude_patterns = self.config.get("exclude_patterns", [])

    @abstractmethod
    def extract(self, file_path: Path) -> Dict[str, Any]:
        """Extract code information from a file.

        Args:
            file_path: Path to the file to analyze.

        Returns:
            Dictionary containing extracted code information.

        Raises:
            ValueError: If the file is not supported or cannot be read.
            IOError: If there are issues reading the file.
        """
        pass

    @abstractmethod
    def supports_file(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file is supported, False otherwise.
        """
        pass

    def should_exclude(self, file_path: Path) -> bool:
        """Check if the file should be excluded based on patterns.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file should be excluded, False otherwise.
        """
        from pathlib import Path
        import fnmatch

        str_path = str(file_path)
        return any(fnmatch.fnmatch(str_path, pattern) for pattern in self.exclude_patterns)

    def validate_file(self, file_path: Path) -> None:
        """Validate that a file can be processed.

        Args:
            file_path: Path to the file to validate.

        Raises:
            ValueError: If the file is not valid for processing.
            IOError: If there are issues accessing the file.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        if file_path.stat().st_size > self.max_file_size:
            raise ValueError(
                f"File size ({file_path.stat().st_size} bytes) exceeds maximum "
                f"allowed size ({self.max_file_size} bytes)"
            )

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get the list of file extensions supported by this extractor.

        Returns:
            List of supported file extensions (e.g., [".py", ".pyi"]).
        """
        pass
