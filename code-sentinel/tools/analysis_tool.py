import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Union
from dataclasses import dataclass

@dataclass
class AnalysisToolResult:
    """Result from running Code Sentinel analysis."""
    success: bool
    issues: List[Dict]
    stats: Dict
    error: Optional[str] = None

class AnalysisTool:
    """Tool for running Code Sentinel analysis in the Computer Use Demo environment."""

    def __init__(self, sentinel_path: Optional[Path] = None):
        """Initialize the analysis tool.

        Args:
            sentinel_path: Path to Code Sentinel installation. If None, assumes it's in the same
                         directory as computer-use-demo.
        """
        self.sentinel_path = sentinel_path or Path(__file__).parent.parent
        self.cli_path = self.sentinel_path / "cli" / "main.py"

        if not self.cli_path.exists():
            raise ValueError(f"Code Sentinel CLI not found at {self.cli_path}")

    def analyze_directory(
        self,
        directory: Union[str, Path],
        *,
        claude_mode: bool = True,
        timeout: int = 30,
        cache: bool = True,
        fix_suggestions: bool = True
    ) -> AnalysisToolResult:
        """Analyze a directory using Code Sentinel.

        Args:
            directory: Path to directory to analyze
            claude_mode: Enable Claude-specific checks
            timeout: Analysis timeout in seconds
            cache: Enable result caching
            fix_suggestions: Include fix suggestions in output

        Returns:
            AnalysisToolResult containing analysis results and stats
        """
        try:
            # Build command
            cmd = [
                "python",
                str(self.cli_path),
                "analyze",
                str(Path(directory).expanduser()),
                "--format", "json",
                "--timeout", str(timeout)
            ]

            if claude_mode:
                cmd.append("--claude-mode")
            if not cache:
                cmd.append("--no-cache")
            if not fix_suggestions:
                cmd.append("--no-fix-suggestions")

            # Run analysis
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output
            output = json.loads(result.stdout)
            return AnalysisToolResult(
                success=True,
                issues=output["issues"],
                stats=output["stats"]
            )

        except subprocess.CalledProcessError as e:
            return AnalysisToolResult(
                success=False,
                issues=[],
                stats={},
                error=f"Analysis failed: {e.stderr}"
            )
        except Exception as e:
            return AnalysisToolResult(
                success=False,
                issues=[],
                stats={},
                error=f"Error running analysis: {str(e)}"
            )

    def summarize_results(self, results: AnalysisToolResult) -> str:
        """Generate a human-readable summary of analysis results.

        Args:
            results: Analysis results to summarize

        Returns:
            String containing the summary
        """
        if not results.success:
            return f"Analysis failed: {results.error}"

        if not results.issues:
            return "No issues found in the analyzed code."

        # Group issues by severity
        issues_by_severity = {
            "high": [],
            "medium": [],
            "low": []
        }
        for issue in results.issues:
            issues_by_severity[issue["severity"]].append(issue)

        # Build summary
        summary = [f"Found {len(results.issues)} issues:"]

        for severity in ["high", "medium", "low"]:
            sev_issues = issues_by_severity[severity]
            if sev_issues:
                summary.append(f"\n{severity.upper()} severity issues:")
                for issue in sev_issues:
                    summary.append(f"- {issue['type']} in {issue['file']} line {issue['line']}")
                    if issue.get('fix_suggestion'):
                        summary.append(f"  Suggestion: {issue['fix_suggestion']}")

        # Add stats
        summary.append(f"\nAnalysis Stats:")
        summary.append(f"Files analyzed: {results.stats['files_analyzed']}")
        summary.append(f"Analysis time: {results.stats['analysis_time']:.2f} seconds")

        return "\n".join(summary)

    def get_fix_recommendations(self, results: AnalysisToolResult) -> List[Dict]:
        """Generate structured fix recommendations from analysis results.

        Args:
            results: Analysis results to generate recommendations from

        Returns:
            List of fix recommendations with file, line, and suggested changes
        """
        if not results.success or not results.issues:
            return []

        recommendations = []
        for issue in results.issues:
            if issue.get('fix_suggestion'):
                recommendations.append({
                    'file': issue['file'],
                    'line': issue['line'],
                    'type': issue['type'],
                    'severity': issue['severity'],
                    'current_code': issue['snippet'],
                    'suggestion': issue['fix_suggestion']
                })

        return sorted(
            recommendations,
            key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['severity']]
        )
