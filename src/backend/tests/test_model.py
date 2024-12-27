import pytest

from pydantic import ValidationError

from model import (
    QuestionRequest,
    AnswerResponse,
    HealthCheckResponse,
    EnvVarResponse,
)


def test_question_request() -> None:
    # Valid input
    question = QuestionRequest(question="What is the capital of France?")
    assert question.question == "What is the capital of France?"

    # Invalid input (missing required field)
    with pytest.raises(ValidationError):
        QuestionRequest()


def test_answer_response() -> None:
    # Valid input
    response = AnswerResponse(
        question="What is the capital of France?",
        answer={"answer_text": "Paris"},
        latency=0.1234,
        session={"name": "session1"},
        answer_query_token="token1",
    )
    assert response.question == "What is the capital of France?"
    assert response.answer == {"answer_text": "Paris"}
    assert response.latency == 0.1234
    assert response.session == {"name": "session1"}
    assert response.answer_query_token == "token1"


def test_health_check_response() -> None:
    # Valid input
    health_check = HealthCheckResponse()
    assert health_check.status == "ok"


def test_env_var_response() -> None:
    # Valid input
    env_var = EnvVarResponse(name="MY_ENV_VAR", value="test_value")
    assert env_var.name == "MY_ENV_VAR"
    assert env_var.value == "test_value"

    # Valid input with None value
    env_var = EnvVarResponse(name="MY_ENV_VAR", value=None)
    assert env_var.name == "MY_ENV_VAR"
    assert env_var.value is None
