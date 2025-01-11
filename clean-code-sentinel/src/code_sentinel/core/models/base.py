"""Abstract base classes for code models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

@dataclass
class CodeIssue:
    """Represents an issue found in code."""
    file: str
    line: int
    column: Optional[int]
    type: str
    severity: str
    message: str
    snippet: Optional[str] = None
    fix_suggestion: Optional[str] = None

@dataclass
class AnalysisContext:
    """Context for code analysis."""
    file_path: Path
    content: str
    language: str
    config: Dict[str, Any]

class CodeModel(ABC):
    """Abstract base class for code models."""

    @abstractmethod
    def analyze(self, context: AnalysisContext) -> List[CodeIssue]:
        """Analyze code and find issues.

        Args:
            context: Analysis context containing code and configuration

        Returns:
            List of issues found in the code
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of programming languages this model supports.

        Returns:
            List of supported language identifiers
        """
        pass

    @abstractmethod
    def can_handle_language(self, language: str) -> bool:
        """Check if this model can handle a given programming language.

        Args:
            language: Language identifier to check

        Returns:
            True if this model can handle the language, False otherwise
        """
        pass

    @abstractmethod
    def get_available_checks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available checks.

        Returns:
            Dictionary mapping check IDs to their metadata
        """
        pass
