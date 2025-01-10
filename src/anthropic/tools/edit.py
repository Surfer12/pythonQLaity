"""Tools for editing files and content."""

import difflib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import BaseTool, ToolResult
from .computer import ComputerTool


class EditTool(ComputerTool):
    """Tool for editing file contents."""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return (
            "Edit a file by replacing specified lines with new content. "
            "Returns a diff of the changes."
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
            "new_content": {
                "type": "string",
                "description": "New content to insert",
            },
        }

    async def execute(
        self,
        relative_path: str,
        start_line: int,
        end_line: int,
        new_content: str,
    ) -> str:
        """
        Edit a file by replacing lines with new content.

        Args:
            relative_path: Path to file relative to workspace
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed)
            new_content: New content to insert

        Returns:
            Unified diff of the changes
        """
        path = self._resolve_path(relative_path)
        self._validate_path(path)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        # Read original content
        with open(path) as f:
            original_lines = f.readlines()

        # Create new content
        new_lines = (
            original_lines[:start_line - 1]
            + [line + "\n" for line in new_content.splitlines()]
            + original_lines[end_line:]
        )

        # Generate diff
        diff = list(
            difflib.unified_diff(
                original_lines,
                new_lines,
                fromfile=str(path),
                tofile=str(path),
                lineterm="",
            )
        )

        # Write new content
        with open(path, "w") as f:
            f.writelines(new_lines)

        return "\n".join(diff)


class ReplaceTool(ComputerTool):
    """Tool for replacing text in files."""

    @property
    def name(self) -> str:
        return "replace_text"

    @property
    def description(self) -> str:
        return (
            "Replace all occurrences of a pattern with new text. "
            "Returns number of replacements made."
        )

    @property
    def parameters(self) -> Dict[str, Dict]:
        return {
            "relative_path": {
                "type": "string",
                "description": "Path relative to workspace root",
            },
            "pattern": {
                "type": "string",
                "description": "Text pattern to replace",
            },
            "replacement": {
                "type": "string",
                "description": "Text to replace pattern with",
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether to match case",
                "default": True,
            },
        }

    async def execute(
        self,
        relative_path: str,
        pattern: str,
        replacement: str,
        case_sensitive: bool = True,
    ) -> str:
        """
        Replace text in a file.

        Args:
            relative_path: Path to file relative to workspace
            pattern: Text pattern to replace
            replacement: Text to replace pattern with
            case_sensitive: Whether to match case

        Returns:
            Message indicating number of replacements
        """
        path = self._resolve_path(relative_path)
        self._validate_path(path)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path) as f:
            content = f.read()

        if case_sensitive:
            new_content = content.replace(pattern, replacement)
        else:
            new_content = content.replace(
                pattern.lower(),
                replacement.lower(),
            )

        count = content.count(pattern)

        with open(path, "w") as f:
            f.write(new_content)

        return f"Made {count} replacements"
