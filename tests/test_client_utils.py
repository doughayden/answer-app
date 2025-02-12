import pytest
from unittest.mock import MagicMock

from client.utils import UtilHandler


def test_setup_logging_with_file_handler(
    mock_util_handler: UtilHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("DEBUG"):
        mock_util_handler._setup_logging(log_level="DEBUG")
    assert "Logging level set to: DEBUG" in caplog.text


def test_setup_logging_with_stream_handler(
    mock_util_handler: UtilHandler,
    caplog: pytest.LogCaptureFixture,
    patch_k_revision: MagicMock,
) -> None:
    with caplog.at_level("DEBUG"):
        mock_util_handler._setup_logging(log_level="DEBUG")
    assert "Logging level set to: DEBUG" in caplog.text


def test_get_default_id_token(
    mock_client_google_auth_default: MagicMock,
    mock_google_auth_transport_requests: MagicMock,
    mock_fetch_id_token: MagicMock,
    mock_verify_token: MagicMock,
) -> None:
    handler = UtilHandler(log_level="DEBUG")
    token = handler._get_default_id_token()
    assert token == "default-token"
    mock_fetch_id_token.assert_called_with(handler._auth_request, handler._audience)


def test_get_impersonated_id_token(
    mock_client_google_auth_default: MagicMock,
    mock_google_auth_transport_requests: MagicMock,
    mock_impersonated_creds: MagicMock,
    mock_id_token_creds: MagicMock,
    mock_verify_token: MagicMock,
    patch_target_principal: None,
) -> None:
    handler = UtilHandler(log_level="DEBUG")
    token = handler._get_impersonated_id_token()
    assert token == "impersonated-token"
    # mock_id_token_creds.assert_called()


def test_get_id_token(
    mock_util_handler: UtilHandler,
    mock_refresh: MagicMock,
    mock_fetch_id_token: MagicMock,
    # mock_impersonated_creds: MagicMock,
    mock_id_token_creds: MagicMock,
) -> None:
    mock_util_handler._target_principal = "test-sa@project.iam.gserviceaccount.com"
    token = mock_util_handler._get_id_token()
    assert token == "impersonated-token"

    mock_util_handler._target_principal = None
    token = mock_util_handler._get_id_token()
    assert token == "default-token"


def test_decode_token(mock_util_handler: UtilHandler) -> None:
    claims = mock_util_handler._decode_token()
    assert claims == {"exp": 9999999999}


def test_token_expired(mock_util_handler: UtilHandler) -> None:
    mock_util_handler._token_exp = 0
    assert mock_util_handler._token_expired() is True

    mock_util_handler._token_exp = 9999999999
    assert mock_util_handler._token_expired() is False


def test_initialization_local(
    mock_google_auth_default: MagicMock,
    mock_google_auth_transport_requests: MagicMock,
    mock_fetch_id_token: MagicMock,
    mock_impersonated_creds: MagicMock,
    mock_id_token_creds: MagicMock,
    mock_verify_token: MagicMock,
    mock_log_attributes: MagicMock,
    patch_target_principal: None,
) -> None:
    handler = UtilHandler(log_level="DEBUG")
    assert handler._project == "test-project-id"
    assert handler._credentials is not None
    assert handler._audience == "http://localhost:8888"
    assert handler._target_principal is not None
    assert handler._auth_request is not None
    assert handler._token == "impersonated-token"
    assert handler._token_exp == 9999999999


def test_initialization_deployed(
    mock_google_auth_default: MagicMock,
    mock_google_auth_transport_requests: MagicMock,
    mock_fetch_id_token: MagicMock,
    mock_verify_token: MagicMock,
    mock_log_attributes: MagicMock,
    patch_k_revision: None,
    patch_audience: None,
) -> None:
    handler = UtilHandler(log_level="DEBUG")
    assert handler._project == "test-project-id"
    assert handler._credentials is not None
    assert handler._audience == "https://app.example.com"
    assert handler._target_principal is None
    assert handler._auth_request is not None
    assert handler._token == "default-token"
    assert handler._token_exp == 9999999999


def test_send_request_success(
    mock_requests_post: MagicMock,
    mock_util_handler: UtilHandler,
) -> None:
    mock_requests_post.return_value.status_code = 200
    mock_requests_post.return_value.json.return_value = {
        "answer": "This is a test answer"
    }
    data = {
        "question": "What is the capital of France?",
        "session_id": "test-session",
    }
    response = mock_util_handler.send_request(data=data, route="/answer")

    assert response == {"answer": "This is a test answer"}
    mock_requests_post.assert_called_once_with(
        "http://localhost:8888/answer",
        headers={
            "Authorization": f"Bearer {mock_util_handler._token}",
            "Content-Type": "application/json",
        },
        json={
            "question": "What is the capital of France?",
            "session_id": "test-session",
        },
    )


def test_send_request_error(
    mock_requests_post: MagicMock,
    mock_util_handler: UtilHandler,
) -> None:
    mock_requests_post.return_value.status_code = 500
    mock_requests_post.return_value.text = "Internal Server Error"

    data = {
        "question": "What is the capital of France?",
        "session_id": "test-session",
    }
    response = mock_util_handler.send_request(data=data, route="/answer")

    assert response == {"error": "Internal Server Error"}
    mock_requests_post.assert_called_once_with(
        "http://localhost:8888/answer",
        headers={
            "Authorization": f"Bearer {mock_util_handler._token}",
            "Content-Type": "application/json",
        },
        json={
            "question": "What is the capital of France?",
            "session_id": "test-session",
        },
    )


def test_send_request_token_refresh(
    mock_requests_post: MagicMock,
    mock_util_handler: UtilHandler,
) -> None:
    mock_util_handler._token_exp = 0  # Force token to be expired
    mock_requests_post.return_value.status_code = 200
    mock_requests_post.return_value.json.return_value = {
        "answer": "This is a test answer"
    }

    data = {
        "question": "What is the capital of France?",
        "session_id": "test-session",
    }
    response = mock_util_handler.send_request(data=data, route="/answer")

    assert response == {"answer": "This is a test answer"}
    mock_requests_post.assert_called_once_with(
        "http://localhost:8888/answer",
        headers={
            "Authorization": f"Bearer default-token",
            "Content-Type": "application/json",
        },
        json={
            "question": "What is the capital of France?",
            "session_id": "test-session",
        },
    )
    assert mock_util_handler._token_exp == 9999999999
