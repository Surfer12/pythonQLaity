from memory import memset_zero
from collections.dict import Dict
from collections.list import List
from time import now

struct LogLevel:
    """Log levels for different types of messages."""
    var DEBUG: Int = 0
    var INFO: Int = 1
    var WARNING: Int = 2
    var ERROR: Int = 3

struct LogEntry:
    """Represents a single log entry."""
    var timestamp: Int
    var level: Int
    var message: String
    var context: Dict[String, String]

struct LoggerTool:
    """Tool for logging and monitoring system events."""

    var log_level: Int
    var log_entries: List[LogEntry]
    var max_entries: Int

    fn __init__(inout self, log_level: Int = LogLevel.INFO, max_entries: Int = 1000):
        """Initialize the logger tool.

        Args:
            log_level: Minimum level to log
            max_entries: Maximum number of entries to keep in memory
        """
        self.log_level = log_level
        self.log_entries = List[LogEntry]()
        self.max_entries = max_entries

    fn log(
        inout self,
        level: Int,
        message: String,
        context: Dict[String, String] = Dict[String, String]()
    ):
        """Log a message if its level is high enough.

        Args:
            level: Log level for this message
            message: The message to log
            context: Optional context dictionary
        """
        if level >= self.log_level:
            let entry = LogEntry(
                timestamp=now(),
                level=level,
                message=message,
                context=context
            )

            self.log_entries.append(entry)

            # Trim old entries if we exceed max
            if len(self.log_entries) > self.max_entries:
                self.log_entries = self.log_entries[1:]

    fn debug(inout self, message: String, context: Dict[String, String] = Dict[String, String]()):
        """Log a debug message.

        Args:
            message: The debug message
            context: Optional context dictionary
        """
        self.log(LogLevel.DEBUG, message, context)

    fn info(inout self, message: String, context: Dict[String, String] = Dict[String, String]()):
        """Log an info message.

        Args:
            message: The info message
            context: Optional context dictionary
        """
        self.log(LogLevel.INFO, message, context)

    fn warning(inout self, message: String, context: Dict[String, String] = Dict[String, String]()):
        """Log a warning message.

        Args:
            message: The warning message
            context: Optional context dictionary
        """
        self.log(LogLevel.WARNING, message, context)

    fn error(inout self, message: String, context: Dict[String, String] = Dict[String, String]()):
        """Log an error message.

        Args:
            message: The error message
            context: Optional context dictionary
        """
        self.log(LogLevel.ERROR, message, context)

    fn get_logs(self, min_level: Int = LogLevel.DEBUG) -> List[LogEntry]:
        """Get all logs at or above the specified level.

        Args:
            min_level: Minimum log level to include

        Returns:
            List of matching log entries
        """
        return [entry for entry in self.log_entries if entry.level >= min_level]

    fn clear(inout self):
        """Clear all log entries."""
        self.log_entries.clear()
