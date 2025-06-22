import base64
from unittest.mock import MagicMock, AsyncMock

from google.cloud.discoveryengine_v1 import Answer
from google.cloud.discoveryengine_v1 import AnswerQueryResponse
from google.cloud.discoveryengine_v1 import Session
import pytest

from answer_app.model import AnswerResponse
from answer_app.model import GetSessionResponse
from answer_app.utils import UtilHandler
from answer_app.utils import _answer_to_markdown
from answer_app.utils import sanitize


def test_sanitize() -> None:
    input_text = (
        "This is a test text with returns\r\n"
        " and newline\n"
        " characters.\r\n"
        " It should be sanitized to remove them."
    )
    expected_output = (
        "This is a test text with returns and newline characters."
        " It should be sanitized to remove them."
    )
    assert sanitize(input_text) == expected_output


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


def test_initialization(mock_answer_app_util_handler: UtilHandler) -> None:
    handler = mock_answer_app_util_handler
    assert handler._project == "test-project-id"
    assert handler._bq_client is not None
    assert handler._vais_handler is not None
    assert handler._table == "test-project-id.test-dataset.test-table"
    assert handler._feedback_table == "test-project-id.test-dataset.test-feedback-table"


def test_setup_logging(
    mock_answer_app_util_handler: UtilHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    handler = mock_answer_app_util_handler
    with caplog.at_level("DEBUG"):
        handler._setup_logging(log_level="DEBUG")
    assert "Logging level set to: DEBUG" in caplog.text


def test_load_config(
    mock_answer_app_util_handler: UtilHandler,
) -> None:
    handler = mock_answer_app_util_handler
    assert handler._config["location"] == "test-location"
    assert handler._config["search_engine_id"] == "test-engine-id"
    assert handler._config["dataset_id"] == "test-dataset"
    assert handler._config["table_id"] == "test-table"
    assert handler._config["feedback_table_id"] == "test-feedback-table"


def test_compose_table(
    mock_answer_app_util_handler: UtilHandler,
) -> None:
    handler = mock_answer_app_util_handler
    table = handler._compose_table(dataset_key="dataset_id", table_key="table_id")
    feedback_table = handler._compose_table(
        dataset_key="dataset_id", table_key="feedback_table_id"
    )

    assert table == "test-project-id.test-dataset.test-table"
    assert feedback_table == "test-project-id.test-dataset.test-feedback-table"


@pytest.mark.asyncio
async def test_answer_query_no_session_id(
    mock_answer_app_util_handler: UtilHandler,
) -> None:
    handler = mock_answer_app_util_handler
    handler._vais_handler.answer_query = AsyncMock(
        return_value=AnswerQueryResponse(
            answer=Answer(answer_text="Paris"),
            session=Session(name="session1"),
            answer_query_token="token1",
        )
    )

    response = await handler.answer_query(
        query_text="What is the capital of France?",
        session_id=None,
        user_pseudo_id="",
    )

    assert isinstance(response, AnswerResponse)
    assert response.answer["answer_text"] == "Paris"
    assert response.question == "What is the capital of France?"
    handler._vais_handler.answer_query.assert_called_once_with(
        query_text="What is the capital of France?",
        session_id=None,
        user_pseudo_id="",
    )


@pytest.mark.asyncio
async def test_answer_query_with_session_id(
    mock_answer_app_util_handler: UtilHandler,
) -> None:
    handler = mock_answer_app_util_handler
    handler._vais_handler.answer_query = AsyncMock(
        return_value=AnswerQueryResponse(
            answer=Answer(answer_text="Paris"),
            session=Session(name="test-session"),
            answer_query_token="token1",
        )
    )

    response = await handler.answer_query(
        query_text="What is the capital of France?",
        session_id="test-session",
        user_pseudo_id="",
    )

    assert isinstance(response, AnswerResponse)
    assert response.answer["answer_text"] == "Paris"
    assert response.question == "What is the capital of France?"
    handler._vais_handler.answer_query.assert_called_once_with(
        query_text="What is the capital of France?",
        session_id="test-session",
        user_pseudo_id="",
    )


@pytest.mark.asyncio
async def test_get_user_sessions(
    mock_answer_app_util_handler: UtilHandler,
) -> None:
    handler = mock_answer_app_util_handler
    handler._vais_handler.get_user_sessions = AsyncMock(
        return_value=[
            Session(name="session1"),
            Session(name="session2"),
        ]
    )

    response = await handler.get_user_sessions(user_pseudo_id="test-user")

    assert isinstance(response, GetSessionResponse)
    assert response.sessions[0]["name"] == "session1"
    assert response.sessions[1]["name"] == "session2"
    handler._vais_handler.get_user_sessions.assert_called_once_with(
        user_pseudo_id="test-user"
    )


@pytest.mark.asyncio
async def test_delete_session(
    mock_answer_app_util_handler: UtilHandler,
) -> None:
    handler = mock_answer_app_util_handler
    handler._vais_handler.delete_session = AsyncMock()

    await handler.delete_session(session_id="test-session")

    handler._vais_handler.delete_session.assert_called_once_with(
        session_id="test-session"
    )


@pytest.mark.asyncio
async def test_bq_insert_row_data(
    mock_answer_app_util_handler: UtilHandler,
) -> None:
    handler = mock_answer_app_util_handler
    handler._bq_client.insert_rows_json = MagicMock(return_value=[])

    data = {"key": "value"}
    errors = await handler.bq_insert_row_data(data=data)

    assert errors == []
    handler._bq_client.insert_rows_json.assert_called_once_with(
        table="test-project-id.test-dataset.test-table", json_rows=[data]
    )


@pytest.mark.asyncio
async def test_bq_insert_row_data_feedback(
    mock_answer_app_util_handler: UtilHandler,
) -> None:
    handler = mock_answer_app_util_handler
    handler._bq_client.insert_rows_json = MagicMock(return_value=[])

    data = {"key": "value"}
    errors = await handler.bq_insert_row_data(data=data, feedback=True)

    assert errors == []
    handler._bq_client.insert_rows_json.assert_called_once_with(
        table="test-project-id.test-dataset.test-feedback-table", json_rows=[data]
    )


@pytest.mark.asyncio
async def test_bq_insert_row_data_error(
    mock_answer_app_util_handler: UtilHandler,
) -> None:
    handler = mock_answer_app_util_handler
    handler._bq_client.insert_rows_json = MagicMock(
        return_value=[
            {"index": 0, "errors": [{"reason": "invalid", "message": "Invalid data"}]}
        ]
    )

    data = {"key": "value"}
    errors = await handler.bq_insert_row_data(data=data)

    assert errors == [
        {"index": 0, "errors": [{"reason": "invalid", "message": "Invalid data"}]}
    ]
    handler._bq_client.insert_rows_json.assert_called_once_with(
        table="test-project-id.test-dataset.test-table", json_rows=[data]
    )
