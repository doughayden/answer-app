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
from rich.console import Console
from rich.markdown import Markdown

from auth_utils import get_impersonated_id_token

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="{asctime} {levelname:<9} [{name}.{funcName}:{lineno:>5}] {message}",
    style="{",
    level=logging.DEBUG,
    handlers=[logging.FileHandler(filename="client.log", mode="w", encoding="utf-8")],
    encoding="utf-8",
)

audience = os.getenv("AUDIENCE", "http://localhost:8888")
logger.debug(f"AUDIENCE: {audience}")

target_principal = os.getenv("TF_VAR_terraform_service_account", None)
logger.debug(f"TARGET PRINCIPAL: {target_principal}")

if target_principal:
    target_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    token = get_impersonated_id_token(
        target_principal=target_principal,
        target_scopes=target_scopes,
        audience=audience,
    )
    logger.debug(f"TOKEN: {token}")

# Initialize the console for rich output.
console = Console()


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
        markdown = Markdown(response.get("markdown", "No markdown returned."))
        print(2 * "\n")
        print("ANSWER: \n\n")
        console.print(markdown)
        print(2 * "\n")
        logger.debug(f"Response: {json.dumps(response, indent=2)}")
        session_id = response.get("session", {}).get("name", "").split("/")[-1]


if __name__ == "__main__":
    stateful = input("\n\nDo you want to maintain state? (y/n): ").lower()[0] == "y"
    main(
        session_id="-" if stateful else None,
    )
