"""Base classes and utilities for Claude tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class ToolResult:
    """Result from a tool execution."""
    tool_name: str
    tool_call_id: str
    args: Dict[str, Any]
    output: Any

class BaseTool(ABC):
    """Base class for all Claude tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """The parameters accepted by the tool."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool-specific output
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tool to a dictionary format.

        Returns:
            Dict containing tool configuration
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
