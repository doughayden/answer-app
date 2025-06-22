from unittest.mock import MagicMock

from google.auth.exceptions import DefaultCredentialsError
import pytest
from pytest_httpx import HTTPXMock

from client.utils import UtilHandler


def test_audience_env_var(
    mock_client_util_handler: UtilHandler,
    patch_audience: None,
) -> None:
    assert mock_client_util_handler.audience == "https://app.example.com"


def test_audience_default(
    mock_client_util_handler: UtilHandler,
) -> None:
    assert mock_client_util_handler.audience == "http://localhost:8888"


def test_target_principal(
    mock_client_util_handler: UtilHandler,
    patch_target_principal: None,
) -> None:
    assert (
        mock_client_util_handler.target_principal
        == "test-sa@test-project.iam.gserviceaccount.com"
    )


def test_target_principal_key_error(
    mock_client_util_handler: UtilHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with pytest.raises(KeyError):
        assert mock_client_util_handler.target_principal
    message = (
        "TF_VAR_terraform_service_account environment variable "
        "required for impersonation is not set."
    )
    assert message in caplog.text


def test_default_id_token(
    mock_client_util_handler: UtilHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("DEBUG"):
        assert mock_client_util_handler.id_token == "default-token"
    assert "Fetching ID token using default credentials..." in caplog.text
    assert "ID token retrieved using ADC." in caplog.text


def test_impersonated_id_token(
    mock_client_util_handler: UtilHandler,
    mock_fetch_id_token: MagicMock,
    patch_target_principal: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mock_fetch_id_token.side_effect = DefaultCredentialsError("test ADC error")
    with caplog.at_level("DEBUG"):
        assert mock_client_util_handler.id_token == "impersonated-token"
    assert "Switching to service account impersonation: test ADC error" in caplog.text
    assert "ID token retrieved using impersonated credentials." in caplog.text


def test_setup_logging_stream_handler(
    mock_client_util_handler: UtilHandler,
    caplog: pytest.LogCaptureFixture,
    patch_k_revision: None,
) -> None:
    with caplog.at_level("DEBUG"):
        mock_client_util_handler._setup_logging()
    assert "Logging level set to: DEBUG" in caplog.text


def test_setup_logging_local_file_handler(
    mock_client_util_handler: UtilHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("DEBUG"):
        mock_client_util_handler._setup_logging()
    assert "Logging level set to: DEBUG" in caplog.text


@pytest.mark.asyncio
async def test_send_request_success_post(
    mock_client_util_handler: UtilHandler,
    httpx_mock: HTTPXMock,
) -> None:
    response_json = {"answer": "This is a test answer"}
    httpx_mock.add_response(json=response_json, url="http://localhost:8888/answer")

    data = {"question": "What is the capital of France?", "session_id": "test-session"}
    response = await mock_client_util_handler.send_request(
        route="/answer",
        data=data,
        method="POST",
    )

    assert response == {"answer": "This is a test answer"}
    assert httpx_mock.get_request().url == "http://localhost:8888/answer"
    assert httpx_mock.get_request().method == "POST"


@pytest.mark.asyncio
async def test_send_request_success_get(
    mock_client_util_handler: UtilHandler,
    httpx_mock: HTTPXMock,
) -> None:
    response_json = {"status": "ok"}
    httpx_mock.add_response(json=response_json)
    response = await mock_client_util_handler.send_request(
        route="/get-session-history",
        method="GET",
    )

    assert response == {"status": "ok"}
    assert httpx_mock.get_request().method == "GET"


@pytest.mark.asyncio
async def test_send_request_error(
    mock_client_util_handler: UtilHandler,
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    httpx_mock.add_response(status_code=500, text="Internal Server Error")

    data = {"question": "What is the capital of France?", "session_id": "test-session"}
    response = await mock_client_util_handler.send_request(data=data, route="/answer")

    assert response == {"error": "Internal Server Error"}
    assert httpx_mock.get_request().url == "http://localhost:8888/answer"
    assert httpx_mock.get_request().method == "POST"
    assert "Internal Server Error" in caplog.text


@pytest.mark.asyncio
async def test_send_request_unsupported_method(
    mock_client_util_handler: UtilHandler,
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    data = {"question": "What is the capital of France?", "session_id": "test-session"}
    response = await mock_client_util_handler.send_request(
        data=data, route="/answer", method="PUT"
    )

    assert response == {"error": "Unsupported method: PUT"}
    assert "Unsupported method: PUT" in caplog.text
