"""Utility functions for path manipulation and project root detection."""

import os
from pathlib import Path
from typing import List, Optional, Set, Union

def find_project_root(
    start_path: Union[str, Path],
    marker_files: Optional[List[str]] = None
) -> Optional[Path]:
    """Find the project root directory by looking for marker files.

    Args:
        start_path: Path to start searching from.
        marker_files: List of files that indicate the project root.
            Defaults to ['.git', 'pyproject.toml', 'setup.py'].

    Returns:
        The project root path, or None if not found.
    """
    if marker_files is None:
        marker_files = ['.git', 'pyproject.toml', 'setup.py']

    start_path = Path(start_path).resolve()

    for path in [start_path, *start_path.parents]:
        if any((path / marker).exists() for marker in marker_files):
            return path

    return None

def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize a path by resolving symlinks and making it absolute.

    Args:
        path: The path to normalize.

    Returns:
        The normalized path.
    """
    return Path(path).resolve()

def is_subpath(path: Union[str, Path], parent: Union[str, Path]) -> bool:
    """Check if a path is a subpath of another path.

    Args:
        path: The path to check.
        parent: The potential parent path.

    Returns:
        True if path is a subpath of parent, False otherwise.
    """
    path = normalize_path(path)
    parent = normalize_path(parent)

    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: The directory path.

    Returns:
        The path to the directory.

    Raises:
        OSError: If the directory cannot be created.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def list_files(
    directory: Union[str, Path],
    pattern: str = '*',
    recursive: bool = True,
    exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """List files in a directory matching a pattern.

    Args:
        directory: The directory to search.
        pattern: Glob pattern for matching files.
        recursive: Whether to search recursively.
        exclude_patterns: List of patterns to exclude.

    Returns:
        List of matching file paths.
    """
    directory = Path(directory)

    if exclude_patterns is None:
        exclude_patterns = []

    # Convert exclude patterns to set of Path objects for faster lookup
    excluded = set()
    for exclude in exclude_patterns:
        excluded.update(directory.glob(exclude))

    # Find matching files
    if recursive:
        matches = directory.rglob(pattern)
    else:
        matches = directory.glob(pattern)

    # Filter out excluded files and directories
    return [
        path for path in matches
        if path.is_file() and path not in excluded
    ]

def get_relative_path(
    path: Union[str, Path],
    relative_to: Union[str, Path]
) -> Path:
    """Get a path relative to another path.

    Args:
        path: The path to make relative.
        relative_to: The reference path.

    Returns:
        The relative path.

    Raises:
        ValueError: If the path cannot be made relative.
    """
    path = normalize_path(path)
    relative_to = normalize_path(relative_to)

    try:
        return path.relative_to(relative_to)
    except ValueError as e:
        raise ValueError(
            f"Cannot make {path} relative to {relative_to}"
        ) from e

def get_file_type(path: Union[str, Path]) -> str:
    """Get the type of a file based on its extension.

    Args:
        path: Path to the file.

    Returns:
        The file type (e.g., 'py', 'js', 'txt').
    """
    return Path(path).suffix.lstrip('.')

def is_binary_file(path: Union[str, Path]) -> bool:
    """Check if a file is binary.

    Args:
        path: Path to the file.

    Returns:
        True if the file is binary, False otherwise.
    """
    try:
        with open(path, 'tr') as f:
            f.read(1024)
        return False
    except UnicodeDecodeError:
        return True
