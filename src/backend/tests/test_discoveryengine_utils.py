import pytest
from typing import Generator
from unittest.mock import patch, MagicMock, AsyncMock

from google.cloud.discoveryengine_v1 import (
    Answer,
    AnswerQueryResponse,
    AnswerQueryRequest,
    Session,
    Query,
)

from discoveryengine_utils import DiscoveryEngineAgent


@pytest.fixture
def mock_default() -> Generator[MagicMock, None, None]:
    with patch("discoveryengine_utils.default") as mock_default:
        mock_default.return_value = (MagicMock(), "test-project-id")
        yield mock_default


@pytest.fixture
def mock_discoveryengine_client() -> Generator[MagicMock, None, None]:
    with patch(
        "discoveryengine_utils.discoveryengine.ConversationalSearchServiceAsyncClient"
    ) as mock_client:
        yield mock_client


def test_initialization_with_project_id(mock_default: MagicMock) -> None:
    agent = DiscoveryEngineAgent(
        location="us-central1",
        engine_id="test-engine-id",
        project_id="custom-project-id",
    )
    assert agent._location == "us-central1"
    assert agent._engine_id == "test-engine-id"
    assert agent._project_id == "custom-project-id"


def test_initialization_without_project_id(mock_default: MagicMock) -> None:
    agent = DiscoveryEngineAgent(location="us-central1", engine_id="test-engine-id")
    assert agent._location == "us-central1"
    assert agent._engine_id == "test-engine-id"
    assert agent._project_id == "test-project-id"


def test_log_attributes(
    mock_default: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    agent = DiscoveryEngineAgent(location="us-central1", engine_id="test-engine-id")
    with caplog.at_level("DEBUG"):
        agent._log_attributes()
    assert "Search Agent project: test-project-id" in caplog.text
    assert "Search Agent location: us-central1" in caplog.text
    assert "Search Agent engine ID: test-engine-id" in caplog.text


@pytest.mark.asyncio
async def test_answer_query(
    mock_default: MagicMock, mock_discoveryengine_client: MagicMock
) -> None:
    mock_client_instance = mock_discoveryengine_client.return_value
    mock_client_instance.answer_query = AsyncMock(return_value=AnswerQueryResponse())

    agent = DiscoveryEngineAgent(location="us-central1", engine_id="test-engine-id")

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
