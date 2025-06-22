from unittest.mock import MagicMock

from fastapi.testclient import TestClient
import pytest

from answer_app.main import app
from answer_app.model import AnswerResponse
from answer_app.model import GetSessionResponse


client = TestClient(app)


@pytest.mark.asyncio
async def test_answer_no_session_id(mock_util_handler_methods: MagicMock) -> None:
    mock_util_handler_methods.answer_query.return_value = AnswerResponse(
        question="What is the capital of France?",
        markdown="**Paris**",
        latency=0.1,
        answer={"answer_text": "Paris"},
        session=None,
        answer_query_token="token1",
    )
    mock_util_handler_methods.bq_insert_row_data.return_value = []

    request_body = {"question": "What is the capital of France?"}
    response = client.post("/answer", json=request_body)

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is the capital of France?"
    assert data["markdown"] == "**Paris**"
    assert "latency" in data
    assert data["answer"]["answer_text"] == "Paris"
    assert data["session"] is None
    assert data["answer_query_token"] == "token1"
    mock_util_handler_methods.answer_query.assert_called_once()
    mock_util_handler_methods.bq_insert_row_data.assert_called_once()


@pytest.mark.asyncio
async def test_answer_with_session_id(mock_util_handler_methods: MagicMock) -> None:
    mock_util_handler_methods.answer_query.return_value = AnswerResponse(
        question="What is the capital of France?",
        markdown="**Paris**",
        latency=0.1,
        answer={"answer_text": "Paris"},
        session={"name": "test-session"},
        answer_query_token="token1",
    )
    mock_util_handler_methods.bq_insert_row_data.return_value = []

    request_body = {
        "question": "What is the capital of France?",
        "session_id": "test-session",
    }
    response = client.post("/answer", json=request_body)

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is the capital of France?"
    assert data["markdown"] == "**Paris**"
    assert "latency" in data
    assert data["answer"]["answer_text"] == "Paris"
    assert data["session"]["name"] == "test-session"
    assert data["answer_query_token"] == "token1"
    mock_util_handler_methods.answer_query.assert_called_once()
    mock_util_handler_methods.bq_insert_row_data.assert_called_once()


@pytest.mark.asyncio
async def test_answer_with_wildcard_session_id(
    mock_util_handler_methods: MagicMock,
) -> None:
    mock_util_handler_methods.answer_query.return_value = AnswerResponse(
        question="What is the capital of France?",
        markdown="**Paris**",
        latency=0.1,
        answer={"answer_text": "Paris"},
        session={"name": "new-session"},
        answer_query_token="token1",
    )
    mock_util_handler_methods.bq_insert_row_data.return_value = []

    request_body = {
        "question": "What is the capital of France?",
        "session_id": "-",
    }
    response = client.post("/answer", json=request_body)

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is the capital of France?"
    assert data["markdown"] == "**Paris**"
    assert "latency" in data
    assert data["answer"]["answer_text"] == "Paris"
    assert data["session"]["name"] == "new-session"
    assert data["answer_query_token"] == "token1"
    mock_util_handler_methods.answer_query.assert_called_once()
    mock_util_handler_methods.bq_insert_row_data.assert_called_once()


def test_health_check(mock_util_handler_methods: MagicMock) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_get_env_variable(
    mock_util_handler_methods: MagicMock,
    patch_my_env_var: MagicMock,
) -> None:
    response = client.get("/get-env-variable?name=MY_ENV_VAR")
    assert response.status_code == 200
    data = response.json()
    assert data == {"name": "MY_ENV_VAR", "value": "test_value"}


def test_get_env_variable_not_set(
    mock_util_handler_methods: MagicMock,
    patch_my_env_var: MagicMock,
) -> None:
    response = client.get("/get-env-variable?name=NOT_SET_VAR")
    assert response.status_code == 200
    data = response.json()
    assert data == {"name": "NOT_SET_VAR", "value": None}


@pytest.mark.asyncio
async def test_get_sessions(mock_util_handler_methods: MagicMock) -> None:
    mock_util_handler_methods.get_user_sessions.return_value = GetSessionResponse(
        sessions=[{"name": "test-session"}, {"name": "another-session"}]
    )

    response = client.get("/sessions/?user_id=test-user")

    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) == 2
    assert data["sessions"][0]["name"] == "test-session"
    assert data["sessions"][1]["name"] == "another-session"
    mock_util_handler_methods.get_user_sessions.assert_called_once_with(
        user_pseudo_id="test-user"
    )


@pytest.mark.asyncio
async def test_answer_with_bq_insert_error(
    mock_util_handler_methods: MagicMock,
) -> None:
    mock_util_handler_methods.answer_query.return_value = AnswerResponse(
        question="What is the capital of France?",
        markdown="**Paris**",
        latency=0.1,
        answer={"answer_text": "Paris"},
        session={"name": "test-session"},
        answer_query_token="token1",
    )
    mock_util_handler_methods.bq_insert_row_data.return_value = [
        {"index": 0, "errors": ["error"]}
    ]

    response = client.post(
        "/answer",
        json={
            "question": "What is the capital of France?",
            "session_id": "test-session",
        },
    )

    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "500: [{'index': 0, 'errors': ['error']}]"


@pytest.mark.asyncio
async def test_answer_with_bq_insert_exception(
    mock_util_handler_methods: MagicMock,
) -> None:
    mock_util_handler_methods.answer_query.return_value = AnswerResponse(
        question="What is the capital of France?",
        markdown="**Paris**",
        latency=0.1,
        answer={"answer_text": "Paris"},
        session={"name": "test-session"},
        answer_query_token="token1",
    )
    mock_util_handler_methods.bq_insert_row_data.side_effect = Exception(
        "Test exception"
    )

    response = client.post(
        "/answer",
        json={
            "question": "What is the capital of France?",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Test exception"


@pytest.mark.asyncio
async def test_feedback(mock_util_handler_methods: MagicMock) -> None:
    mock_util_handler_methods.bq_insert_row_data.return_value = []

    response = client.post(
        "/feedback",
        json={
            "answer_query_token": "token1",
            "question": "What is the capital of France?",
            "answer_text": "Paris",
            "feedback_value": 1,
            "feedback_text": "This is a test feedback",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "answer_query_token": "token1",
        "message": "Feedback logged successfully.",
    }


@pytest.mark.asyncio
async def test_feedback_missing_fields(mock_util_handler_methods: MagicMock) -> None:
    response = client.post(
        "/feedback",
        json={
            "feedback_value": 1,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feedback_invalid_value(mock_util_handler_methods: MagicMock) -> None:
    response = client.post(
        "/feedback",
        json={
            "answer_query_token": "token1",
            "question": "What is the capital of France?",
            "answer_text": "Paris",
            "feedback_value": 10,
            "feedback_text": "This is a test feedback",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feedback_insert_errors(mock_util_handler_methods: MagicMock) -> None:
    mock_util_handler_methods.bq_insert_row_data.return_value = [
        {"index": 0, "errors": ["error"]}
    ]

    response = client.post(
        "/feedback",
        json={
            "answer_query_token": "token1",
            "question": "What is the capital of France?",
            "answer_text": "Paris",
            "feedback_value": 1,
            "feedback_text": "This is a test feedback",
        },
    )

    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "[{'index': 0, 'errors': ['error']}]"
