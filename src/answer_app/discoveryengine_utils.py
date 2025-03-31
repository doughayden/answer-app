import logging

from google.api_core.client_options import ClientOptions
import google.auth
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud.discoveryengine_v1.types import AnswerQueryResponse, Session
from google.cloud.discoveryengine_v1.services.conversational_search_service.pagers import (
    ListSessionsAsyncPager,
)


logger = logging.getLogger(__name__)


class DiscoveryEngineHandler:
    """A class to interact with the Conversational Search Service."""

    def __init__(
        self,
        location: str,
        engine_id: str,
        preamble: str,
        project_id: str | None = None,
    ) -> None:
        """Initialize the DiscoveryEngineHandler class.

        Args:
            location (str): The location of the search engine.
            engine_id (str): The ID of the search engine.
            preamble (str): The preamble for the answer generation.
            project_id (str, optional): The ID of the Google Cloud project. Defaults to None.
        """
        self._location = location
        self._engine_id = engine_id
        self._preamble = preamble
        self._project_id = project_id if project_id else google.auth.default()[1]
        self._client = self._initialize_client()
        self._engine = self._engine_path()
        self._log_attributes()

        return

    def _initialize_client(
        self,
    ) -> discoveryengine.ConversationalSearchServiceAsyncClient:
        """Initialize the Conversational Search Service async client.

        Returns:
            discoveryengine.ConversationalSearchServiceAsyncClient:
            The async client for the Conversational Search Service.

        Ref: https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
        """
        client_options = (
            ClientOptions(
                api_endpoint=f"{self._location}-discoveryengine.googleapis.com"
            )
            if self._location != "global"
            else None
        )

        # Create an async client.
        return discoveryengine.ConversationalSearchServiceAsyncClient(
            client_options=client_options
        )

    def _engine_path(self) -> str:
        """Return the full resource name of the Search engine."""
        return f"projects/{self._project_id}/locations/{self._location}/collections/default_collection/engines/{self._engine_id}"

    def _log_attributes(self) -> None:
        """Log the attributes of the class instance."""
        logger.debug(f"VAIS Handler project: {self._project_id}")
        logger.debug(f"VAIS Handler location: {self._location}")
        logger.debug(f"VAIS Handler engine ID: {self._engine_id}")
        logger.debug(f"VAIS Handler client: {self._client.transport.host}")
        logger.debug(f"VAIS Handler engine: {self._engine}")
        logger.debug(f"VAIS Handler preamble: {self._preamble}")

        return

    async def answer_query(
        self,
        query_text: str,
        session_id: str | None,
        user_pseudo_id: str,
    ) -> AnswerQueryResponse:
        """Call the answer method and return a generated answer and a list of search results,
        with links to the sources.

        Args:
            query_text (str): The text of the query to be answered.
            session_id (str, optional): The session ID to continue a conversation.
            user_pseudo_id (str): The unique ID of the active user.

        Returns:
            AnswerQueryResponse: The response from the Conversational Search Service,
            containing the generated answer and selected references.

        Ref: https://cloud.google.com/generative-ai-app-builder/docs/answer
        """
        # The full resource name of the Search serving config.
        serving_config = f"{self._engine}/servingConfigs/default_serving_config"

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
                preamble=self._preamble,  # Optional: Natural language instructions for customizing the answer
            ),
            include_citations=True,  # Optional: Include citations in the response
            answer_language_code="en",  # Optional: Language code of the answer
        )

        # Construct the session name using the engine as the serving config.
        # Ref: https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.AnswerQueryRequest
        session = f"{self._engine}/sessions/{session_id}" if session_id else None

        # Initialize request argument(s).
        request = discoveryengine.AnswerQueryRequest(
            serving_config=serving_config,
            query=discoveryengine.Query(text=query_text),
            session=session,  # Optional: include previous session ID to continue a conversation
            query_understanding_spec=query_understanding_spec,
            answer_generation_spec=answer_generation_spec,
            user_pseudo_id=user_pseudo_id,  # Optional: User pseudo ID
        )

        # Make the request.
        response = await self._client.answer_query(request)

        # Handle the response.
        logger.debug(response)
        logger.info(f"Answer: {response.answer.answer_text}")

        return response

    async def get_user_sessions(
        self,
        user_pseudo_id: str,
    ) -> list[Session]:
        """Get a list of user sessions.

        Args:
            user_pseudo_id (str): The unique ID of the active user.

        Returns:
            list[Session]: A list of Session objects for the user.

        Ref: https://googleapis.dev/python/google-api-core/latest/page_iterator.html
        """
        logger.info(f"Getting sessions for user {user_pseudo_id}...")

        sessions: list[Session] = []
        page_result: ListSessionsAsyncPager

        page_result = await self._client.list_sessions(
            request=discoveryengine.ListSessionsRequest(
                parent=self._engine,
                filter=f'user_pseudo_id = {user_pseudo_id} AND state = "IN_PROGRESS"',  # Optional: Filter requests by userPseudoId or state
                order_by="update_time",  # Optional: Sort results
            )
        )

        async for session in page_result:
            sessions.append(session)
            logger.debug(f"Session ID: {session.name.split('/')[-1]}")
            logger.debug(f"Session State: {session.state}")
            logger.debug(f"Session user_pseudo_id: {session.user_pseudo_id}")

        logger.info(f"Number of sessions: {len(sessions)}")

        return sessions

    async def delete_session(
        self,
        session_id: str,
    ) -> None:
        """Delete a user session."""
        try:
            await self._client.delete_session(
                request=discoveryengine.DeleteSessionRequest(
                    name=f"{self._engine}/sessions/{session_id}"
                )
            )
            logger.info(f"Session {session_id} deleted.")

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")

        return
