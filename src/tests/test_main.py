import os
import pytest
from fastapi.testclient import TestClient
from main import app
from typing import Generator

client = TestClient(app)


@pytest.fixture(autouse=True)
def set_env_vars() -> Generator[None, None, None]:
    os.environ["MY_ENV_VAR"] = "test_value"
    yield
    del os.environ["MY_ENV_VAR"]


def test_answer() -> None:
    response = client.post(
        "/answer", json={"question": "What is the capital of France?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "references" in data
    assert "latency" in data


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
