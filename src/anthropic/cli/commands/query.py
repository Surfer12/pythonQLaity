import click
from pathlib import Path

from ...core.extractors import create_extractor
from ...core.query import Query, QueryParser, QueryOptimizer, QueryExecutor
from ...core.utils.logging_utils import setup_logger
from ...core.utils.path_utils import collect_python_files

logger = setup_logger('code_sentinel.cli.query')

@click.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.argument('query')
@click.option(
    '--format',
    '-f',
    type=click.Choice(['text', 'json', 'yaml']),
    default='text',
    help='Output format'
)
@click.option(
    '--optimize/--no-optimize',
    default=True,
    help='Enable/disable query optimization'
)
def query(path: Path, query: str, format: str, optimize: bool):
    """Execute a query against a file or directory.

    PATH can be a file or directory to query.
    QUERY is the query string to execute (e.g., "ast_pattern:FunctionDef").
    """
    try:
        # Parse and optionally optimize the query
        parser = QueryParser()
        parsed_query = parser.parse(query)

        if optimize:
            optimizer = QueryOptimizer()
            parsed_query = optimizer.optimize(parsed_query)

        executor = QueryExecutor()

        # Execute query on file(s)
        if path.is_file():
            results = _execute_query(path, parsed_query, executor)
            _output_results(results, format)
        elif path.is_dir():
            files = collect_python_files(path)
            all_results = []

            with click.progressbar(
                files,
                label='Querying files',
                item_show_func=lambda p: str(p) if p else ''
            ) as bar:
                for file in bar:
                    results = _execute_query(file, parsed_query, executor)
                    if results:
                        all_results.extend(results)

            _output_results(all_results, format)
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise click.ClickException(str(e))

def _execute_query(
    filepath: Path,
    query: Query,
    executor: QueryExecutor
) -> list:
    """Execute a query on a single file.

    Args:
        filepath: Path to the file to query.
        query: The query to execute.
        executor: The query executor to use.

    Returns:
        A list of query results.
    """
    try:
        # Extract AST
        extractor = create_extractor(filepath)
        ast = extractor.extract(filepath)

        # Execute query
        results = executor.execute(ast, query, filepath)

        # Convert results to dictionaries for output
        return [
            {
                'filepath': str(filepath),
                'line_number': r.line_number,
                'match_type': r.match_type,
                'context': r.context
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Failed to query {filepath}: {str(e)}")
        click.echo(f"Error querying {filepath}: {str(e)}", err=True)
        return []

def _output_results(results: list, format: str) -> None:
    """Output query results in the specified format.

    Args:
        results: Query results to output.
        format: Output format ('text', 'json', or 'yaml').
    """
    if not results:
        click.echo("No results found.")
        return

    if format == 'text':
        _output_text(results)
    elif format == 'json':
        import json
        click.echo(json.dumps(results, indent=2))
    elif format == 'yaml':
        import yaml
        click.echo(yaml.safe_dump(results, default_flow_style=False))

def _output_text(results: list) -> None:
    """Output query results in text format.

    Args:
        results: Query results to output.
    """
    # Group results by file
    by_file = {}
    for result in results:
        filepath = result['filepath']
        if filepath not in by_file:
            by_file[filepath] = []
        by_file[filepath].append(result)

    # Output results for each file
    for filepath, file_results in sorted(by_file.items()):
        click.echo(f"\nResults for {filepath}:")
        for result in sorted(file_results, key=lambda r: r['line_number']):
            if result['context']:
                click.echo(
                    f"  Line {result['line_number']}: {result['context']}"
                )
            else:
                click.echo(
                    f"  Line {result['line_number']}: {result['match_type']}"
                )
