from pathlib import Path
from typing import Type

from .base_extractor import BaseExtractor
from .python_extractor import PythonExtractor

__all__ = ['BaseExtractor', 'PythonExtractor', 'create_extractor']

# Registry of file extensions to extractor classes
EXTRACTORS = {
    '.py': PythonExtractor,
}

def create_extractor(filepath: Path) -> BaseExtractor:
    """Factory function to create an appropriate extractor for a given file.

    Args:
        filepath: Path to the file that needs to be analyzed.

    Returns:
        An instance of the appropriate extractor for the file type.

    Raises:
        ValueError: If no suitable extractor is found for the file type.
    """
    suffix = filepath.suffix.lower()
    extractor_class = EXTRACTORS.get(suffix)

    if extractor_class is None:
        raise ValueError(f"No extractor available for file type: {suffix}")

    return extractor_class()
