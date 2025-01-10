import click
from pathlib import Path

from ...core.extractors import create_extractor
from ...core.models import create_model
from ...core.utils.logging_utils import setup_logger
from ...core.utils.path_utils import collect_python_files

logger = setup_logger('code_sentinel.cli.analyze')

@click.command()
@click.argument(
    'path',
    type=click.Path(exists=True, path_type=Path)
)
@click.option(
    '--recursive/--no-recursive',
    '-r',
    default=False,
    help='Recursively analyze directories'
)
@click.option(
    '--format',
    '-f',
    type=click.Choice(['text', 'json', 'yaml']),
    default='text',
    help='Output format'
)
def analyze(path: Path, recursive: bool, format: str):
    """Analyze a file or directory for code quality issues.

    PATH can be a file or directory. If PATH is a directory and --recursive
    is specified, all supported files in the directory tree will be analyzed.
    """
    try:
        if path.is_file():
            results = _analyze_file(path)
            _output_results(results, format)
        elif path.is_dir():
            if recursive:
                files = collect_python_files(path)
                all_results = []

                with click.progressbar(
                    files,
                    label='Analyzing files',
                    item_show_func=lambda p: str(p) if p else ''
                ) as bar:
                    for file in bar:
                        results = _analyze_file(file)
                        if results:
                            all_results.append(results)

                _output_results(all_results, format)
            else:
                click.echo(
                    'Directory specified without --recursive. '
                    'Only analyzing Python files in the root directory.'
                )
                all_results = []
                for file in path.glob('*.py'):
                    results = _analyze_file(file)
                    if results:
                        all_results.append(results)

                _output_results(all_results, format)
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise click.ClickException(str(e))

def _analyze_file(filepath: Path) -> dict:
    """Analyze a single file.

    Args:
        filepath: Path to the file to analyze.

    Returns:
        A dictionary containing the analysis results.
    """
    try:
        # Create extractor and model
        extractor = create_extractor(filepath)
        model = create_model(filepath)

        # Extract AST
        ast = extractor.extract(filepath)

        # Analyze code
        symbols = model.extract_symbols(ast)
        deps = model.analyze_dependencies(ast)
        errors = model.validate_ast(ast)
        metrics = model.calculate_metrics(ast)

        # Compile results
        return {
            'filepath': str(filepath),
            'symbols': [
                {
                    'name': s.name,
                    'type': s.type,
                    'location': {
                        'start_line': s.location.start_line,
                        'end_line': s.location.end_line,
                        'start_col': s.location.start_col,
                        'end_col': s.location.end_col
                    },
                    'attributes': s.attributes
                }
                for s in symbols
            ],
            'dependencies': deps,
            'validation_errors': errors,
            'metrics': metrics
        }
    except Exception as e:
        logger.error(f"Failed to analyze {filepath}: {str(e)}")
        click.echo(f"Error analyzing {filepath}: {str(e)}", err=True)
        return None

def _output_results(results: dict, format: str) -> None:
    """Output analysis results in the specified format.

    Args:
        results: Analysis results to output.
        format: Output format ('text', 'json', or 'yaml').
    """
    if not results:
        click.echo("No results to display.")
        return

    if format == 'text':
        _output_text(results)
    elif format == 'json':
        import json
        click.echo(json.dumps(results, indent=2))
    elif format == 'yaml':
        import yaml
        click.echo(yaml.safe_dump(results, default_flow_style=False))

def _output_text(results: dict) -> None:
    """Output analysis results in text format.

    Args:
        results: Analysis results to output.
    """
    if isinstance(results, list):
        # Multiple files
        for file_results in results:
            _output_single_file_text(file_results)
    else:
        # Single file
        _output_single_file_text(results)

def _output_single_file_text(results: dict) -> None:
    """Output analysis results for a single file in text format.

    Args:
        results: Analysis results for a single file.
    """
    click.echo(f"\nAnalysis results for {results['filepath']}:")

    # Output symbols
    if results['symbols']:
        click.echo("\nSymbols found:")
        for symbol in results['symbols']:
            click.echo(
                f"  {symbol['type']} '{symbol['name']}' "
                f"at line {symbol['location']['start_line']}"
            )
            if symbol['attributes']:
                for key, value in symbol['attributes'].items():
                    click.echo(f"    {key}: {value}")

    # Output dependencies
    if results['dependencies']:
        click.echo("\nDependencies:")
        for name, deps in results['dependencies'].items():
            if deps:
                click.echo(f"  {name} depends on: {', '.join(deps)}")

    # Output validation errors
    if results['validation_errors']:
        click.echo("\nValidation errors:")
        for error in results['validation_errors']:
            click.echo(f"  {error}")

    # Output metrics
    if results['metrics']:
        click.echo("\nMetrics:")
        for key, value in sorted(results['metrics'].items()):
            click.echo(f"  {key}: {value}")
