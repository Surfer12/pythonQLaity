"""Tool for running Code Sentinel analysis."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

@dataclass
class AnalysisResult:
    """Result from running Code Sentinel analysis."""
    success: bool
    issues: List[Dict]
    stats: Dict
    error: Optional[str] = None

class AnalysisTool:
    """Tool for running Code Sentinel analysis."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the analysis tool.

        Args:
            config_path: Path to configuration file. If None, uses default config.
        """
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "default.yml"
        if not self.config_path.exists():
            raise ValueError(f"Configuration not found at {self.config_path}")

    def analyze_code(
        self,
        target: Union[str, Path],
        *,
        checks: Optional[List[str]] = None,
        timeout: int = 30,
        cache: bool = True,
        fix_suggestions: bool = True
    ) -> AnalysisResult:
        """Analyze code using configured rules.

        Args:
            target: Path to file or directory to analyze
            checks: List of specific checks to run, or None for all checks
            timeout: Analysis timeout in seconds
            cache: Enable result caching
            fix_suggestions: Include fix suggestions in output

        Returns:
            AnalysisResult containing analysis results and stats
        """
        try:
            # Build analysis configuration
            config = {
                "target": str(Path(target).resolve()),
                "timeout": timeout,
                "cache_enabled": cache,
                "generate_fixes": fix_suggestions,
                "checks": checks or ["all"]
            }

            # Run analysis (placeholder for actual implementation)
            # This will be replaced with actual analysis logic
            results = self._run_analysis(config)

            return AnalysisResult(
                success=True,
                issues=results.get("issues", []),
                stats=results.get("stats", {})
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                issues=[],
                stats={},
                error=f"Error running analysis: {str(e)}"
            )

    def _run_analysis(self, config: Dict) -> Dict:
        """Run the actual analysis.

        This is a placeholder that will be implemented with actual analysis logic.
        """
        # Placeholder implementation
        return {
            "issues": [],
            "stats": {
                "files_analyzed": 0,
                "analysis_time": 0.0
            }
        }

    def summarize_results(self, results: AnalysisResult) -> str:
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
                    summary.append(
                        f"- {issue['type']} in {issue['file']} line {issue['line']}"
                    )
                    if issue.get('fix_suggestion'):
                        summary.append(f"  Suggestion: {issue['fix_suggestion']}")

        # Add stats
        if results.stats:
            summary.append("\nAnalysis Stats:")
            for key, value in results.stats.items():
                summary.append(f"{key}: {value}")

        return "\n".join(summary)

    def get_fix_recommendations(self, results: AnalysisResult) -> List[Dict]:
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
                    'current_code': issue.get('snippet', ''),
                    'suggestion': issue['fix_suggestion']
                })

        return sorted(
            recommendations,
            key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['severity']]
        )
