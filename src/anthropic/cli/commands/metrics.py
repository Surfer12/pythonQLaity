import click
from pathlib import Path
from typing import Dict, List, Union

from ...core.extractors import create_extractor
from ...core.models import create_model
from ...core.utils.logging_utils import setup_logger
from ...core.utils.path_utils import collect_python_files

logger = setup_logger('code_sentinel.cli.metrics')

@click.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--format',
    '-f',
    type=click.Choice(['text', 'json', 'yaml']),
    default='text',
    help='Output format'
)
@click.option(
    '--aggregate/--no-aggregate',
    default=True,
    help='Aggregate metrics for directories'
)
def metrics(path: Path, format: str, aggregate: bool):
    """Calculate code metrics for a file or directory.

    PATH can be a file or directory to analyze.
    """
    try:
        if path.is_file():
            results = _calculate_metrics(path)
            _output_results(results, format)
        elif path.is_dir():
            files = collect_python_files(path)
            all_results = []
            total_metrics = {}

            with click.progressbar(
                files,
                label='Calculating metrics',
                item_show_func=lambda p: str(p) if p else ''
            ) as bar:
                for file in bar:
                    results = _calculate_metrics(file)
                    if results:
                        all_results.append(results)
                        if aggregate:
                            _update_total_metrics(total_metrics, results['metrics'])

            if aggregate:
                results = {
                    'total_metrics': total_metrics,
                    'file_metrics': all_results
                }
            else:
                results = all_results

            _output_results(results, format)
    except Exception as e:
        logger.error(f"Metrics calculation failed: {str(e)}")
        raise click.ClickException(str(e))

def _calculate_metrics(filepath: Path) -> dict:
    """Calculate metrics for a single file.

    Args:
        filepath: Path to the file to analyze.

    Returns:
        A dictionary containing the metrics results.
    """
    try:
        # Create extractor and model
        extractor = create_extractor(filepath)
        model = create_model(filepath)

        # Extract AST and calculate metrics
        ast = extractor.extract(filepath)
        metrics = model.calculate_metrics(ast)

        return {
            'filepath': str(filepath),
            'metrics': metrics
        }
    except Exception as e:
        logger.error(f"Failed to calculate metrics for {filepath}: {str(e)}")
        click.echo(f"Error calculating metrics for {filepath}: {str(e)}", err=True)
        return None

def _update_total_metrics(total: Dict, metrics: Dict) -> None:
    """Update total metrics with metrics from a single file.

    Args:
        total: Dictionary of total metrics to update.
        metrics: Metrics from a single file.
    """
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            total[key] = total.get(key, 0) + value
        elif isinstance(value, dict):
            if key not in total:
                total[key] = {}
            _update_total_metrics(total[key], value)

def _output_results(
    results: Union[Dict, List],
    format: str
) -> None:
    """Output metrics results in the specified format.

    Args:
        results: Metrics results to output.
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

def _output_text(results: Union[Dict, List]) -> None:
    """Output metrics results in text format.

    Args:
        results: Metrics results to output.
    """
    if isinstance(results, dict) and 'total_metrics' in results:
        # Aggregated results
        click.echo("\nTotal metrics across all files:")
        _output_metrics_dict(results['total_metrics'])

        click.echo("\nPer-file metrics:")
        for file_result in results['file_metrics']:
            click.echo(f"\n{file_result['filepath']}:")
            _output_metrics_dict(file_result['metrics'], indent=2)
    elif isinstance(results, list):
        # Non-aggregated results
        for file_result in results:
            click.echo(f"\n{file_result['filepath']}:")
            _output_metrics_dict(file_result['metrics'], indent=2)
    else:
        # Single file results
        click.echo(f"\n{results['filepath']}:")
        _output_metrics_dict(results['metrics'], indent=2)

def _output_metrics_dict(metrics: Dict, indent: int = 0) -> None:
    """Output a metrics dictionary with proper indentation.

    Args:
        metrics: Dictionary of metrics to output.
        indent: Number of spaces to indent.
    """
    prefix = ' ' * indent
    for key, value in sorted(metrics.items()):
        if isinstance(value, dict):
            click.echo(f"{prefix}{key}:")
            _output_metrics_dict(value, indent + 2)
        else:
            click.echo(f"{prefix}{key}: {value}")
