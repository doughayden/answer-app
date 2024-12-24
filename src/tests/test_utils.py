import pytest
from unittest.mock import patch, MagicMock
from utils import UtilHandler
from google.cloud.discoveryengine_v1 import AnswerQueryResponse
from google.auth.credentials import Credentials
from model import AnswerResponse
from typing import Generator


@pytest.fixture
def mock_google_auth_default() -> Generator[MagicMock, None, None]:
    with patch("utils.google.auth.default") as mock_default:
        mock_credentials = MagicMock(spec=Credentials)
        mock_default.return_value = (mock_credentials, "test-project-id")
        yield mock_default


@pytest.fixture
def mock_bigquery_client() -> Generator[MagicMock, None, None]:
    with patch("utils.bigquery.Client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_discoveryengine_agent() -> Generator[MagicMock, None, None]:
    with patch("utils.DiscoveryEngineAgent") as mock_agent:
        yield mock_agent


@pytest.fixture
def mock_load_config() -> Generator[MagicMock, None, None]:
    with patch("utils.UtilHandler._load_config") as mock_load_config:
        mock_load_config.return_value = {
            "location": "us-central1",
            "search_engine_id": "test-engine-id",
            "dataset_id": "test-dataset",
            "table_id": "test-table",
        }
        yield mock_load_config


def test_initialization(
    mock_google_auth_default: MagicMock,
    mock_bigquery_client: MagicMock,
    mock_discoveryengine_agent: MagicMock,
    mock_load_config: MagicMock,
) -> None:
    handler = UtilHandler(log_level="DEBUG")
    assert handler._project == "test-project-id"
    assert handler._bq_client is not None
    assert handler._search_agent is not None
    assert handler._table == "test-project-id.test-dataset.test-table"


def test_setup_logging(caplog: pytest.LogCaptureFixture) -> None:
    handler = UtilHandler(log_level="DEBUG")
    with caplog.at_level("DEBUG"):
        handler._setup_logging(log_level="DEBUG")
    assert "Logging level set to: DEBUG" in caplog.text


def test_compose_table(
    mock_google_auth_default: MagicMock, mock_load_config: MagicMock
) -> None:
    handler = UtilHandler(log_level="DEBUG")
    table = handler._compose_table()
    assert table == "test-project-id.test-dataset.test-table"


@pytest.mark.asyncio
async def test_answer_query_no_session_id(
    mock_google_auth_default: MagicMock,
    mock_discoveryengine_agent: MagicMock,
    mock_load_config: MagicMock,
) -> None:
    mock_agent_instance = mock_discoveryengine_agent.return_value
    mock_agent_instance.answer_query.return_value = {
        "answer": {"answer_text": "Paris"},
        "session": {"name": "session1"},
        "answer_query_token": "token1",
        "latency": 0.1234,
        "question": "What is the capital of France?",
    }

    handler = UtilHandler(log_level="DEBUG")
    response = await handler.answer_query(
        query_text="What is the capital of France?",
        session_id=None,
    )
    assert isinstance(response, dict)
    assert "answer" in response
    assert "session" in response
    assert "latency" in response
    assert response["answer"]["answer_text"] == "Paris"
    assert response["question"] == "What is the capital of France?"
    mock_agent_instance.answer_query.assert_called_once_with(
        query_text="What is the capital of France?",
        session_id=None,
    )


@pytest.mark.asyncio
async def test_answer_query_with_session_id(
    mock_google_auth_default: MagicMock,
    mock_discoveryengine_agent: MagicMock,
    mock_load_config: MagicMock,
) -> None:
    mock_agent_instance = mock_discoveryengine_agent.return_value
    mock_agent_instance.answer_query.return_value = {
        "answer": {"answer_text": "Paris"},
        "session": {"name": "test-session"},
        "answer_query_token": "token1",
        "latency": 0.1234,
        "question": "What is the capital of France?",
    }

    handler = UtilHandler(log_level="DEBUG")
    response = await handler.answer_query(
        query_text="What is the capital of France?",
        session_id="test-session",
    )
    assert isinstance(response, dict)
    assert "answer" in response
    assert "session" in response
    assert "latency" in response
    assert response["answer"]["answer_text"] == "Paris"
    assert response["question"] == "What is the capital of France?"
    mock_agent_instance.answer_query.assert_called_once_with(
        query_text="What is the capital of France?",
        session_id="test-session",
    )


@pytest.mark.asyncio
async def test_bq_insert_row_data(
    mock_google_auth_default: MagicMock,
    mock_bigquery_client: MagicMock,
    mock_load_config: MagicMock,
) -> None:
    mock_client_instance = mock_bigquery_client.return_value
    mock_client_instance.insert_rows_json.return_value = []

    handler = UtilHandler(log_level="DEBUG")
    data = {"key": "value"}
    errors = await handler.bq_insert_row_data(data=data)
    assert errors == []
    mock_client_instance.insert_rows_json.assert_called_once_with(
        table="test-project-id.test-dataset.test-table", json_rows=[data]
    )
