"""
Core loop functionality for the Anthropic Claude interface.

This module provides the main sampling loop and related functionality for
interacting with Claude.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from anthropic import (
    HUMAN_PROMPT,
    AI_PROMPT,
    Anthropic,
    RateLimitError,
)
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)

from computer_use_demo.tools import ToolResult

PROVIDER_TO_DEFAULT_MODEL_NAME = {
    "anthropic": "claude-2.1",
    "bedrock": "anthropic.claude-v2",
    "vertex": "claude-2",
}


class APIProvider:
    """Supported API providers for Claude."""
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


async def sampling_loop(
    client: Anthropic,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = None,
    **kwargs: Any,
) -> Tuple[str, List[ToolResult]]:
    """
    Main sampling loop for interacting with Claude.

    Args:
        client: Anthropic client instance
        messages: List of message dictionaries
        tools: Optional list of tool configurations
        tool_choice: Optional specific tool to use
        **kwargs: Additional arguments passed to create()

    Returns:
        Tuple containing:
        - Generated response text
        - List of tool results from the interaction
    """
    tool_results = []
    response_text = ""

    try:
        response = await client.messages.create(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs
        )

        for content in response.content:
            if isinstance(content, BetaTextBlockParam):
                response_text += content.text
            elif isinstance(content, BetaToolResultBlockParam):
                tool_results.append(
                    ToolResult(
                        tool_name=content.tool_name,
                        tool_call_id=content.tool_call_id,
                        args=content.args,
                        output=content.output,
                    )
                )

    except RateLimitError as e:
        # Handle rate limiting by waiting and retrying
        await handle_rate_limit(e)
        return await sampling_loop(
            client,
            messages,
            tools,
            tool_choice,
            **kwargs
        )

    return response_text, tool_results


async def handle_rate_limit(error: RateLimitError) -> None:
    """Handle rate limit errors by implementing appropriate backoff."""
    # TODO: Implement exponential backoff
    pass
