import base64
import json
import logging
import os

import streamlit as st

from utils import UtilHandler  # type: ignore

logger = logging.getLogger(__name__)

# Initialize a utility handler and store it in session state if not already present.
if "utils" not in st.session_state:
    st.session_state.utils = UtilHandler(
        log_level=os.getenv("LOG_LEVEL", "INFO").upper()
    )

utils = st.session_state.utils

# Set up Streamlit configuration.
st.set_page_config(
    page_title="Conversational Search Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Answer App")

# Sidebar for session ID input
st.sidebar.header("Session Settings")
if "session_id" not in st.session_state:
    st.session_state.session_id = "-"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

session_id = st.sidebar.text_input("Session ID", value=st.session_state.session_id)

# Option to clear chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.session_state.session_id = "-"

# Handle form submission
if question := st.chat_input("Enter your question:"):
    with st.spinner("Sending request..."):
        st.session_state.chat_history.append({"type": "user", "content": question})

        # Send the question to the Conversational Search Agent backend.
        response = utils.send_request(question, session_id)
        logger.debug(f"Response: {json.dumps(response, indent=2)}")
        try:
            encoded_markdown = response["markdown"]
        except KeyError:
            st.error("No markdown returned.")
            encoded_markdown = ""

        # Decode the markdown and escape dollar signs to prevent rendering as MathJax or LaTeX.
        decoded_markdown = (
            base64.b64decode(encoded_markdown).decode("utf-8").replace("$", "\\$")
        )

        # Write it to a local file for offline debugging.
        if os.getenv("LOCAL_DEBUG"):
            with open(".log/answer.md", "w") as f:
                logger.debug(f"Writing markdown to .log/answer.md...")
                f.write(decoded_markdown)

        # Get the session ID if it was returned in the response.
        session_id = response.get("session", {}).get("name", "").split("/")[-1]

        # Get the latency.
        try:
            latency = response["latency"]
        except KeyError:
            st.error("No latency returned.")
            latency = 9999

        # Update chat history
        st.session_state.chat_history.append(
            {"type": "assistant", "content": decoded_markdown}
        )

        # Update the session ID and latency to 2 decimal places in the session state.
        st.session_state.session_id = session_id
        st.session_state.latency = f"{latency:.2f} seconds"

        # Update the sidebar with the session information.
        st.sidebar.markdown(f"**Session ID:** {st.session_state.session_id}")
        st.sidebar.markdown(f"**Latency:** {st.session_state.latency}")

# Display chat history.
avatars = {"user": "🦖", "assistant": "🤖"}
for message in st.session_state.chat_history:
    avatar = avatars[message["type"]]
    st.chat_message(message["type"], avatar=avatar).write(message["content"])
