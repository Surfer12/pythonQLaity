"""Computer interaction module.

This module provides interfaces for interacting with the computer environment,
including file operations, command execution, and system monitoring.
"""

import platform
from typing import Optional, Union
from pathlib import Path

from .base import BaseComputer, CommandError, FileOperationError
from .unix import UnixComputer

def create_computer(
    working_dir: Optional[Union[str, Path]] = None
) -> BaseComputer:
    """Create a computer interface appropriate for the current system.

    Args:
        working_dir: The working directory for operations.
            Defaults to the current directory.

    Returns:
        A computer interface instance.

    Raises:
        RuntimeError: If no suitable implementation is available.
    """
    system = platform.system().lower()

    if system in ('linux', 'darwin'):
        return UnixComputer(working_dir)
    else:
        raise RuntimeError(
            f"No computer implementation available for system: {system}"
        )

# Expose key classes and exceptions
__all__ = [
    'BaseComputer',
    'CommandError',
    'FileOperationError',
    'UnixComputer',
    'create_computer'
]
