import asyncio
import base64
import logging
import time
from typing import Any

from google.api_core.datetime_helpers import DatetimeWithNanoseconds
import google.auth
from google.cloud import bigquery
from google.cloud.discoveryengine_v1.types import Answer, AnswerQueryResponse, Session
from google.protobuf.json_format import MessageToJson
import yaml

from discoveryengine_utils import DiscoveryEngineAgent
from model import AnswerResponse, ClientCitation


logger = logging.getLogger(__name__)


def _timestamp_to_string(timestamp: DatetimeWithNanoseconds | None) -> str | None:
    """Convert a protobuf Timestamp to a standard timestamp-formatted string.

    Args:
        timestamp: (DatetimeWithNanoseconds): The protobuf Timestamp object.
        Subclass of datetime.datetime with nanosecond precision from the
        google.api_core.datetime_helpers module.

    Returns:
        str: The timestamp-formatted string. If the input is None, return None.
    """
    return timestamp.rfc3339() if timestamp else None


def _response_to_dict(response: AnswerQueryResponse) -> dict[str, Any]:
    """Unpack the response object to a dictionary.

    Args:
        response (AnswerQueryResponse): The response object.

    Returns:
        dict[str, Any]: The response dictionary.
    """
    return {
        "answer": {
            "name": response.answer.name,
            "state": Answer.State(response.answer.state).name,
            "answer_text": response.answer.answer_text,
            "citations": [
                {
                    "start_index": citation.start_index,
                    "end_index": citation.end_index,
                    "sources": [
                        {
                            "reference_id": source.reference_id,
                        }
                        for source in citation.sources
                    ],
                }
                for citation in response.answer.citations
            ],
            "references": [
                {
                    "unstructured_document_info": {
                        "document": ref.unstructured_document_info.document,
                        "uri": ref.unstructured_document_info.uri,
                        "title": ref.unstructured_document_info.title,
                        "chunk_contents": [
                            {
                                "content": chunk.content,
                                "page_identifier": chunk.page_identifier,
                                "relevance_score": chunk.relevance_score,
                            }
                            for chunk in ref.unstructured_document_info.chunk_contents
                        ],
                        "struct_data": (
                            MessageToJson(ref.unstructured_document_info.struct_data)
                            if ref.unstructured_document_info.struct_data
                            else ""
                        ),
                    },
                    "chunk_info": {
                        "content": ref.chunk_info.content,
                        "relevance_score": ref.chunk_info.relevance_score,
                        "document_metadata": {
                            "document": ref.chunk_info.document_metadata.document,
                            "uri": ref.chunk_info.document_metadata.uri,
                            "title": ref.chunk_info.document_metadata.title,
                        },
                    },
                    "structured_document_info": {
                        "document": ref.structured_document_info.document,
                        "struct_data": (
                            MessageToJson(ref.structured_document_info.struct_data)
                            if ref.structured_document_info.struct_data
                            else ""
                        ),
                    },
                }
                for ref in response.answer.references
            ],
            "related_questions": [
                question for question in response.answer.related_questions
            ],
            "steps": [
                {
                    "state": Answer.Step.State(step.state).name,
                    "description": step.description,
                    "thought": step.thought,
                    "actions": [
                        {
                            "search_action": {
                                "query": action.search_action.query,
                            },
                            "observation": {
                                "search_results": [
                                    {
                                        "document": result.document,
                                        "uri": result.uri,
                                        "title": result.title,
                                        "snippet_info": [
                                            {
                                                "snippet": snippet_info.snippet,
                                                "snippet_status": snippet_info.snippet_status,
                                            }
                                            for snippet_info in result.snippet_info
                                        ],
                                        "chunk_info": [
                                            {
                                                "chunk": chunk_info.chunk,
                                                "content": chunk_info.content,
                                                "relevance_score": chunk_info.relevance_score,
                                            }
                                            for chunk_info in result.chunk_info
                                        ],
                                        "struct_data": (
                                            MessageToJson(result.struct_data)
                                            if result.struct_data
                                            else ""
                                        ),
                                    }
                                    for result in action.observation.search_results
                                ],
                            },
                        }
                        for action in step.actions
                    ],
                }
                for step in response.answer.steps
            ],
            "query_understanding_info": {
                "query_classification_info": [
                    {
                        "type": Answer.QueryUnderstandingInfo.QueryClassificationInfo.Type(
                            info.type_
                        ).name,
                        "positive": info.positive,
                    }
                    for info in response.answer.query_understanding_info.query_classification_info
                ],
            },
            "answer_skipped_reasons": [
                reason for reason in response.answer.answer_skipped_reasons
            ],
            "create_time": (_timestamp_to_string(response.answer.create_time)),
            "complete_time": (_timestamp_to_string(response.answer.complete_time)),
        },
        "session": {
            "name": response.session.name,
            "state": Session.State(response.session.state).name,
            "user_pseudo_id": response.session.user_pseudo_id,
            "turns": [
                {
                    "query": {
                        "query_id": turn.query.query_id,
                        "text": turn.query.text,
                    },
                    "answer": turn.answer,
                }
                for turn in response.session.turns
            ],
            "start_time": (_timestamp_to_string(response.session.start_time)),
            "end_time": (_timestamp_to_string(response.session.end_time)),
        },
        "answer_query_token": response.answer_query_token,
    }


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
    ) -> AnswerResponse:
        """Call the answer method and return a generated answer and a list of search results,
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
        response = await asyncio.to_thread(
            self._search_agent.answer_query,
            query_text=query_text,
            session_id=session_id,
        )

        # Log the latency in the model response.
        latency = time.time() - start_time
        logger.info(f"Search agent latency: {latency:.4f} seconds.")

        # Create a markdown string of the answer text and citations and a dictionary of the full response.
        markdown = _answer_to_markdown(response.answer)
        response_dict = _response_to_dict(response)

        return AnswerResponse(
            question=query_text,
            markdown=markdown,
            latency=latency,
            **response_dict,
        )

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
