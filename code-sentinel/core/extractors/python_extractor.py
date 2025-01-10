import ast
from pathlib import Path
from typing import Any, Dict, List

from .base_extractor import BaseExtractor

class PythonExtractor(BaseExtractor):
    """Python code extractor implementation."""

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """Extract code information from a Python file.

        Args:
            file_path: Path to the Python file to analyze.

        Returns:
            Dictionary containing extracted code information including:
            - imports: List of import statements
            - classes: List of class definitions
            - functions: List of function definitions
            - global_variables: List of global variable assignments
            - ast: The full AST representation

        Raises:
            ValueError: If the file is not a valid Python file.
            IOError: If there are issues reading the file.
            SyntaxError: If the Python code is not syntactically valid.
        """
        self.validate_file(file_path)

        if not self.supports_file(file_path):
            raise ValueError(f"File is not a supported Python file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            raise SyntaxError(f"Invalid Python syntax in {file_path}: {str(e)}")

        return {
            "imports": self._extract_imports(tree),
            "classes": self._extract_classes(tree),
            "functions": self._extract_functions(tree),
            "global_variables": self._extract_global_variables(tree),
            "ast": tree
        }

    def supports_file(self, file_path: Path) -> bool:
        """Check if the file is a Python file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file has a .py or .pyi extension, False otherwise.
        """
        return file_path.suffix.lower() in self.get_supported_extensions()

    def get_supported_extensions(self) -> List[str]:
        """Get the list of supported Python file extensions.

        Returns:
            List of supported file extensions ([".py", ".pyi"]).
        """
        return [".py", ".pyi"]

    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract import statements from the AST.

        Args:
            tree: The AST to analyze.

        Returns:
            List of dictionaries containing import information.
        """
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append({
                        "type": "import",
                        "name": name.name,
                        "asname": name.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                for name in node.names:
                    imports.append({
                        "type": "import_from",
                        "module": node.module,
                        "name": name.name,
                        "asname": name.asname,
                        "level": node.level
                    })
        return imports

    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions from the AST.

        Args:
            tree: The AST to analyze.

        Returns:
            List of dictionaries containing class information.
        """
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "bases": [self._get_name(base) for base in node.bases],
                    "decorators": [self._get_name(d) for d in node.decorator_list],
                    "methods": self._extract_methods(node),
                    "lineno": node.lineno,
                    "col_offset": node.col_offset
                })
        return classes

    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function definitions from the AST.

        Args:
            tree: The AST to analyze.

        Returns:
            List of dictionaries containing function information.
        """
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not self._is_method(node):
                functions.append(self._function_to_dict(node))
        return functions

    def _extract_methods(self, class_node: ast.ClassDef) -> List[Dict[str, Any]]:
        """Extract method definitions from a class.

        Args:
            class_node: The class AST node to analyze.

        Returns:
            List of dictionaries containing method information.
        """
        methods = []
        for node in ast.walk(class_node):
            if isinstance(node, ast.FunctionDef) and self._is_method(node):
                methods.append(self._function_to_dict(node))
        return methods

    def _extract_global_variables(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract global variable assignments from the AST.

        Args:
            tree: The AST to analyze.

        Returns:
            List of dictionaries containing global variable information.
        """
        variables = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and self._is_global_scope(node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append({
                            "name": target.id,
                            "lineno": target.lineno,
                            "col_offset": target.col_offset
                        })
        return variables

    def _function_to_dict(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Convert a function AST node to a dictionary representation.

        Args:
            node: The function AST node.

        Returns:
            Dictionary containing function information.
        """
        return {
            "name": node.name,
            "args": self._get_arguments(node.args),
            "decorators": [self._get_name(d) for d in node.decorator_list],
            "returns": self._get_name(node.returns) if node.returns else None,
            "lineno": node.lineno,
            "col_offset": node.col_offset
        }

    def _get_arguments(self, args: ast.arguments) -> Dict[str, Any]:
        """Extract function arguments information.

        Args:
            args: The arguments AST node.

        Returns:
            Dictionary containing arguments information.
        """
        return {
            "args": [arg.arg for arg in args.args],
            "vararg": args.vararg.arg if args.vararg else None,
            "kwarg": args.kwarg.arg if args.kwarg else None,
            "defaults": len(args.defaults),
            "kw_defaults": len(args.kw_defaults)
        }

    def _get_name(self, node: ast.AST) -> str:
        """Get the string representation of a name node.

        Args:
            node: The AST node.

        Returns:
            String representation of the name.
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Str):
            return node.s
        return str(node)

    def _is_method(self, node: ast.FunctionDef) -> bool:
        """Check if a function definition is a method.

        Args:
            node: The function AST node.

        Returns:
            True if the function is a method, False otherwise.
        """
        return any(isinstance(parent, ast.ClassDef) for parent in ast.walk(node))

    def _is_global_scope(self, node: ast.AST) -> bool:
        """Check if a node is in the global scope.

        Args:
            node: The AST node.

        Returns:
            True if the node is in the global scope, False otherwise.
        """
        return not any(isinstance(parent, (ast.FunctionDef, ast.ClassDef))
                      for parent in ast.walk(node))
