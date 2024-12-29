import base64
import os

import streamlit as st

from utils import UtilHandler

# Initialize a utility handler.
utils = UtilHandler(log_level=os.getenv("LOG_LEVEL", "DEBUG").upper())

# Set up Streamlit configuration
st.set_page_config(
    page_title="Conversational Search Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize the console for rich output.
st.title("Answer App")

# Sidebar for session ID input
st.sidebar.header("Session Settings")
if "session_id" not in st.session_state:
    st.session_state.session_id = "-"

session_id = st.sidebar.text_input("Session ID", value=st.session_state.session_id)

# Main input for the question
with st.form(key="question_form"):
    question = st.text_input("Enter your question:", key="question_input")
    submit_button = st.form_submit_button(label="Ask")

# Handle form submission
if submit_button:
    if question:
        with st.spinner("Sending request..."):
            response = utils.send_request(question, session_id)
            try:
                encoded_markdown = response["markdown"]
            except KeyError:
                st.error("No markdown returned.")
                encoded_markdown = ""

            # Decode the markdown and write it to a local file for offline debugging.
            decoded_markdown = base64.b64decode(encoded_markdown).decode("utf-8")

            # Escape dollar signs to prevent rendering as MathJax or LaTeX.
            decoded_markdown = decoded_markdown.replace("$", "\\$")
            with open(".log/answer.md", "w") as f:
                f.write(decoded_markdown)

            # Get the session ID if it was returned in the response.
            session_id = response.get("session", {}).get("name", "").split("/")[-1]

            # Get the latency.
            try:
                latency = response["latency"]
            except KeyError:
                st.error("No latency returned.")
                latency = 9999

            st.success("Response received!")
            st.markdown(f"**Answer:** {decoded_markdown}")

            # Update the session ID and latency to 2 decimal places in the session state
            st.session_state.session_id = session_id
            st.session_state.latency = f"{latency:.2f} seconds"

            # Update the sidebar with the latency information
            st.sidebar.markdown(f"**Latency:** {st.session_state.latency}")
    else:
        st.error("Please enter a question.")
