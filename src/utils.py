import asyncio
import logging
import time
from typing import Any

import google.auth
from google.cloud import bigquery
import yaml

from discoveryengine_utils import DiscoveryEngineAgent
from model import AnswerResponse


logger = logging.getLogger(__name__)


class UtilHandler:
    """A utility handler class for the anomaly detection application."""

    def __init__(self, log_level: str = "INFO") -> None:
        """Initialize the UtilHandler class.

        Args:
            log_level (str, optional): The log level to set. Defaults to "INFO".
        """
        self._setup_logging(log_level)
        self._config = self._load_config("config.yaml")
        self._credentials, self._project = google.auth.default()
        self._bq_client = self._load_bigquery_client()
        self._table = self._compose_table()
        self._search_agent = DiscoveryEngineAgent(
            location=self._config["location"],
            engine_id=self._config["search_engine_id"],
            project_id=self._project,
        )

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
            encoding="utf-8",
        )
        logger.info(f"Logging level set to: {log_level}")

        return

    def _load_config(self, filepath: str) -> dict[str, Any]:
        """Load the configuration file and ensure required keys are set.

        Args:
            filepath (str): The path to the configuration file.

        Returns:
            dict[str, Any]: The configuration settings.
        """
        with open(filepath, "r") as file:
            config: dict = yaml.safe_load(file)
        logger.debug(f"Loaded configuration: {config}")

        return config

    def _load_bigquery_client(self) -> bigquery.Client:
        """Load the BigQuery client.

        Returns:
            bigquery.Client: The BigQuery client.
        """
        client = bigquery.Client(
            credentials=self._credentials,
            project=self._project,
        )
        logger.debug(f"BigQuery Client project: {client.project}")

        return client

    def _compose_table(self) -> str:
        """Compose the BigQuery table name.

        Returns:
            str: The BigQuery table name.
        """
        table = (
            f"{self._project}.{self._config['dataset_id']}.{self._config['table_id']}"
        )
        logger.debug(f"Table: {table}")

        return table

    async def answer_query(
        self,
        query_text: str,
        session_id: str | None,
    ) -> dict[str, Any]:
        """Call the answer method and return a generated answer and a list of search results,
        with links to the sources.

        Args:
            query_text (str): The text of the query to be answered.
            session_id (str, optional): The session ID to continue a conversation.

        Returns:
            dict (str, Any): The response from the Conversational Search Service,
            containing the generated answer and selected references.
        """
        logger.debug(f"Query: {query_text}")
        logger.debug(f"Session ID: {session_id}")

        # Start the timer.
        start_time = time.time()

        # Get the answer to the query.
        response = await asyncio.to_thread(
            self._search_agent.answer_query,
            query_text=query_text,
            session_id=session_id,
        )

        # Log the latency in the model response and add it to the response data.
        latency = time.time() - start_time
        response["latency"] = latency
        logger.info(f"Search agent latency: {latency:.4f} seconds.")

        return response

    async def bq_insert_row_data(
        self,
        data: dict[str, Any],
    ) -> list[dict[str, Any]] | None:
        """Insert rows into a BigQuery table.

        Args:
            data (dict[str, Any]): The row data to insert.

        Returns:
            list[dict] | None: A list of errors, if any occurred.

        """
        # Start the timer.
        start_time = time.time()

        # Define the BigQuery table.
        table = (
            f"{self._project}.{self._config['dataset_id']}.{self._config['table_id']}"
        )
        logger.debug(f"Table: {table}")

        # Insert the rows into the BigQuery table.
        errors = await asyncio.to_thread(
            self._bq_client.insert_rows_json,
            table=table,
            json_rows=[data],
        )

        # Log the insert time.
        logger.info(f"Insert row latency: {time.time() - start_time:.4f} seconds.")

        return errors
