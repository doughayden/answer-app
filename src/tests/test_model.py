import pytest
from pydantic import ValidationError
from model import (
    QuestionRequest,
    SelectedReferences,
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


def test_selected_references() -> None:
    # Valid input
    reference = SelectedReferences(
        chunk="chunk1",
        content="This is the content.",
        relevance_score=0.95,
        document="document1",
    )
    assert reference.chunk == "chunk1"
    assert reference.content == "This is the content."
    assert reference.relevance_score == 0.95
    assert reference.document == "document1"

    # Invalid input (missing required field)
    with pytest.raises(ValidationError):
        SelectedReferences(
            chunk="chunk1", content="This is the content.", relevance_score=0.95
        )


def test_answer_response() -> None:
    # Valid input
    response = AnswerResponse(
        answer="Paris",
        references=[
            SelectedReferences(
                chunk="chunk1",
                content="This is the content.",
                relevance_score=0.95,
                document="document1",
            )
        ],
        latency=0.1234,
    )
    assert response.answer == "Paris"
    assert len(response.references) == 1
    assert response.latency == 0.1234


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
