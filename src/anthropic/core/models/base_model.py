from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class CodeLocation:
    """Represents a location in source code.

    Attributes:
        filepath: Path to the source file.
        start_line: Starting line number (1-based).
        end_line: Ending line number (1-based).
        start_col: Starting column number (1-based).
        end_col: Ending column number (1-based).
    """
    filepath: Path
    start_line: int
    end_line: int
    start_col: Optional[int] = None
    end_col: Optional[int] = None

@dataclass
class CodeSymbol:
    """Represents a symbol (function, class, variable) in code.

    Attributes:
        name: The symbol's name.
        type: The symbol's type (e.g., 'function', 'class', 'variable').
        location: Where the symbol is defined.
        attributes: Additional attributes specific to the symbol type.
    """
    name: str
    type: str
    location: CodeLocation
    attributes: Dict[str, Any] = None

class BaseModel(ABC):
    """Base class for language-specific code models.

    This class defines the interface for working with code models,
    including symbol extraction, dependency analysis, and metrics
    calculation.
    """

    @abstractmethod
    def extract_symbols(self, ast_node: Any) -> List[CodeSymbol]:
        """Extract symbols from an AST node.

        Args:
            ast_node: The AST node to analyze.

        Returns:
            A list of CodeSymbol objects representing the symbols found.
        """
        pass

    @abstractmethod
    def analyze_dependencies(self, ast_node: Any) -> Dict[str, List[str]]:
        """Analyze dependencies between symbols in an AST node.

        Args:
            ast_node: The AST node to analyze.

        Returns:
            A dictionary mapping symbol names to lists of dependency names.
        """
        pass

    @abstractmethod
    def calculate_metrics(self, ast_node: Any) -> Dict[str, Any]:
        """Calculate code metrics from an AST node.

        Args:
            ast_node: The AST node to analyze.

        Returns:
            A dictionary of metric names to their values.
        """
        pass

    @abstractmethod
    def validate_ast(self, ast_node: Any) -> List[str]:
        """Validate an AST node for correctness.

        Args:
            ast_node: The AST node to validate.

        Returns:
            A list of validation error messages, empty if valid.
        """
        pass
