"""Tests for the computer interaction module."""

import os
import platform
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from anthropic.core.computer import (
    BaseComputer,
    CommandError,
    FileOperationError,
    UnixComputer,
    create_computer
)

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp:
        yield Path(temp)

@pytest.fixture
def computer(temp_dir: Path) -> BaseComputer:
    """Create a computer interface for testing."""
    return create_computer(temp_dir)

def test_create_computer_unix():
    """Test creating a computer interface on Unix-like systems."""
    system = platform.system().lower()
    if system in ('linux', 'darwin'):
        computer = create_computer()
        assert isinstance(computer, UnixComputer)
    else:
        with pytest.raises(RuntimeError):
            create_computer()

def test_execute_command(computer: BaseComputer):
    """Test executing shell commands."""
    # Test successful command
    result = computer.execute_command('echo "test"')
    assert result.returncode == 0
    assert result.stdout.strip() == 'test'

    # Test command with environment variables
    result = computer.execute_command(
        'echo $TEST_VAR',
        env={'TEST_VAR': 'test_value'}
    )
    assert result.stdout.strip() == 'test_value'

    # Test command failure
    with pytest.raises(CommandError):
        computer.execute_command('nonexistent_command')

    # Test command timeout
    with pytest.raises(CommandError):
        computer.execute_command('sleep 2', timeout=0.1)

def test_file_operations(computer: BaseComputer, temp_dir: Path):
    """Test file operations."""
    test_file = temp_dir / 'test.txt'
    test_content = 'test content'

    # Test writing file
    computer.write_file(test_file, test_content)
    assert test_file.exists()
    assert test_file.read_text() == test_content

    # Test reading file
    content = computer.read_file(test_file)
    assert content == test_content

    # Test binary file operations
    binary_file = temp_dir / 'test.bin'
    binary_content = b'\x00\x01\x02\x03'
    computer.write_file(binary_file, binary_content, binary=True)
    assert computer.read_file(binary_file, binary=True) == binary_content

    # Test file deletion
    computer.delete_file(test_file)
    assert not test_file.exists()

    # Test error handling
    with pytest.raises(FileOperationError):
        computer.read_file(temp_dir / 'nonexistent.txt')

def test_directory_operations(computer: BaseComputer, temp_dir: Path):
    """Test directory operations."""
    # Test directory creation
    test_dir = temp_dir / 'test_dir'
    computer.create_directory(test_dir)
    assert test_dir.is_dir()

    # Test nested directory creation
    nested_dir = test_dir / 'nested' / 'dir'
    computer.create_directory(nested_dir)
    assert nested_dir.is_dir()

    # Test directory listing
    test_file = test_dir / 'test.txt'
    test_file.touch()

    files = computer.list_directory(test_dir)
    assert len(files) == 2  # test.txt and nested/
    assert test_file in files

    # Test recursive listing
    files = computer.list_directory(test_dir, recursive=True)
    assert len(files) == 2  # test.txt and nested/dir

    # Test pattern matching
    files = computer.list_directory(test_dir, pattern='*.txt')
    assert len(files) == 1
    assert files[0] == test_file

    # Test directory deletion
    computer.delete_file(test_dir)
    assert not test_dir.exists()

def test_file_info(computer: BaseComputer, temp_dir: Path):
    """Test getting file information."""
    # Create test file
    test_file = temp_dir / 'test.txt'
    test_content = 'test content'
    computer.write_file(test_file, test_content)

    # Get file info
    info = computer.get_file_info(test_file)

    # Check basic attributes
    assert info['size'] == len(test_content)
    assert info['type'] == 'file'
    assert 'created' in info
    assert 'modified' in info
    assert 'accessed' in info
    assert 'mode' in info

    # Test directory info
    dir_info = computer.get_file_info(temp_dir)
    assert dir_info['type'] == 'directory'

    # Test error handling
    with pytest.raises(FileOperationError):
        computer.get_file_info(temp_dir / 'nonexistent.txt')

def test_working_directory(computer: BaseComputer, temp_dir: Path):
    """Test working directory functionality."""
    # Test initial working directory
    assert computer.working_dir == temp_dir

    # Test changing directory
    test_dir = temp_dir / 'test_dir'
    computer.create_directory(test_dir)
    computer.change_directory(test_dir)
    assert computer.working_dir == test_dir

    # Test relative path resolution
    test_file = 'test.txt'
    computer.write_file(test_file, 'test')
    assert (test_dir / test_file).exists()

    # Test error handling
    with pytest.raises(FileOperationError):
        computer.change_directory(temp_dir / 'nonexistent')
