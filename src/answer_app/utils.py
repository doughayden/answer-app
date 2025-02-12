import asyncio
import base64
import logging
import os
import time
from typing import Any

import google.auth
from google.cloud import bigquery
from google.cloud.discoveryengine_v1.types import Answer, AnswerQueryResponse
import yaml

from answer_app.discoveryengine_utils import DiscoveryEngineAgent
from answer_app.model import AnswerResponse, ClientCitation


logger = logging.getLogger(__name__)


def sanitize(text: str) -> str:
    """Sanitize log entry text by removing newline characters.
    Satisfies GitHub CodeQL security scan.

    Args:
        text (str): The text to sanitize.

    Returns:
        str: The sanitized text.
    """
    return text.replace("\r\n", "").replace("\n", "")


def _answer_to_markdown(answer: Answer) -> str:
    """Convert the Answer object to a base64-encoded markdown-formatted string of
    the answer text and citations.

    Args:
        answer (google.cloud.discoveryengine_v1.types.Answer): The Answer object.

    Returns:
        str: The markdown-formatted answer text with citations encoded using base64.

    Ref: https://github.com/aurelio-labs/cookbook/blob/main/gen-ai/google-ai/gemini-2/web-search.ipynb
    """
    # Start the timer.
    start_time = time.time()

    # Create a list of ClientCitation objects from the response citations and references.
    client_citations: list[ClientCitation] = [
        ClientCitation(
            # fmt: off
            start_index=citation.start_index,
            end_index=citation.end_index,
            ref_index=int(source.reference_id),
            content=answer.references[int(source.reference_id)].chunk_info.content,
            score=answer.references[int(source.reference_id)].chunk_info.relevance_score,
            title=answer.references[int(source.reference_id)].chunk_info.document_metadata.title,
            uri=answer.references[int(source.reference_id)].chunk_info.document_metadata.uri,
            # fmt: on
        )
        for citation in answer.citations
        for source in citation.sources
    ]

    # Sort the client_citations by start index.
    client_citations.sort(key=lambda citation: citation.start_index)

    # Initialize the output.
    markdown: str = answer.answer_text
    offset = 0
    footer: str = "\n\n**Citations:**\n\n"
    collected_uris: dict[str, int] = {}
    citation_index = 0

    for citation in client_citations:
        logger.debug(f"Citation: {citation}")

        # Increment the index and append to the footer if the uri is not in the set.
        if citation.uri not in collected_uris.keys():
            citation_index += 1
            collected_uris[citation.uri] = citation_index
            footer += f"[{citation_index}] [{citation.title}]({citation.get_footer_link()})\n\n"

        citation.update_citation_index(collected_uris[citation.uri])
        logger.debug(f"Citation index: {citation.citation_index}")
        logger.debug(f"Footer: {footer}")

        # Insert citation numbers and links into the answer text.
        markdown = (
            markdown[: citation.end_index + offset]
            + citation.get_inline_link()
            + markdown[citation.end_index + offset :]
        )

        # Increase the offset by the number of characters added to the answer text.
        offset += citation.count_chars()

    # Append the footer and log the full annotated markdown answer text.
    markdown += footer
    logger.debug(f"Markdown: {markdown}")

    # Base64 encode the markdown string to ensure fidelity when sending over HTTP.
    encoded_markdown = base64.b64encode(markdown.encode("utf-8")).decode("utf-8")

    # Log the markdown conversion time.
    logger.debug(f"Markdown conversion time: {time.time() - start_time:.4f} seconds.")

    return encoded_markdown


class UtilHandler:
    """A utility handler class."""

    def __init__(self, log_level: str = "INFO") -> None:
        """Initialize the UtilHandler class.

        Args:
            log_level (str, optional): The log level to set. Defaults to "INFO".
        """
        self._setup_logging(log_level)
        self._config = self._load_config("config.yaml")
        self._credentials, self._project = google.auth.default()
        self._bq_client = self._load_bigquery_client()
        self._table = self._compose_table(
            dataset_key="dataset_id", table_key="table_id"
        )
        self._feedback_table = self._compose_table(
            dataset_key="dataset_id", table_key="feedback_table_id"
        )
        self._search_agent = DiscoveryEngineAgent(
            location=self._config["location"],
            engine_id=self._config["search_engine_id"],
            preamble=self._config.get("preamble", "Give a detailed answer."),
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
            filepath (str): The relative path to the configuration file.

        Returns:
            dict[str, Any]: The configuration settings.
        """
        this_directory = os.path.dirname(os.path.abspath(__file__))
        abs_filepath = os.path.join(this_directory, filepath)
        with open(abs_filepath, "r") as file:
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

    def _compose_table(
        self,
        dataset_key: str,
        table_key: str,
    ) -> str:
        """Compose the BigQuery table name.

        Args:
            dataset_id (str): The config key for the dataset ID.
            table_id (str): The config key for the table ID.

        Returns:
            str: The BigQuery table name.
        """
        table = f"{self._project}.{self._config[dataset_key]}.{self._config[table_key]}"
        logger.debug(f"Table: {table}")

        return table

    async def answer_query(
        self,
        query_text: str,
        session_id: str | None,
    ) -> AnswerResponse:
        """Call the answer method to return a generated answer and a list of search results,
        with links to the sources.

        Args:
            query_text (str): The text of the query to be answered.
            session_id (str, optional): The session ID to continue a conversation.

        Returns:
            AnswerResponse: The response from the Conversational Search Service,
            containing the generated answer, citations, references, and a markdown-formatted
            answer sting to display to the client.
        """
        logger.debug(f"Query: {query_text}")
        logger.debug(f"Session ID: {session_id}")

        # Start the timer.
        start_time = time.time()

        # Get the answer to the query.
        response = await self._search_agent.answer_query(
            query_text=query_text,
            session_id=session_id,
        )

        # Log the latency in the model response.
        latency = time.time() - start_time
        logger.info(f"Search agent latency: {latency:.4f} seconds.")

        # Create a markdown string of the answer text and citations and a dictionary of the full response.
        markdown = _answer_to_markdown(response.answer)
        response_dict = AnswerQueryResponse.to_dict(
            instance=response,
            use_integers_for_enums=False,
        )

        return AnswerResponse(
            question=query_text,
            markdown=markdown,
            latency=latency,
            **response_dict,
        )

    async def bq_insert_row_data(
        self,
        data: dict[str, Any],
        feedback: bool = False,
    ) -> list[dict[str, Any]] | None:
        """Insert rows into a BigQuery table.

        Args:
            data (dict[str, Any]): The row data to insert.
            feedback (bool, optional): Whether to insert into the feedback table.

        Returns:
            list[dict] | None: A list of errors, if any occurred.

        """
        # Start the timer.
        start_time = time.time()

        # Choose the table to insert the data.
        table = self._feedback_table if feedback else self._table

        # Insert the rows into the BigQuery table.
        errors = await asyncio.to_thread(
            self._bq_client.insert_rows_json,
            table=table,
            json_rows=[data],
        )

        # Log the insert time.
        logger.info(f"Insert row latency: {time.time() - start_time:.4f} seconds.")

        return errors
