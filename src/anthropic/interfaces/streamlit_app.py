"""
Streamlit interface for the Anthropic Claude demo.
"""

import asyncio
import base64
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import StrEnum
from functools import partial
from pathlib import PosixPath
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Generator,
)

import httpx
import streamlit as st
from anthropic import RateLimitError
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)

from computer_use_demo.loop import (
    PROVIDER_TO_DEFAULT_MODEL_NAME,
    APIProvider,
    sampling_loop,
)
from computer_use_demo.tools import ToolResult

CONFIG_DIR = PosixPath("~/.anthropic").expanduser()
API_KEY_FILE = CONFIG_DIR / "api_key"

STREAMLIT_STYLE = """
<style>
    /* Highlight the stop button in red */
    button[kind=header] {
        background-color: rgb(255, 75, 75);
        border: 1px solid rgb(255, 75, 75);
        color: rgb(255, 255, 255);
    }
    button[kind=header]:hover {
        background-color: rgb(255, 51, 51);
    }
    /* Hide the streamlit deploy button */
    .stAppDeployButton {
        visibility: hidden;
    }
</style>
"""


def setup_page() -> None:
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title="Claude Demo",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)


def load_api_key() -> Optional[str]:
    """
    Load the API key from environment or config file.

    Returns:
        Optional[str]: The API key if found, None otherwise
    """
    # Try environment variable first
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    # Try config file
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()

    return None


def save_api_key(api_key: str) -> None:
    """
    Save the API key to the config file.

    Args:
        api_key: The API key to save
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    API_KEY_FILE.write_text(api_key)


@contextmanager
def loading_spinner(text: str) -> Generator[None, None, None]:
    """
    Context manager for showing a loading spinner.

    Args:
        text: The text to show while loading
    """
    try:
        with st.spinner(text):
            yield
    finally:
        pass


def handle_tool_result(result: ToolResult) -> None:
    """
    Display a tool result in the Streamlit interface.

    Args:
        result: The tool result to display
    """
    st.markdown(f"**Tool:** {result.tool_name}")
    st.markdown(f"**Call ID:** {result.tool_call_id}")

    with st.expander("Arguments"):
        st.json(result.args)

    with st.expander("Output"):
        st.json(result.output)


def format_messages(
    chat_history: List[Dict[str, Any]],
    user_input: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Format chat history and user input into messages for Claude.

    Args:
        chat_history: List of previous messages
        user_input: Optional new user input

    Returns:
        Formatted messages for Claude API
    """
    formatted_msgs = []

    # Add chat history
    for msg in chat_history:
        formatted_msgs.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    # Add new user input if provided
    if user_input:
        formatted_msgs.append({
            "role": "user",
            "content": user_input,
        })

    return formatted_msgs


def main() -> None:
    """Main Streamlit application."""
    setup_page()
    st.title("Claude Demo")

    # API Key Management
    api_key = load_api_key()
    if not api_key:
        api_key = st.text_input(
            "Enter your Anthropic API key:",
            type="password",
            help="Your API key will be saved locally",
        )
        if api_key:
            save_api_key(api_key)
            st.success("API key saved!")
            st.rerun()
        st.stop()

    # Sidebar Configuration
    with st.sidebar:
        st.header("Configuration")

        provider = st.selectbox(
            "API Provider",
            options=[
                APIProvider.ANTHROPIC,
                APIProvider.BEDROCK,
                APIProvider.VERTEX,
            ],
            index=0,
        )

        model = st.text_input(
            "Model",
            value=PROVIDER_TO_DEFAULT_MODEL_NAME[provider],
            help="The model to use for generation",
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            help="Controls randomness in generation",
        )

    # Chat Interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        role = message["role"]
        content = message["content"]

        with st.chat_message(role):
            if isinstance(content, str):
                st.markdown(content)
            elif isinstance(content, ToolResult):
                handle_tool_result(content)

    # User Input
    user_input = st.chat_input("Type your message here...")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
        })

        with loading_spinner("Claude is thinking..."):
            try:
                formatted_messages = format_messages(
                    st.session_state.chat_history,
                    user_input,
                )

                response_text, tool_results = asyncio.run(
                    sampling_loop(
                        client=None,  # TODO: Initialize client
                        messages=formatted_messages,
                        temperature=temperature,
                    )
                )

                with st.chat_message("assistant"):
                    st.markdown(response_text)
                    for result in tool_results:
                        handle_tool_result(result)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text,
                })

            except RateLimitError:
                st.error(
                    "Rate limit exceeded. Please wait a moment and try again."
                )
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
