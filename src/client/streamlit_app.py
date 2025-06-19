import asyncio
import base64
import json
import logging
import os
import pathlib
import sys
from typing import Any

import streamlit as st
from streamlit_feedback import streamlit_feedback

# Hack to get streamlit to recognize the src layout package.
python_path = str(pathlib.Path(__file__).resolve().parent.parent)
sys.path.insert(0, python_path)

from client.utils import utils

logger = logging.getLogger(__name__)
logger.debug("Streamlit app starting...")
logger.debug(f"Streamlit version: {st.__version__}")


def log_context() -> None:
    """Log the Streamlit context and session state."""
    logger.debug("[LOG_CONTEXT]")
    logger.debug(f"Cookies:\n{json.dumps(st.context.cookies.to_dict(), indent=2)}")
    logger.debug(f"Headers:\n{json.dumps(st.context.headers.to_dict(), indent=2)}")


def setup_app() -> None:
    """Set up Streamlit configuration."""
    logger.debug("[SETUP_APP]")
    st.set_page_config(
        page_title="Conversational Search",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Answer App")

    log_context()

    return


async def get_session_history() -> list[str]:
    """Get the session history for the current user."""
    logger.debug("[GET_SESSION_HISTORY]")

    route: str = "/sessions/"
    user_id: str = st.experimental_user["email"]
    data: dict[str, str] = {"user_id": user_id}
    logger.debug(f"Getting session history for user {user_id}...")

    response: dict[str, Any] = await utils.send_request(
        route=route,
        data=data,
        method="GET",
    )
    logger.debug(f"Response:\n{json.dumps(response, indent=2)}")

    session_history: list[str] = [
        session["turns"][0]["query"]["text"] for session in response.get("sessions", [])
    ]
    logger.debug(f"Session history: {session_history}")
    return session_history


async def initialize() -> None:
    """Initialize the Streamlit app session state and sidebar."""
    logger.debug("[INITIALIZE]")

    # Initialize session state variables.
    if "answer_query_token" not in st.session_state:
        st.session_state["answer_query_token"] = ""
    if "question" not in st.session_state:
        st.session_state["question"] = ""
    if "answer_text" not in st.session_state:
        st.session_state["answer_text"] = ""
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = "-"
    if "session_history" not in st.session_state:
        st.session_state["session_history"] = await get_session_history()
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    st.session_state["avatars"] = {"user": "🦖", "assistant": "🤖"}

    # Sidebar - user authentication details.
    st.sidebar.header("User Settings", divider="rainbow")
    st.sidebar.markdown(f"Welcome! {st.experimental_user['name']}")
    st.sidebar.markdown(f"**User ID:** {st.experimental_user['email']}")
    st.sidebar.button("Log out", on_click=st.logout)

    # Sidebar - session details.
    st.sidebar.header("Session Settings", divider="rainbow")
    if st.sidebar.button("Start new session"):
        st.session_state["answer_query_token"] = ""
        st.session_state["question"] = ""
        st.session_state["answer_text"] = ""
        st.session_state["session_id"] = "-"
        st.session_state["chat_history"] = []

    # Option to input a session ID.
    st.session_state["session_id"] = st.sidebar.text_input(
        "Session ID", value=st.session_state["session_id"]
    )

    # Display the last 5 sessions in the sidebar.
    st.sidebar.markdown(f"**Session History:**")
    for session in st.session_state["session_history"][-5:]:
        st.sidebar.markdown(f"{session}")

    return


def display_chat_history() -> None:
    """Display chat history."""
    logger.debug("[DISPLAY_CHAT_HISTORY]")
    for message in st.session_state["chat_history"]:
        avatar = st.session_state["avatars"][message["type"]]
        with st.chat_message(message["type"], avatar=avatar):
            st.markdown(message["content"])

    return


async def form_submission() -> None:
    """Handle form submission and display the answer."""
    logger.debug("[FORM_SUBMISSION]")
    if question := st.chat_input("Enter your question:"):

        # Update the session state with the question.
        st.session_state["question"] = question
        st.session_state["chat_history"].append({"type": "user", "content": question})

        # Display the user's question in the chat.
        st.chat_message(
            name="user",
            avatar=st.session_state["avatars"]["user"],
        ).write(question)

        # Initialize and empty AI chat bubble in a context manager.
        with st.chat_message(
            "assistant", avatar=st.session_state["avatars"]["assistant"]
        ):
            message_placeholder = st.empty()

            # Send the question to the Conversational Search backend.
            logger.info("Sending question to backend...")

            route = "/answer"
            data = {
                "question": question,
                "session_id": st.session_state["session_id"],
                "user_pseudo_id": st.experimental_user["email"],
            }
            logger.debug(f"Data:\n{json.dumps(data, indent=2)}")

            response: dict[str, Any] = await utils.send_request(
                route=route,
                data=data,
                method="POST",
            )
            logger.debug(f"Response:\n{json.dumps(response, indent=2)}")

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
            st.session_state["chat_history"].append(
                {"type": "assistant", "content": decoded_markdown}
            )

            # Write it to a local file for offline debugging.
            if os.getenv("LOCAL_DEBUG"):
                with open(".log/answer.md", "w") as f:
                    logger.debug(f"Writing markdown to .log/answer.md...")
                    f.write(decoded_markdown)

            # Get the answer text and update the session state.
            try:
                st.session_state["answer_text"] = response["answer"]["answer_text"]
                logger.debug(f"Answer text: {st.session_state['answer_text']}")
            except KeyError:
                logger.error("No answer text returned.")
                st.error("No answer text returned.")
                st.session_state["answer_text"] = ""

            # Get the session ID if it was returned in the response and update the sidebar.
            st.session_state["session_id"] = (
                response.get("session", {}).get("name", "").split("/")[-1]
            )
            st.sidebar.markdown(f"**Session ID:** {st.session_state['session_id']}")

            # Get the latency and update the sidebar.
            try:
                st.session_state["latency"] = response["latency"]
            except KeyError:
                logger.error("No latency returned.")
                st.error("No latency returned.")
                st.session_state.latency = 9999
            st.sidebar.markdown(
                f"**Latency:** {st.session_state['latency']:.2f} seconds"
            )

            # Get the answer query token.
            try:
                st.session_state["answer_query_token"] = response["answer_query_token"]
                logger.debug(
                    f"Answer query token: {st.session_state['answer_query_token']}"
                )
            except KeyError:
                logger.error("No answer query token returned.")
                st.error("No answer query token returned.")
                st.session_state["answer_query_token"] = ""

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
    logger.debug("[SEND_FEEDBACK]")
    logger.info("Sending feedback...")
    logger.debug(f"Feedback: {feedback}")

    # Map the streamlit_feedback "score" return symbol to a numerical score.
    scores: dict[str, int] = {"👍": 1, "👎": 0}
    score: int | None = scores.get(feedback["score"])

    # Send the feedback to the backend.
    route: str = "/feedback"
    data: dict[str, Any] = {
        "answer_query_token": st.session_state["answer_query_token"],
        "question": st.session_state["question"],
        "answer_text": st.session_state["answer_text"],
        "feedback_value": score,
        "feedback_text": feedback.get("text"),
    }
    logger.debug(f"Feedback data: {data}")

    response: dict[str, Any] = await utils.send_request(
        route=route,
        data=data,
        method="POST",
    )
    logger.info(f"Feedback response: {response}")

    # Display a success message.
    st.success("Feedback submitted. Thank you!")

    return


async def user_feedback() -> None:
    """Display a user feedback form. Use the send_feedback function as the callback."""
    logger.debug("[USER_FEEDBACK]")
    if st.session_state.get("answer_query_token"):
        feedback: dict[str, Any] = streamlit_feedback(
            feedback_type="thumbs",
            optional_text_label="Please provide feedback on the answer.",
            # on_submit=send_feedback,
            key=f"feedback_{st.session_state['answer_query_token']}",
        )

        # Send the feedback to the backend.
        if feedback:
            await send_feedback(feedback)

    return


async def main() -> None:
    """Main function."""
    # Log the initial session state.
    logger.info(
        f"[START] Session state:\n{json.dumps(st.session_state.to_dict(), indent=2)}"
    )

    # Setup the Streamlit app.
    setup_app()

    if not st.experimental_user.is_logged_in:
        st.button("Log in with Google", on_click=st.login, args=["google"])
        logger.debug("User not logged in.")
        st.stop()

    logger.debug("User logged in.")
    await initialize()
    display_chat_history()
    await form_submission()
    await user_feedback()

    # Log the final session state.
    logger.info(
        f"[END] Session state:\n{json.dumps(st.session_state.to_dict(), indent=2)}"
    )

    return


if __name__ == "__main__":
    asyncio.run(main())
