import logging
import os
import requests

import google.auth
import google.auth.transport.requests
from google.auth import impersonated_credentials


logger = logging.getLogger(__name__)


class UtilHandler:
    """A utility handler class."""

    def __init__(self, log_level: str = "INFO") -> None:
        """Initialize the UtilHandler class.

        Args:
            log_level (str, optional): The log level to set. Defaults to "INFO".
        """
        self._setup_logging(log_level)
        # Get ADC for the caller (a Google user account).
        self._credentials, self._project = google.auth.default()
        self._audience = os.getenv("AUDIENCE", "http://localhost:8888")
        self._target_principal = os.getenv("TF_VAR_terraform_service_account", None)
        self._target_scopes = None
        self._token = None

        if self._target_principal:
            self._target_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
            self._token = self._get_impersonated_id_token()

        self._log_attributes()

        return

    def _setup_logging(self, log_level: str = "INFO") -> None:
        """Set up logging with the specified log level.

        Args:
            log_level (str, optional): The log level to set. Defaults to "INFO".
        """
        log_format = "{levelname:<9} [{name}.{funcName}:{lineno:>5}] {message}"
        logging.basicConfig(
            format=log_format,
            style="{",
            level=getattr(logging, log_level, logging.INFO),
            handlers=[
                logging.FileHandler(
                    filename=".log/client.log", mode="w", encoding="utf-8"
                )
            ],
            encoding="utf-8",
        )
        logger.info(f"Logging level set to: {log_level}")

        return

    def _get_impersonated_id_token(self) -> str:
        """Use Service Account Impersonation to generate a token for authorized requests.
        Caller must have the “Service Account Token Creator” role on the target service account.
        # Args:
        #     target_principal: The Service Account email address to impersonate.
        #     target_scopes: List of auth scopes for the Service Account.
        #     audience: the URI of the Google Cloud resource to access with impersonation.
        Returns: Open ID Connect ID Token-based service account credentials bearer token
        that can be used in HTTP headers to make authenticated requests.
        refs:
        https://cloud.google.com/docs/authentication/get-id-token#impersonation
        https://cloud.google.com/iam/docs/create-short-lived-credentials-direct#user-credentials_1
        https://stackoverflow.com/questions/74411491/python-equivalent-for-gcloud-auth-print-identity-token-command
        https://googleapis.dev/python/google-auth/latest/reference/google.auth.impersonated_credentials.html
        """
        # Create impersonated credentials.
        target_creds = impersonated_credentials.Credentials(
            source_credentials=self._credentials,
            target_principal=self._target_principal,
            target_scopes=self._target_scopes,
        )

        # Use impersonated creds to fetch and refresh an access token.
        request = google.auth.transport.requests.Request()
        id_creds = impersonated_credentials.IDTokenCredentials(
            target_credentials=target_creds,
            target_audience=self._audience,
            include_email=True,
        )
        id_creds.refresh(request)

        return id_creds.token

    def _log_attributes(self) -> None:
        """Log the attributes of the class."""
        logger.debug(f"Project: {self._project}")
        logger.debug(f"AUDIENCE: {self._audience}")
        logger.debug(f"TARGET PRINCIPAL: {self._target_principal}")
        logger.debug(f"TOKEN: {self._token}")

        return

    def send_request(
        self,
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
        url = f"{self._audience}/answer"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        data = {"question": question, "session_id": session_id}
        response = requests.post(url, headers=headers, json=data)
        return response.json()
