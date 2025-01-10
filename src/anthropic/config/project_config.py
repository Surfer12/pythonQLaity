"""Project configuration management.

This module handles loading, validating, and managing project configuration.
It supports loading from YAML files and environment variables, with validation
against a JSON schema.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import jsonschema
import yaml
from omegaconf import OmegaConf

from ..core.utils.data_utils import merge_dicts
from ..core.utils.logging_utils import setup_logger
from ..core.utils.path_utils import find_project_root

logger = setup_logger('code_sentinel.config')

class ConfigurationError(Exception):
    """Raised when there is a configuration error."""
    pass

class ProjectConfig:
    """Manages project configuration.

    This class handles loading configuration from various sources,
    validating it against a schema, and providing access to settings.
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        schema_path: Optional[Union[str, Path]] = None
    ):
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If not provided,
                will look for 'code_sentinel.yaml' in the project root.
            schema_path: Path to the JSON schema file. If not provided,
                will use the default schema.
        """
        self._config: Dict[str, Any] = {}
        self._schema: Dict[str, Any] = {}

        # Load schema
        if schema_path is None:
            schema_path = Path(__file__).parent / 'schema.json'
        self._load_schema(schema_path)

        # Load default configuration
        default_config_path = Path(__file__).parent / 'defaults.yaml'
        self._config = self._load_yaml(default_config_path)

        # Load project configuration if provided
        if config_path is not None:
            project_config = self._load_yaml(config_path)
            self._config = merge_dicts(self._config, project_config)
        else:
            # Try to find project config in root
            project_root = find_project_root(Path.cwd())
            if project_root is not None:
                config_path = project_root / 'code_sentinel.yaml'
                if config_path.exists():
                    project_config = self._load_yaml(config_path)
                    self._config = merge_dicts(self._config, project_config)

        # Load environment variables
        self._load_env_vars()

        # Validate configuration
        self.validate()

    def _load_schema(self, path: Union[str, Path]) -> None:
        """Load the JSON schema.

        Args:
            path: Path to the schema file.

        Raises:
            ConfigurationError: If the schema cannot be loaded.
        """
        try:
            with open(path, 'r') as f:
                self._schema = json.load(f)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load schema from {path}: {str(e)}"
            )

    def _load_yaml(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load a YAML configuration file.

        Args:
            path: Path to the YAML file.

        Returns:
            The loaded configuration.

        Raises:
            ConfigurationError: If the file cannot be loaded.
        """
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from {path}: {str(e)}"
            )

    def _load_env_vars(self) -> None:
        """Load configuration from environment variables.

        Environment variables should be prefixed with 'CODE_SENTINEL_'
        and use underscores for nesting. For example:
        CODE_SENTINEL_OUTPUT_FORMAT=json
        """
        prefix = 'CODE_SENTINEL_'
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert key to nested dictionary path
                path = key[len(prefix):].lower().split('_')

                # Convert value to appropriate type
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)

                # Update configuration
                current = self._config
                for part in path[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[path[-1]] = value

    def validate(self) -> None:
        """Validate the configuration against the schema.

        Raises:
            ConfigurationError: If the configuration is invalid.
        """
        try:
            jsonschema.validate(self._config, self._schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {str(e)}")

    def get(self, path: str, default: Any = None) -> Any:
        """Get a configuration value by path.

        Args:
            path: Dot-separated path to the value (e.g., 'output.format').
            default: Value to return if the path doesn't exist.

        Returns:
            The configuration value, or the default if not found.
        """
        current = self._config
        for part in path.split('.'):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, path: str, value: Any) -> None:
        """Set a configuration value by path.

        Args:
            path: Dot-separated path to the value.
            value: The value to set.

        Raises:
            ConfigurationError: If the resulting configuration is invalid.
        """
        # Create a copy of the config
        new_config = self._config.copy()

        # Update the value
        current = new_config
        parts = path.split('.')
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

        # Validate the new configuration
        try:
            jsonschema.validate(new_config, self._schema)
            self._config = new_config
        except jsonschema.exceptions.ValidationError as e:
            raise ConfigurationError(
                f"Invalid configuration after setting {path}: {str(e)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Get the complete configuration as a dictionary.

        Returns:
            The configuration dictionary.
        """
        return self._config.copy()

    def save(self, path: Union[str, Path]) -> None:
        """Save the configuration to a YAML file.

        Args:
            path: Path to save the configuration to.

        Raises:
            ConfigurationError: If the file cannot be written.
        """
        try:
            with open(path, 'w') as f:
                yaml.safe_dump(self._config, f, default_flow_style=False)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration to {path}: {str(e)}"
            )

# Global configuration instance
config = ProjectConfig()
