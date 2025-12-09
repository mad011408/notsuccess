"""NEXUS AI Agent - Web Application"""

from typing import Optional


def create_web_app(agent=None, title: str = "NEXUS AI Agent"):
    """
    Create Streamlit web application

    Args:
        agent: NexusAgent instance
        title: Application title

    Returns:
        Streamlit app configuration
    """
    try:
        import streamlit as st
    except ImportError:
        raise ImportError("Streamlit not installed. Run: pip install streamlit")

    # Page config
    st.set_page_config(
        page_title=title,
        page_icon="🤖",
        layout="wide"
    )

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "agent" not in st.session_state:
        st.session_state.agent = agent

    # Header
    st.title(f"🤖 {title}")

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        # Model selection
        model = st.selectbox(
            "Model",
            ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"]
        )

        # Temperature
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7)

        # Max tokens
        max_tokens = st.slider("Max Tokens", 100, 4096, 2048)

        st.divider()

        # Tools section
        st.header("Tools")
        if st.session_state.agent:
            tools = list(st.session_state.agent._tools.keys())
            for tool in tools:
                st.checkbox(tool, value=True)

        st.divider()

        # Actions
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()

        if st.button("Reset Agent"):
            if st.session_state.agent:
                st.session_state.agent.reset()
                st.success("Agent reset!")

    # Chat interface
    chat_container = st.container()

    with chat_container:
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            if st.session_state.agent:
                import asyncio

                async def get_response():
                    full_response = ""
                    async for chunk in st.session_state.agent.run(prompt):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                    return full_response

                response = asyncio.run(get_response())
            else:
                response = "Agent not initialized. Please configure the agent."
                message_placeholder.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.session_state.agent:
            state = st.session_state.agent.get_state()
            st.metric("Status", state.get("status", "unknown"))

    with col2:
        st.metric("Messages", len(st.session_state.messages))

    with col3:
        if st.session_state.agent:
            st.metric("Iteration", st.session_state.agent.state.iteration)

    return st


def run_streamlit_app(agent=None):
    """Run streamlit app (for command line)"""
    import subprocess
    import sys

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        __file__, "--server.headless", "true"
    ])


# Streamlit entry point
if __name__ == "__main__":
    create_web_app()

