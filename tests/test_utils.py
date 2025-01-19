import base64
import pytest
from typing import Generator
from unittest.mock import patch, MagicMock, AsyncMock

from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from google.cloud.discoveryengine_v1 import AnswerQueryResponse, Answer, Session
from google.auth.credentials import Credentials
import pytz

from answer_app.utils import (
    UtilHandler,
    _timestamp_to_string,
    _response_to_dict,
    _answer_to_markdown,
)
from answer_app.model import AnswerResponse


@pytest.fixture
def mock_google_auth_default() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.google.auth.default") as mock_default:
        mock_credentials = MagicMock(spec=Credentials)
        mock_default.return_value = (mock_credentials, "test-project-id")
        yield mock_default


@pytest.fixture
def mock_bigquery_client() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.bigquery.Client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_discoveryengine_agent() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.DiscoveryEngineAgent") as mock_agent:
        yield mock_agent


@pytest.fixture
def mock_load_config() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.UtilHandler._load_config") as mock_load_config:
        mock_load_config.return_value = {
            "location": "us-central1",
            "search_engine_id": "test-engine-id",
            "dataset_id": "test-dataset",
            "table_id": "test-table",
            "feedback_table_id": "test-feedback-table",
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
    assert handler._feedback_table == "test-project-id.test-dataset.test-feedback-table"


def test_setup_logging(caplog: pytest.LogCaptureFixture) -> None:
    handler = UtilHandler(log_level="DEBUG")
    with caplog.at_level("DEBUG"):
        handler._setup_logging(log_level="DEBUG")
    assert "Logging level set to: DEBUG" in caplog.text


def test_compose_table(
    mock_google_auth_default: MagicMock, mock_load_config: MagicMock
) -> None:
    handler = UtilHandler(log_level="DEBUG")
    table = handler._compose_table(dataset_key="dataset_id", table_key="table_id")
    assert table == "test-project-id.test-dataset.test-table"
    feedback_table = handler._compose_table(
        dataset_key="dataset_id", table_key="feedback_table_id"
    )
    assert feedback_table == "test-project-id.test-dataset.test-feedback-table"


def test_timestamp_to_string() -> None:
    timestamp = DatetimeWithNanoseconds(2023, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
    assert _timestamp_to_string(timestamp) == "2023-01-01T12:00:00.000000Z"
    assert _timestamp_to_string(None) is None


def test_response_to_dict() -> None:
    utc = pytz.UTC
    response = AnswerQueryResponse(
        answer=Answer(
            name="answer1",
            state=Answer.State.SUCCEEDED,
            answer_text="This is an answer",
            citations=[],
            references=[],
            related_questions=[],
            steps=[],
            query_understanding_info=Answer.QueryUnderstandingInfo(
                query_classification_info=[]
            ),
            answer_skipped_reasons=[],
            create_time=DatetimeWithNanoseconds(2023, 1, 1, 12, 0, 0, tzinfo=utc),
            complete_time=DatetimeWithNanoseconds(2023, 1, 1, 12, 0, 1, tzinfo=utc),
        ),
        session=Session(
            name="session1",
            state=Session.State.IN_PROGRESS,
            user_pseudo_id="user1",
            turns=[],
            start_time=DatetimeWithNanoseconds(2023, 1, 1, 12, 0, 0, tzinfo=utc),
            end_time=DatetimeWithNanoseconds(2023, 1, 1, 12, 0, 1, tzinfo=utc),
        ),
        answer_query_token="token1",
    )
    response_dict = _response_to_dict(response)
    assert response_dict["answer"]["name"] == "answer1"
    assert response_dict["answer"]["state"] == "SUCCEEDED"
    assert response_dict["answer"]["answer_text"] == "This is an answer"
    assert response_dict["answer"]["create_time"] == "2023-01-01T12:00:00.000000Z"
    assert response_dict["answer"]["complete_time"] == "2023-01-01T12:00:01.000000Z"
    assert response_dict["session"]["name"] == "session1"
    assert response_dict["session"]["state"] == "IN_PROGRESS"
    assert response_dict["session"]["user_pseudo_id"] == "user1"
    assert response_dict["session"]["start_time"] == "2023-01-01T12:00:00.000000Z"
    assert response_dict["session"]["end_time"] == "2023-01-01T12:00:01.000000Z"
    assert response_dict["answer_query_token"] == "token1"


def test_answer_to_markdown() -> None:
    answer = Answer(
        answer_text="This is an answer",
        citations=[
            Answer.Citation(
                start_index=0,
                end_index=17,
                sources=[Answer.CitationSource(reference_id="0")],
            )
        ],
        references=[
            Answer.Reference(
                chunk_info=Answer.Reference.ChunkInfo(
                    content="Reference content",
                    relevance_score=0.9,
                    document_metadata=Answer.Reference.ChunkInfo.DocumentMetadata(
                        title="Reference title", uri="http://example.com"
                    ),
                )
            )
        ],
    )
    markdown = _answer_to_markdown(answer)
    expected_markdown = (
        'This is an answer _[[1](http://example.com "Reference content")]_\n\n**Citations:**\n\n'
        "[1] [Reference title](http://example.com)\n\n"
    )
    encoded_expected_markdown = base64.b64encode(
        expected_markdown.encode("utf-8")
    ).decode("utf-8")
    assert markdown == encoded_expected_markdown


def test_answer_to_markdown_multiple_citations() -> None:
    answer = Answer(
        answer_text="This is an answer. It has multiple citations. Some are repeated. Some are not.",
        citations=[
            Answer.Citation(
                start_index=0,
                end_index=18,
                sources=[Answer.CitationSource(reference_id="0")],
            ),
            Answer.Citation(
                start_index=19,
                end_index=45,
                sources=[Answer.CitationSource(reference_id="0")],
            ),
            Answer.Citation(
                start_index=46,
                end_index=64,
                sources=[Answer.CitationSource(reference_id="4")],
            ),
            Answer.Citation(
                start_index=65,
                end_index=78,
                sources=[Answer.CitationSource(reference_id="1")],
            ),
        ],
        references=[
            Answer.Reference(
                chunk_info=Answer.Reference.ChunkInfo(
                    content="Reference content 0",
                    relevance_score=0.9,
                    document_metadata=Answer.Reference.ChunkInfo.DocumentMetadata(
                        title="Reference 0 title", uri="http://example.com"
                    ),
                )
            ),
            Answer.Reference(
                chunk_info=Answer.Reference.ChunkInfo(
                    content="Reference content 1",
                    relevance_score=0.9,
                    document_metadata=Answer.Reference.ChunkInfo.DocumentMetadata(
                        title="Reference 1 title", uri="http://exemplar.com"
                    ),
                )
            ),
            Answer.Reference(
                chunk_info=Answer.Reference.ChunkInfo(
                    content="Reference content 2",
                    relevance_score=0.9,
                    document_metadata=Answer.Reference.ChunkInfo.DocumentMetadata(
                        title="Reference 0 title", uri="http://example.com"
                    ),
                )
            ),
            Answer.Reference(
                chunk_info=Answer.Reference.ChunkInfo(
                    content="Reference content 3",
                    relevance_score=0.9,
                    document_metadata=Answer.Reference.ChunkInfo.DocumentMetadata(
                        title="Reference 1 title", uri="http://exemplar.com"
                    ),
                )
            ),
            Answer.Reference(
                chunk_info=Answer.Reference.ChunkInfo(
                    content="Reference content 4",
                    relevance_score=0.9,
                    document_metadata=Answer.Reference.ChunkInfo.DocumentMetadata(
                        title="Reference 2 title", uri="http://anotherexample.com"
                    ),
                )
            ),
        ],
    )
    markdown = _answer_to_markdown(answer)
    expected_markdown = (
        'This is an answer. _[[1](http://example.com "Reference content 0")]_ '
        'It has multiple citations. _[[1](http://example.com "Reference content 0")]_ '
        'Some are repeated. _[[2](http://anotherexample.com "Reference content 4")]_ '
        'Some are not. _[[3](http://exemplar.com "Reference content 1")]_'
        "\n\n**Citations:**\n\n"
        "[1] [Reference 0 title](http://example.com)\n\n"
        "[2] [Reference 2 title](http://anotherexample.com)\n\n"
        "[3] [Reference 1 title](http://exemplar.com)\n\n"
    )
    encoded_expected_markdown = base64.b64encode(
        expected_markdown.encode("utf-8")
    ).decode("utf-8")
    assert markdown == encoded_expected_markdown


@pytest.mark.asyncio
async def test_answer_query_no_session_id(
    mock_google_auth_default: MagicMock,
    mock_discoveryengine_agent: MagicMock,
    mock_load_config: MagicMock,
) -> None:
    mock_agent_instance = mock_discoveryengine_agent.return_value
    mock_agent_instance.answer_query = AsyncMock(
        return_value=AnswerQueryResponse(
            answer=Answer(answer_text="Paris"),
            session=Session(name="session1"),
            answer_query_token="token1",
        )
    )
    handler = UtilHandler(log_level="DEBUG")
    response = await handler.answer_query(
        query_text="What is the capital of France?", session_id=None
    )
    assert isinstance(response, AnswerResponse)
    assert response.answer["answer_text"] == "Paris"
    assert response.question == "What is the capital of France?"
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
    mock_agent_instance.answer_query = AsyncMock(
        return_value=AnswerQueryResponse(
            answer=Answer(answer_text="Paris"),
            session=Session(name="test-session"),
            answer_query_token="token1",
        )
    )
    handler = UtilHandler(log_level="DEBUG")
    response = await handler.answer_query(
        query_text="What is the capital of France?",
        session_id="test-session",
    )
    assert isinstance(response, AnswerResponse)
    assert response.answer["answer_text"] == "Paris"
    assert response.question == "What is the capital of France?"
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


@pytest.mark.asyncio
async def test_bq_insert_row_data_feedback(
    mock_google_auth_default: MagicMock,
    mock_bigquery_client: MagicMock,
    mock_load_config: MagicMock,
) -> None:
    mock_client_instance = mock_bigquery_client.return_value
    mock_client_instance.insert_rows_json.return_value = []

    handler = UtilHandler(log_level="DEBUG")
    data = {"key": "value"}
    errors = await handler.bq_insert_row_data(data=data, feedback=True)
    assert errors == []
    mock_client_instance.insert_rows_json.assert_called_once_with(
        table="test-project-id.test-dataset.test-feedback-table", json_rows=[data]
    )


@pytest.mark.asyncio
async def test_bq_insert_row_data_error(
    mock_google_auth_default: MagicMock,
    mock_bigquery_client: MagicMock,
    mock_load_config: MagicMock,
) -> None:
    mock_client_instance = mock_bigquery_client.return_value
    mock_client_instance.insert_rows_json.return_value = [
        {"index": 0, "errors": [{"reason": "invalid", "message": "Invalid data"}]}
    ]

    handler = UtilHandler(log_level="DEBUG")
    data = {"key": "value"}
    errors = await handler.bq_insert_row_data(data=data)
    assert errors == [
        {"index": 0, "errors": [{"reason": "invalid", "message": "Invalid data"}]}
    ]
    mock_client_instance.insert_rows_json.assert_called_once_with(
        table="test-project-id.test-dataset.test-table", json_rows=[data]
    )
