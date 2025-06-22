from unittest.mock import MagicMock, AsyncMock

from google.cloud.discoveryengine_v1 import Answer
from google.cloud.discoveryengine_v1 import AnswerQueryRequest
from google.cloud.discoveryengine_v1 import AnswerQueryResponse
from google.cloud.discoveryengine_v1 import Query
from google.cloud.discoveryengine_v1 import Session
import pytest

from answer_app.discoveryengine_utils import DiscoveryEngineHandler


def test_initialization_with_project_id(
    mock_discoveryengine_utils_google_auth_default: MagicMock,
) -> None:
    handler = DiscoveryEngineHandler(
        location="test-location",
        engine_id="test-engine-id",
        preamble="test-preamble",
        project_id="custom-project-id",
    )

    assert handler._location == "test-location"
    assert handler._engine_id == "test-engine-id"
    assert handler._preamble == "test-preamble"
    assert handler._project_id == "custom-project-id"


def test_initialization_without_project_id(
    mock_discoveryengine_handler: DiscoveryEngineHandler,
) -> None:
    handler = mock_discoveryengine_handler

    assert handler._location == "test-location"
    assert handler._engine_id == "test-engine-id"
    assert handler._preamble == "test-preamble"
    assert handler._project_id == "test-project-id"


def test_engine_path(mock_discoveryengine_handler: DiscoveryEngineHandler) -> None:
    handler = mock_discoveryengine_handler

    expected_path = (
        "projects/test-project-id/locations/test-location/"
        "collections/default_collection/engines/test-engine-id"
    )

    assert handler._engine == expected_path


def test_log_attributes(
    mock_discoveryengine_handler: DiscoveryEngineHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    handler = mock_discoveryengine_handler

    expected_path = (
        "projects/test-project-id/locations/test-location/"
        "collections/default_collection/engines/test-engine-id"
    )

    with caplog.at_level("DEBUG"):
        handler._log_attributes()

    assert "VAIS Handler project: test-project-id" in caplog.text
    assert "VAIS Handler location: test-location" in caplog.text
    assert "VAIS Handler engine ID: test-engine-id" in caplog.text
    assert f"VAIS Handler engine: {expected_path}" in caplog.text
    assert "VAIS Handler preamble: test-preamble" in caplog.text


@pytest.mark.asyncio
async def test_answer_query(
    mock_discoveryengine_handler: DiscoveryEngineHandler,
) -> None:
    handler = mock_discoveryengine_handler
    handler._client.answer_query = AsyncMock(return_value=AnswerQueryResponse())

    response = await handler.answer_query(
        query_text="What is the capital of France?",
        session_id=None,
        user_pseudo_id="test-user",
    )
    assert isinstance(response, AnswerQueryResponse)
    assert isinstance(response.answer, Answer)
    assert isinstance(response.session, Session)
    assert isinstance(response.answer_query_token, str)
    handler._client.answer_query.assert_called_once()
    args, kwargs = handler._client.answer_query.call_args
    assert isinstance(args[0], AnswerQueryRequest)
    assert isinstance(args[0].query, Query)
    assert args[0].query.text == "What is the capital of France?"
    assert args[0].user_pseudo_id == "test-user"


@pytest.mark.asyncio
async def test_get_user_sessions(
    mock_discoveryengine_handler: DiscoveryEngineHandler,
) -> None:
    handler = mock_discoveryengine_handler
    handler._client.list_sessions = AsyncMock(
        return_value=AsyncMock(
            __aiter__=lambda self: self,
            __anext__=AsyncMock(
                side_effect=[
                    Session(name="session1"),
                    Session(name="session2"),
                    StopAsyncIteration,
                ]
            ),
        )
    )

    response = await handler.get_user_sessions(user_pseudo_id="test-user")

    assert len(response) == 2
    assert isinstance(response[0], Session)
    assert isinstance(response[1], Session)
    assert response[0].name == "session1"
    assert response[1].name == "session2"
    handler._client.list_sessions.assert_called_once()


@pytest.mark.asyncio
async def test_delete_session(
    mock_discoveryengine_handler: DiscoveryEngineHandler,
) -> None:
    handler = mock_discoveryengine_handler
    handler._client.delete_session = AsyncMock()

    await handler.delete_session(session_id="test-session-id")

    handler._client.delete_session.assert_called_once()


@pytest.mark.asyncio
async def test_delete_session_error(
    mock_discoveryengine_handler: DiscoveryEngineHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    handler = mock_discoveryengine_handler
    handler._client.delete_session = AsyncMock(side_effect=Exception("Test error"))

    await handler.delete_session(session_id="test-session-id")
    handler._client.delete_session.assert_called_once()
    assert "Error deleting session test-session-id: Test error" in caplog.text
    assert "Session test-session-id deleted." not in caplog.text
