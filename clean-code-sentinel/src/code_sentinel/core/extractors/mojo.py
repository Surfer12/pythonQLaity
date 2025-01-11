"""Mojo code extractor implementation."""

import os
from pathlib import Path
from typing import Dict, List, Optional

from .base import CodeExtractor

class MojoExtractor(CodeExtractor):
    """Extractor for Mojo code files."""

    def extract_code(self, path: Path) -> Dict[str, str]:
        """Extract code from Mojo files.

        Args:
            path: Path to file or directory to extract code from

        Returns:
            Dictionary mapping file paths to their contents
        """
        results = {}

        if path.is_file() and self.can_handle_file(path):
            with open(path, 'r', encoding='utf-8') as f:
                results[str(path)] = f.read()
        elif path.is_dir():
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    if self.can_handle_file(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            results[str(file_path)] = f.read()

        return results

    def get_supported_extensions(self) -> List[str]:
        """Get list of Mojo file extensions.

        Returns:
            List of supported file extensions
        """
        return ['.mojo', '.🔥']  # .mojo is standard, .🔥 is unofficial but used

    def can_handle_file(self, path: Path) -> bool:
        """Check if file is a Mojo source file.

        Args:
            path: Path to file to check

        Returns:
            True if file is a Mojo source file, False otherwise
        """
        return path.suffix in self.get_supported_extensions()

    def get_file_type(self, path: Path) -> Optional[str]:
        """Get the type of a Mojo file.

        Args:
            path: Path to file to check

        Returns:
            'mojo' if file is a Mojo source file, None otherwise
        """
        return 'mojo' if self.can_handle_file(path) else None
