"""Code Sentinel CLI.

This module provides the main entry point for the Code Sentinel command-line
interface. It sets up the CLI group and registers all available commands.
"""

import click

from ..core.utils.logging_utils import setup_logger
from .commands import analyze, metrics, query

logger = setup_logger('code_sentinel')

@click.group()
@click.option(
    '--debug/--no-debug',
    default=False,
    help='Enable debug logging'
)
def cli(debug: bool):
    """Code Sentinel: A static analysis tool for improving code quality.

    This tool analyzes code for quality, security, and maintainability issues.
    It supports multiple programming languages and can be integrated into
    various development workflows.
    """
    if debug:
        logger.setLevel('DEBUG')

# Register commands
cli.add_command(analyze)
cli.add_command(metrics)
cli.add_command(query)

if __name__ == '__main__':
    cli()
