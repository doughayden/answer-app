import base64
import json
import logging
import os
from typing import Any

import streamlit as st
from streamlit_feedback import streamlit_feedback

from utils import UtilHandler  # type: ignore

logger = logging.getLogger(__name__)

# Initialize a utility handler and store it in session state if not already present.
if "utils" not in st.session_state:
    st.session_state.utils = UtilHandler(
        log_level=os.getenv("LOG_LEVEL", "INFO").upper()
    )
logger.debug("Streamlit app starting...")
logger.debug(f"Session state: {st.session_state}")


def send_feedback(feedback: dict[str, Any]) -> None:
    """Send feedback to the backend.

    Args:
        feedback (dict): The feedback data from the
        streamlit_feedback form. A function used as the
        callback for the streamlit_feedback form submission
        event gets passed the feedback data as a dictionary.

    Returns:
        None
    """
    logger.info("Sending feedback...")
    logger.debug(f"Feedback: {feedback}")

    # Map the streamlit_feedback "score" return symbol to a numerical score.
    scores = {"👍": 1, "👎": 0}
    score = scores.get(feedback["score"])

    # Send the feedback to the backend.
    data = {
        "answer_query_token": st.session_state.answer_query_token,
        "question": st.session_state.question,
        "answer_text": st.session_state.answer_text,
        "feedback_value": score,
        "feedback_text": feedback.get("text"),
    }
    logger.debug(f"Feedback data: {data}")
    response = st.session_state.utils.send_request(data=data, route="/feedback")
    logger.info(f"Feedback response: {response}")

    # Display a success message.
    st.success("Feedback submitted. Thank you!")

    return


# Set up Streamlit configuration.
st.set_page_config(
    page_title="Conversational Search Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Answer App")

# Initialize session state variables.
if "answer_query_token" not in st.session_state:
    st.session_state.answer_query_token = ""
if "question" not in st.session_state:
    st.session_state.question = ""
if "answer_text" not in st.session_state:
    st.session_state.answer_text = ""
if "session_id" not in st.session_state:
    st.session_state.session_id = "-"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Sidebar for session ID input.
st.sidebar.header("Session Settings")
session_id = st.sidebar.text_input("Session ID", value=st.session_state.session_id)

# Option to clear chat history.
if st.sidebar.button("Clear Chat History"):
    st.session_state.answer_query_token = ""
    st.session_state.question = ""
    st.session_state.answer_text = ""
    st.session_state.session_id = "-"
    st.session_state.chat_history = []

# Display chat history.
avatars = {"user": "🦖", "assistant": "🤖"}
for message in st.session_state.chat_history:
    avatar = avatars[message["type"]]
    with st.chat_message(message["type"], avatar=avatar):
        st.markdown(message["content"])

# Handle form submission.
if question := st.chat_input("Enter your question:"):

    # Update the session state with the question.
    st.session_state.question = question
    st.session_state.chat_history.append({"type": "user", "content": question})

    # Display the user's question in the chat.
    st.chat_message("user", avatar=avatars["user"]).write(question)

    # Initialize and empty AI chat bubble in a context manager.
    with st.chat_message("assistant", avatar=avatars["assistant"]):
        message_placeholder = st.empty()

        # Send the question to the Conversational Search Agent backend.
        logger.info("Sending question to backend...")
        data = {"question": question, "session_id": session_id}
        route = "/answer"
        response = st.session_state.utils.send_request(data=data, route=route)
        logger.debug(f"Response: {json.dumps(response, indent=2)}")

        # Get the encoded markdown-formatted answer from the backend.
        try:
            encoded_markdown = response["markdown"]
        except KeyError:
            logger.error("No markdown returned.")
            st.error("No markdown returned.")
            encoded_markdown = ""

        # Decode it and escape dollar signs to prevent rendering as MathJax or LaTeX.
        decoded_markdown = (
            base64.b64decode(encoded_markdown).decode("utf-8").replace("$", "\\$")
        )

        # Display the formatted answer and update the chat history.
        message_placeholder.markdown(decoded_markdown)
        st.session_state.chat_history.append(
            {"type": "assistant", "content": decoded_markdown}
        )

        # Write it to a local file for offline debugging.
        if os.getenv("LOCAL_DEBUG"):
            with open(".log/answer.md", "w") as f:
                logger.debug(f"Writing markdown to .log/answer.md...")
                f.write(decoded_markdown)

        # Get the answer text and update the session state.
        try:
            st.session_state.answer_text = response["answer"]["answer_text"]
            logger.debug(f"Answer text: {st.session_state.answer_text}")
        except KeyError:
            logger.error("No answer text returned.")
            st.error("No answer text returned.")
            st.session_state.answer_text = ""

        # Get the session ID if it was returned in the response and update the sidebar.
        st.session_state.session_id = (
            response.get("session", {}).get("name", "").split("/")[-1]
        )
        st.sidebar.markdown(f"**Session ID:** {st.session_state.session_id}")

        # Get the latency and update the sidebar.
        try:
            st.session_state.latency = response["latency"]
        except KeyError:
            logger.error("No latency returned.")
            st.error("No latency returned.")
            latency = 9999
        st.sidebar.markdown(f"**Latency:** {st.session_state.latency:.2f} seconds")

        # Get the answer query token.
        try:
            st.session_state.answer_query_token = response["answer_query_token"]
            logger.debug(f"Answer query token: {st.session_state.answer_query_token}")
        except KeyError:
            logger.error("No answer query token returned.")
            st.error("No answer query token returned.")
            st.session_state.answer_query_token = ""

# Display a user feedback form.
if st.session_state.get("answer_query_token"):
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label="Please provide feedback on the answer.",
        on_submit=send_feedback,
        key=f"feedback_{st.session_state.answer_query_token}",
    )

# Log the full session state for debugging.
logger.debug(f"Session state: {st.session_state}")
