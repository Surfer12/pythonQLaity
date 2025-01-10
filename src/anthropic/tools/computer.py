"""Tools for computer interaction and file operations."""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .base import BaseTool, ToolResult

class ComputerTool(BaseTool):
    """Base class for computer interaction tools."""

    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize the computer tool.

        Args:
            workspace_root: Root directory for operations. Defaults to current directory.
        """
        self.workspace_root = workspace_root or Path.cwd()

    def _resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path to an absolute path within the workspace.

        Args:
            relative_path: Path relative to workspace root

        Returns:
            Absolute path
        """
        return (self.workspace_root / relative_path).resolve()

    def _validate_path(self, path: Path) -> None:
        """
        Validate that a path is within the workspace.

        Args:
            path: Path to validate

        Raises:
            ValueError: If path is outside workspace
        """
        try:
            path.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError(
                f"Path {path} is outside workspace root {self.workspace_root}"
            )

class FileReadTool(ComputerTool):
    """Tool for reading file contents."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read contents of a file. Returns lines from start to end index "
            "and summary of other lines."
        )

    @property
    def parameters(self) -> Dict[str, Dict]:
        return {
            "relative_path": {
                "type": "string",
                "description": "Path relative to workspace root",
            },
            "start_line": {
                "type": "integer",
                "description": "Starting line number (1-indexed)",
            },
            "end_line": {
                "type": "integer",
                "description": "Ending line number (1-indexed)",
            },
        }

    async def execute(
        self,
        relative_path: str,
        start_line: int,
        end_line: int,
    ) -> str:
        """
        Read specified lines from a file.

        Args:
            relative_path: Path to file relative to workspace
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed)

        Returns:
            Contents of specified lines and summary
        """
        path = self._resolve_path(relative_path)
        self._validate_path(path)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path) as f:
            lines = f.readlines()

        # Adjust indices
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)

        # Get requested lines
        content = "".join(lines[start_idx:end_idx])

        # Add summary of other lines
        if start_idx > 0:
            content = f"[Lines 1-{start_idx} omitted]\n" + content
        if end_idx < len(lines):
            content += f"\n[Lines {end_idx + 1}-{len(lines)} omitted]"

        return content

class FileWriteTool(ComputerTool):
    """Tool for writing to files."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file."

    @property
    def parameters(self) -> Dict[str, Dict]:
        return {
            "relative_path": {
                "type": "string",
                "description": "Path relative to workspace root",
            },
            "content": {
                "type": "string",
                "description": "Content to write",
            },
            "mode": {
                "type": "string",
                "description": "Write mode (w=overwrite, a=append)",
                "enum": ["w", "a"],
                "default": "w",
            },
        }

    async def execute(
        self,
        relative_path: str,
        content: str,
        mode: str = "w",
    ) -> str:
        """
        Write content to a file.

        Args:
            relative_path: Path to file relative to workspace
            content: Content to write
            mode: Write mode (w=overwrite, a=append)

        Returns:
            Success message
        """
        path = self._resolve_path(relative_path)
        self._validate_path(path)

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, mode) as f:
            f.write(content)

        return f"Successfully wrote to {relative_path}"

class CommandTool(ComputerTool):
    """Tool for running shell commands."""

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return "Run a shell command and return its output."

    @property
    def parameters(self) -> Dict[str, Dict]:
        return {
            "command": {
                "type": "string",
                "description": "Command to execute",
            },
            "cwd": {
                "type": "string",
                "description": "Working directory relative to workspace root",
                "default": ".",
            },
        }

    async def execute(self, command: str, cwd: str = ".") -> str:
        """
        Run a shell command.

        Args:
            command: Command to execute
            cwd: Working directory relative to workspace root

        Returns:
            Command output
        """
        work_dir = self._resolve_path(cwd)
        self._validate_path(work_dir)

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"
