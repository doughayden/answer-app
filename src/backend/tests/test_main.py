import os
import pytest
from typing import Generator
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from main import app


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


@patch("utils.DiscoveryEngineAgent.answer_query")
@patch("utils.bigquery.Client.insert_rows_json")
def test_answer_with_session_id(
    mock_insert_rows_json: MagicMock, mock_answer_query: MagicMock
) -> None:
    mock_insert_rows_json.return_value = []  # Simulate successful insert with no errors
    mock_session = MagicMock()
    mock_session.name = "projects/test-project-id/locations/global/collections/default_collection/engines/test-engine-id/sessions/test-session"

    mock_answer_query.return_value = {
        "answer": {"answer_text": "Paris"},
        "session": {"name": "test-session"},
        "answer_query_token": "token1",
        "latency": 0.1234,
        "question": "What is the capital of France?",
    }

    response = client.post(
        "/answer",
        json={
            "question": "What is the capital of France?",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "session" in data
    assert "latency" in data
    assert data["session"]["name"] == "test-session"
    assert data["answer"]["answer_text"] == "Paris"
    assert data["question"] == "What is the capital of France?"
    mock_insert_rows_json.assert_called_once()


@patch("utils.DiscoveryEngineAgent.answer_query")
@patch("utils.bigquery.Client.insert_rows_json")
def test_answer_with_wildcard_session_id(
    mock_insert_rows_json: MagicMock, mock_answer_query: MagicMock
) -> None:
    mock_insert_rows_json.return_value = []  # Simulate successful insert with no errors
    mock_session = MagicMock()
    mock_session.name = "projects/test-project-id/locations/global/collections/default_collection/engines/test-engine-id/sessions/new-session"

    mock_answer_query.return_value = {
        "answer": {"answer_text": "Paris"},
        "session": {"name": "new-session"},
        "answer_query_token": "token1",
        "latency": 0.1234,
        "question": "What is the capital of France?",
    }

    response = client.post(
        "/answer",
        json={"question": "What is the capital of France?", "session_id": "-"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "session" in data
    assert "latency" in data
    assert data["session"]["name"] == "new-session"
    assert data["answer"]["answer_text"] == "Paris"
    assert data["question"] == "What is the capital of France?"
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
