from typing import List, Any

class ToolResult:
    """
    A base class for tool results.
    """
    def __init__(self, success: bool, data: Any = None, errors: List[str] = None):
        self.success = success
        self.data = data
        self.errors = errors if errors else []

class ToolCollection:
    """
    A base class for a collection of tools.
    """
    def __init__(self, tools: List[Any] = None):
        self.tools = tools if tools else []

    def add_tool(self, tool: Any):
        self.tools.append(tool)

    def run_all(self):
        results = []
        for tool in self.tools:
            results.append(tool.run())
        return results
