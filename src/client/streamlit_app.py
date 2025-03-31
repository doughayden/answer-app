import asyncio
import base64
import json
import logging
import os
from typing import Any
import uuid

import streamlit as st
from streamlit_feedback import streamlit_feedback

from utils import UtilHandler  # type: ignore


logger = logging.getLogger(__name__)
logger.debug("Streamlit app starting...")
logger.debug(f"Streamlit version: {st.__version__}")


def get_user_id() -> str:
    """Get the user ID from the Streamlit context."""
    user_id = st.session_state.get("user_id", f"test_user_{uuid.uuid4()}")
    logger.debug(f"User ID: {user_id}")
    return user_id


def get_session_history(user_id: str) -> list[str]:
    """Get the session history for the current user."""
    logger.debug(f"Getting session history for user {user_id}...")
    session_history = []
    return session_history


def setup_app() -> None:
    """Set up Streamlit configuration."""
    st.set_page_config(
        page_title="Conversational Search",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Answer App")

    cookies = st.context.cookies
    logger.debug(f"Cookies: {cookies.to_dict()}")
    headers = st.context.headers
    logger.debug(f"Headers: {headers.to_dict()}")

    # Initialize session state variables.
    if "utils" not in st.session_state:
        st.session_state.utils = UtilHandler(
            log_level=os.getenv("LOG_LEVEL", "INFO").upper()
        )
    if "answer_query_token" not in st.session_state:
        st.session_state.answer_query_token = ""
    if "question" not in st.session_state:
        st.session_state.question = ""
    if "answer_text" not in st.session_state:
        st.session_state.answer_text = ""
    if "session_id" not in st.session_state:
        st.session_state.session_id = "-"
    if "user_id" not in st.session_state:
        st.session_state.user_id = get_user_id()
    if "session_history" not in st.session_state:
        st.session_state.session_history = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    st.session_state.avatars = {"user": "🦖", "assistant": "🤖"}

    # Sidebar for session ID input.
    st.sidebar.header("Session Settings")
    st.session_state.session_id = st.sidebar.text_input(
        "Session ID", value=st.session_state.session_id
    )
    st.sidebar.markdown(f"**User ID:** {st.session_state.user_id}")
    st.sidebar.markdown(f"**Session History:** {st.session_state.session_history}")

    # Option to clear chat history and start a new session.
    if st.sidebar.button("Clear Chat History"):
        st.session_state.answer_query_token = ""
        st.session_state.question = ""
        st.session_state.answer_text = ""
        st.session_state.session_id = "-"
        st.session_state.chat_history = []

    return


def display_chat_history() -> None:
    """Display chat history."""
    for message in st.session_state.chat_history:
        avatar = st.session_state.avatars[message["type"]]
        with st.chat_message(message["type"], avatar=avatar):
            st.markdown(message["content"])

    return


async def form_submission() -> None:
    """Handle form submission and display the answer."""
    if question := st.chat_input("Enter your question:"):

        # Update the session state with the question.
        st.session_state.question = question
        st.session_state.chat_history.append({"type": "user", "content": question})

        # Display the user's question in the chat.
        st.chat_message("user", avatar=st.session_state.avatars["user"]).write(question)

        # Initialize and empty AI chat bubble in a context manager.
        with st.chat_message("assistant", avatar=st.session_state.avatars["assistant"]):
            message_placeholder = st.empty()

            # Send the question to the Conversational Search backend.
            logger.info("Sending question to backend...")
            data = {
                "question": question,
                "session_id": st.session_state.session_id,
                "user_pseudo_id": st.session_state.user_id,
            }
            logger.debug(f"Data: {json.dumps(data, indent=2)}")
            route = "/answer"
            response = await st.session_state.utils.send_request(route=route, data=data)
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
                st.session_state.latency = 9999
            st.sidebar.markdown(f"**Latency:** {st.session_state.latency:.2f} seconds")

            # Get the answer query token.
            try:
                st.session_state.answer_query_token = response["answer_query_token"]
                logger.debug(
                    f"Answer query token: {st.session_state.answer_query_token}"
                )
            except KeyError:
                logger.error("No answer query token returned.")
                st.error("No answer query token returned.")
                st.session_state.answer_query_token = ""

    return


async def send_feedback(feedback: dict[str, Any]) -> None:
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
    route = "/feedback"
    response = await st.session_state.utils.send_request(route=route, data=data)
    logger.info(f"Feedback response: {response}")

    # Display a success message.
    st.success("Feedback submitted. Thank you!")

    return


async def user_feedback() -> None:
    """Display a user feedback form. Use the send_feedback function as the callback."""
    if st.session_state.get("answer_query_token"):
        feedback = streamlit_feedback(
            feedback_type="thumbs",
            optional_text_label="Please provide feedback on the answer.",
            # on_submit=send_feedback,
            key=f"feedback_{st.session_state.answer_query_token}",
        )

        # Send the feedback to the backend.
        if feedback:
            await send_feedback(feedback)

    return


async def main() -> None:
    """Main function."""
    # Log the initial session state for debugging.
    logger.debug(f"[START] Session state: {st.session_state}")

    # Run tha app components.
    setup_app()
    display_chat_history()
    await form_submission()
    await user_feedback()

    # Log the final session state for debugging.
    logger.debug(f"[END] Session state: {st.session_state}")

    return


if __name__ == "__main__":
    asyncio.run(main())
