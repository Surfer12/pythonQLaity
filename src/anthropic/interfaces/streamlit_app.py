import os
from typing import Dict, List

import streamlit as st
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

# Define the default system prompt
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."

def display_claude_response(
    full_response: dict,
    placeholder: st.empty,
    text_color: str = "#FFFFFF",
):
    # ... existing code ...

def construct_messages_for_claude(
    system_prompt: str,
    chat_history: List[Dict[str, str]],
    user_input: str,
) -> List[Dict[str, str]]:
    # ... existing code ...

def main():
    # ... existing code ...
    with st.sidebar:
        # ... existing code ...
        if st.button("Clear Chat History"):
            st.session_state.messages = []

    # Initialize chat history in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Get user input
    if prompt := st.chat_input("What is up?"):
        # Add user message to the state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Construct messages for Claude
        messages_for_claude = construct_messages_for_claude(
            st.session_state.get("system_prompt", DEFAULT_SYSTEM_PROMPT),
            st.session_state.messages[:-1],
            prompt,
        )

        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = send_claude_message(messages_for_claude)
            display_claude_response(full_response, message_placeholder)

        # Add assistant response to the state
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response.get("content", "")}
        )

    # Initialize the model selection in the sidebar
    if "model_name" not in st.session_state:
        st.session_state.model_name = "claude-3-opus-20240229"

    # Sidebar for settings
    with st.sidebar:
        st.header("Model Settings")
        model_name = st.selectbox(
            "Choose a model",
            ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-2.1"],
            index=0,
            key="model_name",
        )
        if st.session_state.model_name != model_name:
            st.session_state.model_name = model_name
            st.experimental_rerun()

        st.header("System Prompt")
        system_prompt = st.text_area(
            "Enter your system prompt here:",
            value=st.session_state.get("system_prompt", DEFAULT_SYSTEM_PROMPT),
            height=200,
            key="system_prompt",
        )
        if st.session_state.system_prompt != system_prompt:
            st.session_state.system_prompt = system_prompt
            st.experimental_rerun()

        st.header("API Key")
        api_key_input = st.text_input(
            "Enter your Anthropic API key:",
            type="password",
            key="anthropic_api_key",
            help="You can find your API key on the Anthropic website.",
        )
        if api_key_input:
            os.environ["ANTHROPIC_API_KEY"] = api_key_input

        st.header("Response Formatting")
        response_format = st.selectbox(
            "Response Format",
            options=["markdown", "json"],
            index=0,
            key="response_format",
            help="Choose the format for displaying the assistant's response.",
        )
        st.session_state.response_format = response_format

        st.header("Example Prompts")
        example_prompts = {
            "Code Explanation": "Explain this code snippet.",
            "Creative Writing": "Write a short story about a cat.",
            "Summarization": "Summarize the following text.",
        }
        selected_example = st.selectbox("Choose an example prompt", example_prompts.keys())
        if st.button("Load Example"):
            st.session_state.chat_input = example_prompts[selected_example]

        st.header("Temperature Setting")
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("temperature", 0.7),
            step=0.01,
            key="temperature",
            help="Adjust the randomness of the responses.",
        )
        st.session_state.temperature = temperature

if __name__ == "__main__":
    main()
