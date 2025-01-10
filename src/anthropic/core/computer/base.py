"""Base computer interaction functionality.

This module provides the core abstractions for interacting with the computer
environment, including file operations, command execution, and system monitoring.
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utils.logging_utils import setup_logger
from ..utils.path_utils import normalize_path

logger = setup_logger('code_sentinel.computer')

class ComputerError(Exception):
    """Base exception for computer interaction errors."""
    pass

class CommandError(ComputerError):
    """Raised when a command execution fails."""
    pass

class FileOperationError(ComputerError):
    """Raised when a file operation fails."""
    pass

class BaseComputer(ABC):
    """Abstract base class for computer interaction.

    This class defines the interface for interacting with the computer
    environment. Concrete implementations should handle the specifics
    of different operating systems and environments.
    """

    def __init__(self, working_dir: Optional[Union[str, Path]] = None):
        """Initialize the computer interface.

        Args:
            working_dir: The working directory for operations.
                Defaults to the current directory.
        """
        self.working_dir = Path(working_dir or Path.cwd()).resolve()

    @abstractmethod
    def execute_command(
        self,
        command: str,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """Execute a shell command.

        Args:
            command: The command to execute.
            cwd: Working directory for the command.
            env: Environment variables for the command.
            timeout: Timeout in seconds.
            check: Whether to check the return code.

        Returns:
            The completed process.

        Raises:
            CommandError: If the command fails and check is True.
        """
        pass

    @abstractmethod
    def read_file(
        self,
        path: Union[str, Path],
        binary: bool = False
    ) -> Union[str, bytes]:
        """Read the contents of a file.

        Args:
            path: Path to the file.
            binary: Whether to read in binary mode.

        Returns:
            The file contents.

        Raises:
            FileOperationError: If the file cannot be read.
        """
        pass

    @abstractmethod
    def write_file(
        self,
        path: Union[str, Path],
        content: Union[str, bytes],
        binary: bool = False
    ) -> None:
        """Write content to a file.

        Args:
            path: Path to the file.
            content: Content to write.
            binary: Whether to write in binary mode.

        Raises:
            FileOperationError: If the file cannot be written.
        """
        pass

    @abstractmethod
    def delete_file(self, path: Union[str, Path]) -> None:
        """Delete a file.

        Args:
            path: Path to the file.

        Raises:
            FileOperationError: If the file cannot be deleted.
        """
        pass

    @abstractmethod
    def list_directory(
        self,
        path: Optional[Union[str, Path]] = None,
        pattern: str = '*',
        recursive: bool = False
    ) -> List[Path]:
        """List files in a directory.

        Args:
            path: Directory path. Defaults to working directory.
            pattern: Glob pattern for matching files.
            recursive: Whether to search recursively.

        Returns:
            List of matching file paths.

        Raises:
            FileOperationError: If the directory cannot be read.
        """
        pass

    @abstractmethod
    def create_directory(
        self,
        path: Union[str, Path],
        parents: bool = True,
        exist_ok: bool = True
    ) -> None:
        """Create a directory.

        Args:
            path: Directory path.
            parents: Whether to create parent directories.
            exist_ok: Whether to ignore existing directory.

        Raises:
            FileOperationError: If the directory cannot be created.
        """
        pass

    @abstractmethod
    def get_file_info(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Get information about a file.

        Args:
            path: Path to the file.

        Returns:
            Dictionary containing file information (size, modified time, etc.).

        Raises:
            FileOperationError: If the file information cannot be retrieved.
        """
        pass

    def resolve_path(self, path: Optional[Union[str, Path]] = None) -> Path:
        """Resolve a path relative to the working directory.

        Args:
            path: The path to resolve. Defaults to working directory.

        Returns:
            The resolved absolute path.
        """
        if path is None:
            return self.working_dir
        return normalize_path(self.working_dir / Path(path))

    def change_directory(self, path: Union[str, Path]) -> None:
        """Change the working directory.

        Args:
            path: The new working directory.

        Raises:
            FileOperationError: If the directory does not exist or is not accessible.
        """
        path = normalize_path(path)
        if not path.is_dir():
            raise FileOperationError(f"Directory does not exist: {path}")
        self.working_dir = path
