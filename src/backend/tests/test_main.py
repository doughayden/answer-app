import os
import pytest
from typing import Generator
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import HTTPException

from main import app
from google.cloud.discoveryengine_v1.types import AnswerQueryResponse, Answer, Session
import base64

client = TestClient(app)


@pytest.fixture(autouse=True)
def set_env_vars() -> Generator[None, None, None]:
    os.environ["MY_ENV_VAR"] = "test_value"
    yield
    del os.environ["MY_ENV_VAR"]


def test_answer_no_session_id() -> None:
    response = client.post(
        "/answer", json={"question": "What is the capital of France?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "latency" in data
    assert data["session"]["name"] == ""


@pytest.mark.asyncio
@patch("utils.DiscoveryEngineAgent.answer_query")
@patch("utils.bigquery.Client.insert_rows_json")
async def test_answer_with_session_id(
    mock_insert_rows_json: MagicMock, mock_answer_query: MagicMock
) -> None:
    mock_insert_rows_json.return_value = []  # Simulate successful insert with no errors
    mock_answer_query.return_value = AnswerQueryResponse(
        answer=Answer(answer_text="**Paris**"),
        session=Session(name="test-session"),
        answer_query_token="token1",
    )

    response = client.post(
        "/answer",
        json={
            "question": "What is the capital of France?",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is the capital of France?"
    expected_markdown = base64.b64encode(
        "**Paris**\n\n**Citations:**\n\n".encode("utf-8")
    ).decode("utf-8")
    assert data["markdown"] == expected_markdown
    assert "latency" in data  # Ensure latency is present but do not assert its value
    assert data["answer"]["answer_text"] == "**Paris**"
    assert data["session"]["name"] == "test-session"
    assert data["answer_query_token"] == "token1"

    mock_insert_rows_json.assert_called_once()


@pytest.mark.asyncio
@patch("utils.DiscoveryEngineAgent.answer_query")
@patch("utils.bigquery.Client.insert_rows_json")
async def test_answer_with_wildcard_session_id(
    mock_insert_rows_json: MagicMock, mock_answer_query: MagicMock
) -> None:
    mock_insert_rows_json.return_value = []  # Simulate successful insert with no errors
    mock_answer_query.return_value = AnswerQueryResponse(
        answer=Answer(answer_text="**Paris**"),
        session=Session(name="new-session"),
        answer_query_token="token1",
    )

    response = client.post(
        "/answer",
        json={"question": "What is the capital of France?", "session_id": "-"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is the capital of France?"
    expected_markdown = base64.b64encode(
        "**Paris**\n\n**Citations:**\n\n".encode("utf-8")
    ).decode("utf-8")
    assert data["markdown"] == expected_markdown
    assert "latency" in data  # Ensure latency is present but do not assert its value
    assert data["answer"]["answer_text"] == "**Paris**"
    assert data["session"]["name"] == "new-session"
    assert data["answer_query_token"] == "token1"

    mock_insert_rows_json.assert_called_once()


def test_health_check() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_get_env_variable() -> None:
    response = client.get("/get-env-variable?name=MY_ENV_VAR")
    assert response.status_code == 200
    data = response.json()
    assert data == {"name": "MY_ENV_VAR", "value": "test_value"}


def test_get_env_variable_not_set() -> None:
    response = client.get("/get-env-variable?name=NOT_SET_VAR")
    assert response.status_code == 200
    data = response.json()
    assert data == {"name": "NOT_SET_VAR", "value": None}


@pytest.mark.asyncio
@patch("utils.UtilHandler.bq_insert_row_data")
@patch("utils.DiscoveryEngineAgent.answer_query")
async def test_answer_with_bq_insert_error(
    mock_answer_query: MagicMock, mock_bq_insert_row_data: MagicMock
) -> None:
    mock_answer_query.return_value = AnswerQueryResponse(
        answer=Answer(answer_text="**Paris**"),
        session=Session(name="test-session"),
        answer_query_token="token1",
    )
    mock_bq_insert_row_data.return_value = [{"index": 0, "errors": ["error"]}]

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
@patch("utils.UtilHandler.bq_insert_row_data")
@patch("utils.DiscoveryEngineAgent.answer_query")
async def test_answer_with_bq_insert_exception(
    mock_answer_query: MagicMock, mock_bq_insert_row_data: MagicMock
) -> None:
    mock_answer_query.return_value = AnswerQueryResponse(
        answer=Answer(answer_text="**Paris**"),
        session=Session(name="test-session"),
        answer_query_token="token1",
    )
    mock_bq_insert_row_data.side_effect = Exception("Test exception")

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
