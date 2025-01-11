from memory import memset_zero
from utils.result import Result, Ok, Error
from utils.vector import DynamicVector
from utils.string import String
from utils.path import Path

struct AnalysisTool:
    """Tool for analyzing code and system interactions."""

    var config: DynamicVector[String]
    var working_dir: Path

    fn __init__(inout self, working_dir: Path):
        """Initialize the analysis tool.

        Args:
            working_dir: Working directory for analysis
        """
        self.working_dir = working_dir
        self.config = DynamicVector[String]()

    fn analyze_file(self, file_path: Path) -> Result[DynamicVector[String], String]:
        """Analyze a single file for potential issues.

        Args:
            file_path: Path to file to analyze

        Returns:
            Result containing either findings or error message
        """
        if not file_path.exists():
            return Error("File not found: " + str(file_path))

        var findings = DynamicVector[String]()

        # Check for system interactions
        try:
            let content = file_path.read_text()

            # Check for command execution
            if "system(" in content or "popen(" in content or "subprocess.run(" in content:
                findings.append("Found command execution in " + str(file_path))

            # Check for file operations
            if "open(" in content or "write(" in content:
                findings.append("Found file operations in " + str(file_path))

            # Check for network calls
            if "urlopen(" in content or "requests." in content:
                findings.append("Found network operations in " + str(file_path))

            return Ok(findings)

        except:
            return Error("Failed to analyze file: " + str(file_path))

    fn analyze_directory(
        self,
        dir_path: Path,
        recursive: Bool = True
    ) -> Result[DynamicVector[String], String]:
        """Analyze all files in a directory.

        Args:
            dir_path: Directory to analyze
            recursive: Whether to analyze subdirectories

        Returns:
            Result containing either findings or error message
        """
        if not dir_path.exists():
            return Error("Directory not found: " + str(dir_path))

        if not dir_path.is_dir():
            return Error("Path is not a directory: " + str(dir_path))

        var all_findings = DynamicVector[String]()

        try:
            let pattern = "**/*.py" if recursive else "*.py"
            for file in dir_path.glob(pattern):
                match self.analyze_file(file):
                    case Ok(findings):
                        all_findings.extend(findings)
                    case Error(err):
                        all_findings.append("Error analyzing " + str(file) + ": " + err)

            return Ok(all_findings)

        except:
            return Error("Failed to analyze directory: " + str(dir_path))

    fn get_summary(self, findings: DynamicVector[String]) -> String:
        """Generate a summary of analysis findings.

        Args:
            findings: Vector of analysis findings

        Returns:
            Summary string
        """
        var summary = String("Analysis Summary:\n")
        summary += "----------------\n"
        summary += "Total findings: " + str(len(findings)) + "\n\n"

        var command_exec = 0
        var file_ops = 0
        var network_ops = 0

        for finding in findings:
            if "command execution" in finding:
                command_exec += 1
            elif "file operations" in finding:
                file_ops += 1
            elif "network operations" in finding:
                network_ops += 1

        summary += "Command execution findings: " + str(command_exec) + "\n"
        summary += "File operation findings: " + str(file_ops) + "\n"
        summary += "Network operation findings: " + str(network_ops) + "\n"

        return summary
