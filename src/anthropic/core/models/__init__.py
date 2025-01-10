from pathlib import Path
from typing import Type

from .base_model import BaseModel, CodeLocation, CodeSymbol
from .python_model import PythonModel

__all__ = [
    'BaseModel',
    'CodeLocation',
    'CodeSymbol',
    'PythonModel',
    'create_model'
]

# Registry of file extensions to model classes
MODELS = {
    '.py': PythonModel,
}

def create_model(filepath: Path) -> BaseModel:
    """Factory function to create an appropriate model for a given file.

    Args:
        filepath: Path to the file that needs to be analyzed.

    Returns:
        An instance of the appropriate model for the file type.

    Raises:
        ValueError: If no suitable model is found for the file type.
    """
    suffix = filepath.suffix.lower()
    model_class = MODELS.get(suffix)

    if model_class is None:
        raise ValueError(f"No model available for file type: {suffix}")

    return model_class()
