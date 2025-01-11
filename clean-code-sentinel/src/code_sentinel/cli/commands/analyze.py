"""CLI command for running code analysis."""

import click
from pathlib import Path
from typing import List, Optional, Dict, Any

from ...core.extractors.base import CodeExtractor
from ...core.extractors.mojo import MojoExtractor
from ...core.models.base import CodeModel, AnalysisContext
from ...core.models.mojo import MojoModel
from ...tools.analysis_tool import AnalysisTool

class LanguageHandler:
    """Handles language-specific extractors and models."""

    def __init__(self):
        self.extractors: Dict[str, CodeExtractor] = {
            'mojo': MojoExtractor()
        }
        self.models: Dict[str, CodeModel] = {
            'mojo': MojoModel()
        }

    def get_extractor(self, file_path: Path) -> Optional[CodeExtractor]:
        """Get appropriate extractor for a file."""
        for extractor in self.extractors.values():
            if extractor.can_handle_file(file_path):
                return extractor
        return None

    def get_model(self, language: str) -> Optional[CodeModel]:
        """Get appropriate model for a language."""
        return self.models.get(language.lower())

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
@click.option(
    '--language',
    '-l',
    type=str,
    help='Force specific language analysis (e.g., mojo).'
)
def analyze(
    target: str,
    checks: Optional[List[str]],
    timeout: int,
    no_cache: bool,
    no_fix_suggestions: bool,
    output_format: str,
    language: Optional[str]
):
    """Run code analysis on the specified target.

    TARGET is the path to the file or directory to analyze.
    """
    try:
        # Initialize components
        handler = LanguageHandler()
        tool = AnalysisTool()
        target_path = Path(target)

        # Get appropriate extractor and model
        if language:
            extractor = handler.extractors.get(language.lower())
            model = handler.models.get(language.lower())
            if not extractor or not model:
                raise click.UsageError(f"Language '{language}' not supported")
        else:
            extractor = handler.get_extractor(target_path)
            if not extractor:
                raise click.UsageError(
                    f"Could not determine appropriate analyzer for {target}"
                )
            file_type = extractor.get_file_type(target_path)
            model = handler.get_model(file_type) if file_type else None

        if not model:
            raise click.UsageError(
                f"No analysis model available for {target}"
            )

        # Extract code
        files = extractor.extract_code(target_path)
        if not files:
            click.echo("No files found to analyze.")
            return

        # Analyze each file
        all_issues = []
        for file_path, content in files.items():
            context = AnalysisContext(
                file_path=Path(file_path),
                content=content,
                language=model.get_supported_languages()[0],
                config=tool.get_config()
            )
            issues = model.analyze(context)
            all_issues.extend(issues)

        # Process results
        results = tool.create_results(
            success=True,
            issues=all_issues,
            stats={
                'files_analyzed': len(files),
                'issues_found': len(all_issues)
            }
        )

        # Output results
        if output_format == 'json':
            click.echo(results.to_json())
        else:
            click.echo(tool.summarize_results(results))

        # Exit with status code based on success and issues
        exit(1 if all_issues else 0)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)
