"""Tools for running commands and processes."""

import asyncio
import os
import subprocess
from typing import Dict, Optional

from .computer import ComputerTool


class RunTool(ComputerTool):
    """Tool for running commands."""

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return (
            "Run a shell command in the specified working directory. "
            "Returns command output."
        )

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
            "timeout": {
                "type": "integer",
                "description": "Command timeout in seconds",
                "default": 30,
            },
        }

    async def execute(
        self,
        command: str,
        cwd: str = ".",
        timeout: int = 30,
    ) -> str:
        """
        Run a shell command.

        Args:
            command: Command to execute
            cwd: Working directory relative to workspace root
            timeout: Command timeout in seconds

        Returns:
            Command output
        """
        work_dir = self._resolve_path(cwd)
        self._validate_path(work_dir)

        if not work_dir.is_dir():
            raise NotADirectoryError(f"Directory not found: {work_dir}")

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                proc.terminate()
                await proc.wait()
                return f"Command timed out after {timeout} seconds"

            if proc.returncode != 0:
                return (
                    f"Command failed with exit code {proc.returncode}.\n"
                    f"stdout: {stdout.decode()}\n"
                    f"stderr: {stderr.decode()}"
                )

            return stdout.decode()

        except Exception as e:
            return f"Error executing command: {str(e)}"
