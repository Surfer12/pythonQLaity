"""Utility functions for logging setup and configuration."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Union

def setup_logger(
    name: str,
    level: Union[int, str] = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    format_string: Optional[str] = None,
    propagate: bool = False
) -> logging.Logger:
    """Set up a logger with the specified configuration.

    Args:
        name: The name of the logger.
        level: The logging level (default: INFO).
        log_file: Optional path to a log file.
        format_string: Optional custom format string for log messages.
        propagate: Whether to propagate messages to parent loggers.

    Returns:
        The configured logger.
    """
    # Convert string level to integer if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Set up format string
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    formatter = logging.Formatter(format_string)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def set_log_level(logger: logging.Logger, level: Union[int, str]) -> None:
    """Set the logging level for a logger and all its handlers.

    Args:
        logger: The logger to modify.
        level: The new logging level.
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

def add_file_handler(
    logger: logging.Logger,
    log_file: Union[str, Path],
    format_string: Optional[str] = None,
    level: Optional[Union[int, str]] = None
) -> None:
    """Add a file handler to an existing logger.

    Args:
        logger: The logger to modify.
        log_file: Path to the log file.
        format_string: Optional custom format string for log messages.
        level: Optional specific level for this handler.
    """
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    formatter = logging.Formatter(format_string)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    if level is not None:
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        file_handler.setLevel(level)

    logger.addHandler(file_handler)

def remove_file_handlers(logger: logging.Logger) -> None:
    """Remove all file handlers from a logger.

    Args:
        logger: The logger to modify.
    """
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

def get_child_logger(
    parent_logger: logging.Logger,
    child_name: str,
    level: Optional[Union[int, str]] = None
) -> logging.Logger:
    """Create a child logger with inherited settings.

    Args:
        parent_logger: The parent logger.
        child_name: Name for the child logger.
        level: Optional specific level for the child logger.

    Returns:
        The child logger.
    """
    logger_name = f"{parent_logger.name}.{child_name}"
    child_logger = logging.getLogger(logger_name)

    if level is not None:
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        child_logger.setLevel(level)

    return child_logger
