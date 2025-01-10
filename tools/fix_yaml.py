#!/usr/bin/env python3
"""Script to fix common YAML issues."""

import sys
import yaml
from pathlib import Path

def fix_yaml_file(file_path):
    """Fix common YAML issues in a file."""
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()

        # Parse YAML to validate
        data = yaml.safe_load(content)

        # Write back with proper formatting
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        print(f"Successfully fixed {file_path}")
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: fix_yaml.py <yaml_file_or_directory>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if path.is_file():
        fix_yaml_file(path)
    elif path.is_dir():
        for yaml_file in path.glob('**/*.yaml'):
            fix_yaml_file(yaml_file)
    else:
        print(f"Path not found: {path}")
        sys.exit(1)

if __name__ == '__main__':
    main()
