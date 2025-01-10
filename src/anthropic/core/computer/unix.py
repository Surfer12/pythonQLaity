"""Unix implementation of computer interaction."""

import os
import shutil
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import BaseComputer, CommandError, FileOperationError

class UnixComputer(BaseComputer):
    """Unix implementation of computer interaction."""

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
        try:
            # Use working directory if cwd not specified
            if cwd is None:
                cwd = self.working_dir

            # Merge environment variables with current environment
            full_env = os.environ.copy()
            if env:
                full_env.update(env)

            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env=full_env,
                timeout=timeout,
                check=check,
                text=True,
                capture_output=True
            )
            return result

        except subprocess.CalledProcessError as e:
            raise CommandError(
                f"Command failed with exit code {e.returncode}: {e.stderr}"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise CommandError(
                f"Command timed out after {timeout} seconds"
            ) from e
        except Exception as e:
            raise CommandError(f"Command execution failed: {str(e)}") from e

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
        path = self.resolve_path(path)
        mode = 'rb' if binary else 'r'

        try:
            with open(path, mode) as f:
                return f.read()
        except Exception as e:
            raise FileOperationError(
                f"Failed to read file {path}: {str(e)}"
            ) from e

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
        path = self.resolve_path(path)
        mode = 'wb' if binary else 'w'

        try:
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, mode) as f:
                f.write(content)
        except Exception as e:
            raise FileOperationError(
                f"Failed to write file {path}: {str(e)}"
            ) from e

    def delete_file(self, path: Union[str, Path]) -> None:
        """Delete a file.

        Args:
            path: Path to the file.

        Raises:
            FileOperationError: If the file cannot be deleted.
        """
        path = self.resolve_path(path)

        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            else:
                raise FileOperationError(f"Path does not exist: {path}")
        except Exception as e:
            raise FileOperationError(
                f"Failed to delete {path}: {str(e)}"
            ) from e

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
        path = self.resolve_path(path)

        try:
            if recursive:
                matches = list(path.rglob(pattern))
            else:
                matches = list(path.glob(pattern))
            return sorted(matches)
        except Exception as e:
            raise FileOperationError(
                f"Failed to list directory {path}: {str(e)}"
            ) from e

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
        path = self.resolve_path(path)

        try:
            path.mkdir(parents=parents, exist_ok=exist_ok)
        except Exception as e:
            raise FileOperationError(
                f"Failed to create directory {path}: {str(e)}"
            ) from e

    def get_file_info(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Get information about a file.

        Args:
            path: Path to the file.

        Returns:
            Dictionary containing file information:
                - size: File size in bytes
                - created: Creation timestamp
                - modified: Last modified timestamp
                - accessed: Last accessed timestamp
                - mode: File mode and permissions
                - type: File type (file, directory, link, etc.)

        Raises:
            FileOperationError: If the file information cannot be retrieved.
        """
        path = self.resolve_path(path)

        try:
            stat_result = path.stat()

            # Determine file type
            if path.is_file():
                file_type = 'file'
            elif path.is_dir():
                file_type = 'directory'
            elif path.is_symlink():
                file_type = 'link'
            else:
                file_type = 'other'

            return {
                'size': stat_result.st_size,
                'created': datetime.fromtimestamp(stat_result.st_ctime),
                'modified': datetime.fromtimestamp(stat_result.st_mtime),
                'accessed': datetime.fromtimestamp(stat_result.st_atime),
                'mode': stat.filemode(stat_result.st_mode),
                'type': file_type
            }
        except Exception as e:
            raise FileOperationError(
                f"Failed to get file info for {path}: {str(e)}"
            ) from e
