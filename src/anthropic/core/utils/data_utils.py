"""Utility functions for data manipulation."""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
import yaml

T = TypeVar('T')

def ensure_list(value: Union[List[Any], Any]) -> List[Any]:
    """Ensure that a value is a list.

    If the value is already a list, return it as is.
    If it's not a list, wrap it in a list.
    If it's None, return an empty list.

    Args:
        value: The value to convert to a list.

    Returns:
        A list containing the value, or the value itself if it's already a list.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

def safe_cast(value: Any, target_type: Type[T], default: Optional[T] = None) -> Optional[T]:
    """Safely cast a value to a target type.

    Args:
        value: The value to cast.
        target_type: The type to cast to.
        default: The default value to return if casting fails.

    Returns:
        The cast value, or the default if casting fails.
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default

def load_yaml(file_path: str) -> Dict[str, Any]:
    """Load a YAML file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        The loaded YAML data as a dictionary.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(data: Dict[str, Any], file_path: str) -> None:
    """Save data to a YAML file.

    Args:
        data: The data to save.
        file_path: Path where to save the YAML file.

    Raises:
        yaml.YAMLError: If the data cannot be serialized to YAML.
    """
    with open(file_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False)

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries.

    The second dictionary takes precedence when there are conflicts.

    Args:
        dict1: The first dictionary.
        dict2: The second dictionary.

    Returns:
        The merged dictionary.
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if (
            key in result and
            isinstance(result[key], dict) and
            isinstance(value, dict)
        ):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: The dictionary to flatten.
        parent_key: The parent key for nested values.
        sep: The separator to use between keys.

    Returns:
        A flattened dictionary with dot-separated keys.
    """
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)

def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """Convert a flattened dictionary back to a nested dictionary.

    Args:
        d: The flattened dictionary.
        sep: The separator used between keys.

    Returns:
        A nested dictionary.
    """
    result: Dict[str, Any] = {}

    for key, value in d.items():
        parts = key.split(sep)
        target = result

        for part in parts[:-1]:
            target = target.setdefault(part, {})

        target[parts[-1]] = value

    return result

def deep_get(d: Dict[str, Any], path: str, default: Any = None, sep: str = '.') -> Any:
    """Get a value from a nested dictionary using a dot-separated path.

    Args:
        d: The dictionary to search.
        path: The dot-separated path to the value.
        default: The value to return if the path doesn't exist.
        sep: The separator used in the path.

    Returns:
        The value at the path, or the default if not found.
    """
    current = d

    try:
        for part in path.split(sep):
            current = current[part]
        return current
    except (KeyError, TypeError):
        return default

def deep_set(d: Dict[str, Any], path: str, value: Any, sep: str = '.') -> None:
    """Set a value in a nested dictionary using a dot-separated path.

    Args:
        d: The dictionary to modify.
        path: The dot-separated path to the value.
        value: The value to set.
        sep: The separator used in the path.
    """
    parts = path.split(sep)
    current = d

    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value

def deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively update a dictionary with another dictionary.

    Args:
        d: The dictionary to update.
        u: The dictionary containing the updates.

    Returns:
        The updated dictionary.
    """
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def filter_dict(
    d: Dict[str, Any],
    predicate: callable,
    recursive: bool = True
) -> Dict[str, Any]:
    """Filter a dictionary based on a predicate function.

    Args:
        d: The dictionary to filter.
        predicate: A function that takes a key-value pair and returns a boolean.
        recursive: Whether to recursively filter nested dictionaries.

    Returns:
        A new dictionary containing only the key-value pairs that satisfy the predicate.
    """
    result = {}

    for k, v in d.items():
        if isinstance(v, dict) and recursive:
            filtered = filter_dict(v, predicate, recursive=True)
            if filtered:
                result[k] = filtered
        elif predicate(k, v):
            result[k] = v

    return result
