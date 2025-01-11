"""Mojo code analysis model implementation."""

import re
from typing import Dict, List, Any

from .base import CodeModel, CodeIssue, AnalysisContext

class MojoModel(CodeModel):
    """Model for analyzing Mojo code."""

    def analyze(self, context: AnalysisContext) -> List[CodeIssue]:
        """Analyze Mojo code and find issues.

        Args:
            context: Analysis context containing code and configuration

        Returns:
            List of issues found in the code
        """
        issues = []

        # Get enabled checks from config
        enabled_checks = self._get_enabled_checks(context.config)

        # Run enabled checks
        if 'struct_naming' in enabled_checks:
            issues.extend(self._check_struct_naming(context))
        if 'fn_naming' in enabled_checks:
            issues.extend(self._check_fn_naming(context))
        if 'type_hints' in enabled_checks:
            issues.extend(self._check_type_hints(context))
        if 'memory_management' in enabled_checks:
            issues.extend(self._check_memory_management(context))

        return issues

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages.

        Returns:
            List containing 'mojo'
        """
        return ['mojo']

    def can_handle_language(self, language: str) -> bool:
        """Check if language is Mojo.

        Args:
            language: Language identifier to check

        Returns:
            True if language is 'mojo', False otherwise
        """
        return language.lower() == 'mojo'

    def get_available_checks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available Mojo checks.

        Returns:
            Dictionary mapping check IDs to their metadata
        """
        return {
            'struct_naming': {
                'name': 'Struct Naming Convention',
                'description': 'Check struct names follow PascalCase convention',
                'severity': 'medium'
            },
            'fn_naming': {
                'name': 'Function Naming Convention',
                'description': 'Check function names follow snake_case convention',
                'severity': 'medium'
            },
            'type_hints': {
                'name': 'Type Hints',
                'description': 'Check for missing type hints in function signatures',
                'severity': 'high'
            },
            'memory_management': {
                'name': 'Memory Management',
                'description': 'Check for proper memory management patterns',
                'severity': 'high'
            }
        }

    def _get_enabled_checks(self, config: Dict[str, Any]) -> List[str]:
        """Get list of enabled checks from config."""
        checks_config = config.get('checks', {}).get('mojo', {})
        return [
            check_id for check_id, check_config in checks_config.items()
            if check_config.get('enabled', True)
        ]

    def _check_struct_naming(self, context: AnalysisContext) -> List[CodeIssue]:
        """Check struct naming conventions."""
        issues = []
        struct_pattern = re.compile(r'struct\s+([a-zA-Z_][a-zA-Z0-9_]*)')

        for match in struct_pattern.finditer(context.content):
            name = match.group(1)
            if not name[0].isupper() or '_' in name:
                issues.append(CodeIssue(
                    file=str(context.file_path),
                    line=context.content.count('\n', 0, match.start()) + 1,
                    column=match.start(1) - match.start() + 1,
                    type='struct_naming',
                    severity='medium',
                    message=f"Struct name '{name}' should use PascalCase",
                    snippet=match.group(0),
                    fix_suggestion=f"Rename to '{self._to_pascal_case(name)}'"
                ))

        return issues

    def _check_fn_naming(self, context: AnalysisContext) -> List[CodeIssue]:
        """Check function naming conventions."""
        issues = []
        fn_pattern = re.compile(r'fn\s+([a-zA-Z_][a-zA-Z0-9_]*)')

        for match in fn_pattern.finditer(context.content):
            name = match.group(1)
            if not name.islower() or not re.match(r'^[a-z][a-z0-9_]*$', name):
                issues.append(CodeIssue(
                    file=str(context.file_path),
                    line=context.content.count('\n', 0, match.start()) + 1,
                    column=match.start(1) - match.start() + 1,
                    type='fn_naming',
                    severity='medium',
                    message=f"Function name '{name}' should use snake_case",
                    snippet=match.group(0),
                    fix_suggestion=f"Rename to '{self._to_snake_case(name)}'"
                ))

        return issues

    def _check_type_hints(self, context: AnalysisContext) -> List[CodeIssue]:
        """Check for missing type hints."""
        issues = []
        fn_pattern = re.compile(
            r'fn\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(([^)]*)\)(?:\s*->\s*[^{]+)?'
        )

        for match in fn_pattern.finditer(context.content):
            params = match.group(1).strip()
            if params and not all(':' in param for param in params.split(',')):
                issues.append(CodeIssue(
                    file=str(context.file_path),
                    line=context.content.count('\n', 0, match.start()) + 1,
                    column=None,
                    type='type_hints',
                    severity='high',
                    message="Missing type hints in function parameters",
                    snippet=match.group(0),
                    fix_suggestion="Add type hints for all parameters"
                ))

        return issues

    def _check_memory_management(self, context: AnalysisContext) -> List[CodeIssue]:
        """Check memory management patterns."""
        issues = []
        # Add memory management checks specific to Mojo
        # This is a placeholder for future implementation
        return issues

    @staticmethod
    def _to_pascal_case(name: str) -> str:
        """Convert string to PascalCase."""
        return ''.join(word.capitalize() for word in re.split(r'[_\s]+', name))

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert string to snake_case."""
        name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)
        return name.lower()
