"""CLI command for running code analysis."""

import click
from pathlib import Path
from typing import List, Optional

from ...tools.analysis_tool import AnalysisTool

@click.command()
@click.argument('target', type=click.Path(exists=True))
@click.option(
    '--checks',
    '-c',
    multiple=True,
    help='Specific checks to run. Can be specified multiple times.'
)
@click.option(
    '--timeout',
    '-t',
    type=int,
    default=30,
    help='Analysis timeout in seconds.'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='Disable result caching.'
)
@click.option(
    '--no-fix-suggestions',
    is_flag=True,
    help='Disable generation of fix suggestions.'
)
@click.option(
    '--output-format',
    '-f',
    type=click.Choice(['text', 'json']),
    default='text',
    help='Output format for results.'
)
def analyze(
    target: str,
    checks: Optional[List[str]],
    timeout: int,
    no_cache: bool,
    no_fix_suggestions: bool,
    output_format: str
):
    """Run code analysis on the specified target.

    TARGET is the path to the file or directory to analyze.
    """
    try:
        # Initialize analysis tool
        tool = AnalysisTool()

        # Run analysis
        results = tool.analyze_code(
            target,
            checks=list(checks) if checks else None,
            timeout=timeout,
            cache=not no_cache,
            fix_suggestions=not no_fix_suggestions
        )

        # Output results
        if output_format == 'json':
            click.echo(results.to_json())
        else:
            click.echo(tool.summarize_results(results))

        # Exit with status code based on success
        exit(0 if results.success else 1)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)
