import pytest
from unittest.mock import MagicMock, AsyncMock

from google.cloud.discoveryengine_v1 import Answer
from google.cloud.discoveryengine_v1 import AnswerQueryResponse
from google.cloud.discoveryengine_v1 import AnswerQueryRequest
from google.cloud.discoveryengine_v1 import Session
from google.cloud.discoveryengine_v1 import Query

from answer_app.discoveryengine_utils import DiscoveryEngineAgent


def test_initialization_with_project_id(mock_default: MagicMock) -> None:
    agent = DiscoveryEngineAgent(
        location="us-central1",
        engine_id="test-engine-id",
        preamble="test-preamble",
        project_id="custom-project-id",
    )
    assert agent._location == "us-central1"
    assert agent._engine_id == "test-engine-id"
    assert agent._preamble == "test-preamble"
    assert agent._project_id == "custom-project-id"


def test_initialization_without_project_id(mock_default: MagicMock) -> None:
    agent = DiscoveryEngineAgent(
        location="us-central1",
        engine_id="test-engine-id",
        preamble="test-preamble",
    )
    assert agent._location == "us-central1"
    assert agent._engine_id == "test-engine-id"
    assert agent._preamble == "test-preamble"
    assert agent._project_id == "test-project-id"


def test_log_attributes(
    mock_default: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    agent = DiscoveryEngineAgent(
        location="us-central1",
        engine_id="test-engine-id",
        preamble="test-preamble",
    )
    with caplog.at_level("DEBUG"):
        agent._log_attributes()
    assert "Search Agent project: test-project-id" in caplog.text
    assert "Search Agent location: us-central1" in caplog.text
    assert "Search Agent engine ID: test-engine-id" in caplog.text
    assert "Search Agent preamble: test-preamble" in caplog.text


@pytest.mark.asyncio
async def test_answer_query(
    mock_default: MagicMock, mock_discoveryengine_client: MagicMock
) -> None:
    mock_client_instance = mock_discoveryengine_client.return_value
    mock_client_instance.answer_query = AsyncMock(return_value=AnswerQueryResponse())

    agent = DiscoveryEngineAgent(
        location="us-central1",
        engine_id="test-engine-id",
        preamble="test-preamble",
    )

    response = await agent.answer_query(
        query_text="What is the capital of France?",
        session_id=None,
    )
    assert isinstance(response, AnswerQueryResponse)
    assert isinstance(response.answer, Answer)
    assert isinstance(response.session, Session)
    assert isinstance(response.answer_query_token, str)
    mock_client_instance.answer_query.assert_called_once()
    args, kwargs = mock_client_instance.answer_query.call_args
    assert isinstance(args[0], AnswerQueryRequest)
    assert isinstance(args[0].query, Query)
    assert args[0].query.text == "What is the capital of France?"
