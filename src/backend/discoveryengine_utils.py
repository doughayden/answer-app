"""Ref: https://cloud.google.com/generative-ai-app-builder/docs/answer"""

import logging

from google.api_core.client_options import ClientOptions
from google.auth import default
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud.discoveryengine_v1.types import AnswerQueryResponse
from google.protobuf.json_format import MessageToJson


logger = logging.getLogger(__name__)


class DiscoveryEngineAgent:
    """A class to interact with the Conversational Search Service."""

    def __init__(
        self,
        location: str,
        engine_id: str,
        project_id: str | None = None,
    ) -> None:
        """Initialize the DiscoveryEngineAgent class.

        Args:
            location (str): The location of the search engine.
            engine_id (str): The ID of the search engine.
            project_id (str, optional): The ID of the Google Cloud project. Defaults to None.
        """
        self._location = location
        self._engine_id = engine_id
        self._project_id = project_id if project_id else default()[1]
        self._client = self._initialize_client()
        self._log_attributes()

        return

    def _log_attributes(self) -> None:
        """Log the attributes of the class."""
        logger.debug(f"Search Agent project: {self._project_id}")
        logger.debug(f"Search Agent location: {self._location}")
        logger.debug(f"Search Agent engine ID: {self._engine_id}")
        logger.debug(f"Search Agent client: {self._client.transport.host}")

        return

    def _initialize_client(self) -> discoveryengine.ConversationalSearchServiceClient:
        """Initialize the Conversational Search Service client.

        Returns:
            discoveryengine.ConversationalSearchServiceClient:
            The client for the Conversational Search Service.
        """
        #  For more information, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
        client_options = (
            ClientOptions(
                api_endpoint=f"{self._location}-discoveryengine.googleapis.com"
            )
            if self._location != "global"
            else None
        )

        # Create a client
        return discoveryengine.ConversationalSearchServiceClient(
            client_options=client_options
        )

    def answer_query(
        self,
        query_text: str,
        session_id: str | None,
    ) -> AnswerQueryResponse:
        """Call the answer method and return a generated answer and a list of search results,
        with links to the sources.

        Args:
            query_text (str): The text of the query to be answered.
            session_id (str, optional): The session ID to continue a conversation.

        Returns:
            AnswerQueryResponse: The response from the Conversational Search Service,
            containing the generated answer and selected references.

        Ref: https://cloud.google.com/generative-ai-app-builder/docs/answer#search-answer-basic
        """
        # The full resource name of the Search engine.
        engine = f"projects/{self._project_id}/locations/{self._location}/collections/default_collection/engines/{self._engine_id}"

        # The full resource name of the Search serving config.
        serving_config = f"{engine}/servingConfigs/default_serving_config"

        # Optional: Options for query phase
        query_understanding_spec = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec(
            query_rephraser_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(
                disable=False,  # Optional: Disable query rephraser
                max_rephrase_steps=1,  # Optional: Number of rephrase steps
            ),
            # Optional: Classify query types
            query_classification_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec(
                types=[
                    discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.ADVERSARIAL_QUERY,
                    discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.NON_ANSWER_SEEKING_QUERY,
                ]  # Options: ADVERSARIAL_QUERY, NON_ANSWER_SEEKING_QUERY or both
            ),
        )

        # Optional: Options for answer phase
        answer_generation_spec = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(
            ignore_adversarial_query=False,  # Optional: Ignore adversarial query
            ignore_non_answer_seeking_query=False,  # Optional: Ignore non-answer seeking query
            ignore_low_relevant_content=False,  # Optional: Return fallback answer when content is not relevant
            model_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.ModelSpec(
                model_version="gemini-1.5-flash-001/answer_gen/v2",  # Optional: Model to use for answer generation
            ),
            prompt_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.PromptSpec(
                preamble="Give a detailed answer.",  # Optional: Natural language instructions for customizing the answer.
            ),
            include_citations=True,  # Optional: Include citations in the response
            answer_language_code="en",  # Optional: Language code of the answer
        )

        # Construct the session name using the engine as the serving config.
        # Ref: https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.AnswerQueryRequest
        session = f"{engine}/sessions/{session_id}" if session_id else None

        # Initialize request argument(s).
        request = discoveryengine.AnswerQueryRequest(
            serving_config=serving_config,
            query=discoveryengine.Query(text=query_text),
            session=session,  # Optional: include previous session ID to continue a conversation
            query_understanding_spec=query_understanding_spec,
            answer_generation_spec=answer_generation_spec,
        )

        # Make the request.
        response = self._client.answer_query(request)

        # Handle the response.
        logger.debug(response)
        logger.info(f"Answer: {response.answer.answer_text}")

        return response
