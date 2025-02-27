"""Sample client script to interact with the Agent Builder Search Engine.
To call the deployed backend service, set the AUDIENCE environment variable
to the URL of the deployed service. The default value is http://localhost:8888
for local testing when the AUDIENCE environment variable is not set.

Example local testing - 1st terminal:
uvicorn main:app --reload --host 0.0.0.0 --port 8888

Open a new terminal and run the client script:
python scripts/client.py
"""

import base64
import json
import logging
import os

from rich.console import Console
from rich.markdown import Markdown

from utils import UtilHandler  # type: ignore

logger = logging.getLogger(__name__)

# Initialize a utility handler.
utils = UtilHandler(log_level=os.getenv("LOG_LEVEL", "DEBUG").upper())

# Initialize the console for rich output.
console = Console()


def main(
    session_id: str | None = None,
) -> None:
    """Get a question from the user and send it to the Agent Builder Search Engine.

    Args:
        session_id (str | None): The session ID to use for the question.

    Returns:
        None
    """
    # Construct the prompt with a placeholder for the session ID.
    prompt = (
        "Session ID: {session_id}\n\n"
        "Enter a question to send to the Search app. Press Return to exit...\n\n"
        "QUESTION:"
        "\n\n"
    )
    print("\n")

    # Loop to get questions from the user. Exit on empty input.
    while question := input(prompt.format(session_id=session_id)):
        data = {
            "question": question,
            "session_id": session_id,
        }
        route = "/answer"
        response = utils.send_request(data=data, route=route)
        logger.debug(f"Response: {json.dumps(response, indent=2)}")

        try:
            encoded_markdown = response["markdown"]
        except KeyError:
            print("No markdown returned. Exiting...")
            break

        # Decode the markdown and write it to a local file for offline debugging.
        decoded_markdown = base64.b64decode(encoded_markdown).decode("utf-8")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(script_dir, ".log")
        markdown_filename = os.path.join(log_dir, "answer.md")
        with open(markdown_filename, "w") as f:
            f.write(decoded_markdown)

        # Print the markdown to the console.
        markdown = Markdown(decoded_markdown)
        print(2 * "\n")
        print("ANSWER: \n\n")
        console.print(markdown)
        print(2 * "\n")

        # Update the session ID if it was returned in the response.
        try:
            session_id = response["session"]["name"].split("/")[-1]
        except:
            session_id = None


if __name__ == "__main__":
    stateful = input("\n\nDo you want to maintain state? (y/n): ").lower()[0] == "y"
    main(
        session_id="-" if stateful else None,
    )
