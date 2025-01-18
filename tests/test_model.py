import pytest

from pydantic import ValidationError

from answer_app.model import (
    QuestionRequest,
    AnswerResponse,
    HealthCheckResponse,
    EnvVarResponse,
    ClientCitation,
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
        markdown="**Paris**",
    )
    assert response.question == "What is the capital of France?"
    assert response.answer == {"answer_text": "Paris"}
    assert response.latency == 0.1234
    assert response.session == {"name": "session1"}
    assert response.answer_query_token == "token1"
    assert response.markdown == "**Paris**"


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


def test_client_citation() -> None:
    # Valid input
    citation = ClientCitation(
        start_index=0,
        end_index=10,
        ref_index=1,
        content='Test "content"',
        score=0.9,
        title="Test Title",
        citation_index=1,
        uri="gs://bucket/file.txt",
    )
    assert citation.start_index == 0
    assert citation.end_index == 10
    assert citation.ref_index == 1
    assert citation.content == 'Test "content"'
    assert citation.score == 0.9
    assert citation.title == "Test Title"
    assert citation.citation_index == 1
    assert citation.uri == "gs://bucket/file.txt"

    # Test get_inline_link method
    assert (
        citation.get_inline_link()
        == " _[[1](https://storage.cloud.google.com/bucket/file.txt \"Test 'content'\")]_"
    )

    # Test get_footer_link method
    assert (
        citation.get_footer_link() == "https://storage.cloud.google.com/bucket/file.txt"
    )

    # Test count_chars method
    assert citation.count_chars() == len(
        " _[[1](https://storage.cloud.google.com/bucket/file.txt \"Test 'content'\")]_"
    )

    # Test without citation_index
    citation.citation_index = None
    with pytest.raises(ValueError):
        citation.get_inline_link()

    # Test update_citation_index method
    citation.update_citation_index(2)
    assert citation.citation_index == 2
    assert (
        citation.get_inline_link()
        == " _[[2](https://storage.cloud.google.com/bucket/file.txt \"Test 'content'\")]_"
    )
    assert citation.count_chars() == len(
        " _[[2](https://storage.cloud.google.com/bucket/file.txt \"Test 'content'\")]_"
    )
