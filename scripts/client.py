"""Sample client script to interact with the Agent Builder Search Engine.
To call the deployed backend service, set the AUDIENCE environment variable
to the URL of the deployed service. The default value is http://localhost:8888
for local testing when the AUDIENCE environment variable is not set.

Example local testing - 1st terminal:
uvicorn main:app --reload --host 0.0.0.0 --port 8888

Open a new terminal and run the client script:
python scripts/client.py
"""

import json
import logging
import os
import requests

from google.auth import default

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="{levelname:<9} [{name}.{funcName}:{lineno:>5}] {message}",
    style="{",
    level=logging.DEBUG,
    handlers=[logging.FileHandler(filename="client.log", mode="w", encoding="utf-8")],
    encoding="utf-8",
)

creds, project = default()
token = creds.token

audience = os.getenv("AUDIENCE", "http://localhost:8888")


def send_request(
    question: str,
    session_id: str = "-",
) -> dict:
    """Send a request to the Discovery Engine API.

    Args:
        question (str): The question to ask the Agent Builder Search Engine.
        session_id (str): The session ID for the question.

    Returns:
        dict: The response from the Discovery Engine API.
    """
    url = f"{audience}/answer"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = {"question": question, "session_id": session_id}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def main(
    session_id: str | None = None,
) -> None:
    """Get a question from the user and send it to the Agent Builder Search Engine.

    Args:
        session_id (str | None): The session ID to use for the question.

    Returns:
        None
    """
    prompt = (
        "Session ID: {session_id}\n\n"
        "Enter a question to send to the Search app. Press Return to exit...\n\n"
        "QUESTION:"
        "\n\n"
    )
    print("\n")
    while question := input(prompt.format(session_id=session_id)):
        response = send_request(
            question=question,
            session_id=session_id,
        )
        print(2 * "\n")
        print(
            f"ANSWER: \n\n{response.get('answer', {}).get('answer_text', 'No answer returned.')}"
        )
        print(2 * "\n")
        logger.debug(f"Response: {json.dumps(response, indent=2)}")
        session_id = response.get("session", {}).get("name", "").split("/")[-1]


if __name__ == "__main__":
    stateful = input("\n\nDo you want to maintain state? (y/n): ").lower()[0] == "y"
    main(
        session_id="-" if stateful else None,
    )
