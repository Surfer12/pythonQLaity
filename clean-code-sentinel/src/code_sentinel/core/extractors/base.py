"""Abstract base classes for code extractors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

class CodeExtractor(ABC):
    """Abstract base class for code extractors."""

    @abstractmethod
    def extract_code(self, path: Path) -> Dict[str, str]:
        """Extract code from a file or directory.

        Args:
            path: Path to file or directory to extract code from

        Returns:
            Dictionary mapping file paths to their contents
        """
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get list of file extensions this extractor supports.

        Returns:
            List of supported file extensions (e.g. ['.py', '.mojo'])
        """
        pass

    @abstractmethod
    def can_handle_file(self, path: Path) -> bool:
        """Check if this extractor can handle a given file.

        Args:
            path: Path to file to check

        Returns:
            True if this extractor can handle the file, False otherwise
        """
        pass

    @abstractmethod
    def get_file_type(self, path: Path) -> Optional[str]:
        """Get the type of a file.

        Args:
            path: Path to file to check

        Returns:
            String identifying the file type, or None if unknown
        """
        pass
