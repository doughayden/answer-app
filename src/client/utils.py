import logging
import os
from typing import Any

from dotenv import load_dotenv
import google.auth
from google.auth import impersonated_credentials
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import httpx

logger = logging.getLogger(__name__)


class UtilHandler:
    """A utility handler class.
    This class handles the OAuth 2.0 flow for Google Cloud services and
    manages the ID token for authentication. It also sets up logging.

        Attributes:
            _log_level (str): The log level to set. Defaults to "INFO".
            default_creds (google.auth.credentials.Credentials): The default
                application credentials.
            project (str): The Google Cloud project ID.
            audience (str): The audience for the ID token.
            target_principal (str): The service account email address used for
                impersonation.
            id_token (str): The ID token used for authentication.
    """

    def __init__(self, log_level: str = "INFO") -> None:
        """Initialize the UtilHandler class instance.
        Sets up logging and loads the .env file if it exists.

        Args:
            log_level (str, optional): The log level to set. Defaults to "INFO".
        """
        # Configure logging.
        self._log_level: str = log_level
        self._setup_logging()

        # Load environment variables from .env file if it exists.
        if load_dotenv():
            logger.debug("Local .env file loaded.")
        else:
            logger.debug("No local .env file found.")

        # Get ADC
        self.default_creds, self.project = google.auth.default()

        # Initialize instance properties.
        self._audience: str | None = None
        self._target_principal: str | None = None
        self._id_token: str | None = None

        return

    @property
    def audience(self) -> str:
        """Get the audience for the ID token.

        Returns:
            str: The audience for the ID token. Defaults to "http://localhost:8888".
        """
        if self._audience is None:
            self._audience = os.getenv("AUDIENCE", "http://localhost:8888")

        logger.debug(f"audience: {self._audience}")

        return self._audience

    @property
    def target_principal(self) -> str:
        """Get the target principal for the ID token.
        This is the service account email address that will be used to
        authenticate the request to the Cloud Run service.

        Returns:
            str: The target principal for the ID token.
        """
        if self._target_principal is None:
            try:
                self._target_principal = os.environ["TF_VAR_terraform_service_account"]
            except KeyError:
                message = (
                    "TF_VAR_terraform_service_account environment variable "
                    "required for impersonation is not set."
                )
                logger.error(message)
                raise KeyError(message)

        logger.debug(f"target_principal: {self._target_principal}")

        return self._target_principal

    @property
    def id_token(self) -> str:
        """Get the default ID token.

        Returns:
            str: The default ID token.
        """
        if self._id_token is None:
            request = Request()
            try:
                logger.debug("Fetching ID token using default credentials...")
                self._id_token = id_token.fetch_id_token(
                    request=request,
                    audience=self.audience,
                )
                logger.debug(f"ID token retrieved using ADC.")

            except DefaultCredentialsError as e:
                logger.debug(f"Switching to service account impersonation: {e}")

                # Create impersonated credentials.
                target_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
                target_creds = impersonated_credentials.Credentials(
                    source_credentials=self.default_creds,
                    target_principal=self.target_principal,
                    target_scopes=target_scopes,
                )

                # Use impersonated creds to fetch and refresh an access token.
                id_creds = impersonated_credentials.IDTokenCredentials(
                    target_credentials=target_creds,
                    target_audience=self._audience,
                    include_email=True,
                )
                id_creds.refresh(request=request)
                self._id_token = id_creds.token
                logger.debug(f"ID token retrieved using impersonated credentials.")

        logger.debug(f"id_token: {self._id_token}")

        return self._id_token

    def _setup_logging(self) -> None:
        """Set up logging with the specified log level.

        Args:
            log_level (str, optional): The log level to set. Defaults to "INFO".
        """
        log_format = (
            "{levelname:<9} {asctime} [{name}.{funcName}:{lineno:>5}] {message}"
        )
        date_format = "%Y-%m-%d %H:%M:%S %Z"

        # Use the stream handler in Cloud Run, otherwise use the file handler.
        if os.getenv("K_REVISION"):
            stream_handler = logging.StreamHandler()
            handlers = [stream_handler]

        else:
            # Construct the log filename using the script directory.
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(script_dir, ".log")
            log_filename = os.path.join(log_dir, "client.log")

            # Ensure the log directory exists.
            os.makedirs(log_dir, exist_ok=True)

            # Create a file handler.
            file_handler = logging.FileHandler(
                filename=log_filename,
                mode="w",
                encoding="utf-8",
            )
            handlers = [file_handler]

        # Configure the root logger.
        logging.basicConfig(
            format=log_format,
            datefmt=date_format,
            style="{",
            level=getattr(logging, self._log_level, logging.INFO),
            handlers=handlers,
            encoding="utf-8",
        )
        logger.info(f"Logging level set to: {self._log_level}")

        return

    async def send_request(
        self,
        route: str,
        data: dict[str, Any] | None = None,
        method: str = "POST",
    ) -> dict[str, Any]:
        """Send a request to the answer-app Cloud Run backend service.

        Args:
            route (str): The API route to receive the request.
            data (dict, optional): The data to send in the request. Passed as the body
                for POST and as query parameters for GET requests. Defaults to None.
            method (str, optional): The HTTP method to use. Defaults to "POST".

        Returns:
            dict: The response from the Discovery Engine API.
        """
        # Construct and send the request.
        url = f"{self.audience}{route}"
        logger.info(f"URL: {url}")
        headers = {
            "Authorization": f"Bearer {self.id_token}",
            "Content-Type": "application/json",
        }
        logger.debug(f"Headers: {headers}")
        logger.info(f"Request data: {data}")

        async with httpx.AsyncClient() as client:
            match method:
                case "POST":
                    response = await client.post(url, headers=headers, json=data)
                case "GET":
                    response = await client.get(url, headers=headers, params=data)
                case _:
                    message = f"Unsupported method: {method}"
                    logger.error(message)
                    return {"error": message}

        logger.info(f"Response status code: {response.status_code}")

        # Check for errors.
        if response.status_code != 200:
            logger.error(f"Error: {response.text}")
            return {"error": response.text}

        return response.json()


utils = UtilHandler(log_level=os.getenv("LOG_LEVEL", "INFO").upper())
