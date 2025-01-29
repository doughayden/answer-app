import os
import pytest
from typing import Generator
from unittest.mock import patch, MagicMock

from google.auth.credentials import Credentials

from client.utils import UtilHandler


@pytest.fixture
def mock_default() -> Generator[MagicMock, None, None]:
    with patch("answer_app.discoveryengine_utils.default") as mock_default:
        mock_default.return_value = (MagicMock(), "test-project-id")
        yield mock_default


@pytest.fixture
def mock_discoveryengine_client() -> Generator[MagicMock, None, None]:
    with patch(
        "answer_app.discoveryengine_utils.discoveryengine.ConversationalSearchServiceAsyncClient"
    ) as mock_client:
        yield mock_client


@pytest.fixture(autouse=True)
def set_env_vars() -> Generator[None, None, None]:
    os.environ["MY_ENV_VAR"] = "test_value"
    yield
    del os.environ["MY_ENV_VAR"]


@pytest.fixture
def mock_google_auth_default() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.google.auth.default") as mock_default:
        mock_credentials = MagicMock(spec=Credentials)
        mock_default.return_value = (mock_credentials, "test-project-id")
        yield mock_default


@pytest.fixture
def mock_bigquery_client() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.bigquery.Client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_discoveryengine_agent() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.DiscoveryEngineAgent") as mock_agent:
        yield mock_agent


@pytest.fixture
def mock_load_config() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.UtilHandler._load_config") as mock_load_config:
        mock_load_config.return_value = {
            "location": "us-central1",
            "search_engine_id": "test-engine-id",
            "dataset_id": "test-dataset",
            "table_id": "test-table",
            "feedback_table_id": "test-feedback-table",
        }
        yield mock_load_config


@pytest.fixture
def mock_bq_insert_row_data() -> Generator[MagicMock, None, None]:
    with patch(
        "answer_app.utils.UtilHandler.bq_insert_row_data"
    ) as mock_bq_insert_row_data:
        yield mock_bq_insert_row_data


@pytest.fixture
def mock_answer_query() -> Generator[MagicMock, None, None]:
    with patch(
        "answer_app.utils.DiscoveryEngineAgent.answer_query"
    ) as mock_answer_query:
        yield mock_answer_query


@pytest.fixture
def mock_client_google_auth_default():
    with patch("client.utils.google.auth.default") as mock_default:
        mock_credentials = MagicMock(spec=Credentials)
        mock_default.return_value = (mock_credentials, "test-project-id")
        yield mock_default


@pytest.fixture
def mock_google_auth_transport_requests() -> Generator[MagicMock, None, None]:
    with patch("client.utils.google.auth.transport.requests.Request") as mock_request:
        yield mock_request


# @pytest.fixture
# def mock_default_id_token() -> Generator[MagicMock, None, None]:
#     with patch(
#         "client.utils.UtilHandler._get_default_id_token"
#     ) as mock_default_id_token:
#         mock_default_id_token.return_value = "default-token"
#         yield mock_default_id_token


# @pytest.fixture
# def mock_impersonated_id_token() -> Generator[MagicMock, None, None]:
#     with patch(
#         "client.utils.UtilHandler._get_impersonated_id_token"
#     ) as mock_impersonated_id_token:
#         mock_impersonated_id_token.return_value = "impersonated-token"
#         yield mock_impersonated_id_token


@pytest.fixture
def mock_fetch_id_token() -> Generator[MagicMock, None, None]:
    with patch(
        "client.utils.google.oauth2.id_token.fetch_id_token"
    ) as mock_fetch_id_token:
        mock_fetch_id_token.return_value = "default-token"
        yield mock_fetch_id_token


@pytest.fixture
def mock_impersonated_creds() -> Generator[MagicMock, None, None]:
    with patch(
        "client.utils.google.auth.impersonated_credentials.Credentials"
    ) as mock_impersonated_creds:
        mock_impersonated_creds_instance = mock_impersonated_creds.return_value
        yield mock_impersonated_creds_instance


@pytest.fixture
def mock_id_token_creds() -> Generator[MagicMock, None, None]:
    with patch(
        "client.utils.google.auth.impersonated_credentials.IDTokenCredentials"
    ) as mock_id_token_creds:
        mock_id_token_creds_instance = mock_id_token_creds.return_value
        mock_id_token_creds_instance.token = "impersonated-token"
        yield mock_id_token_creds_instance


@pytest.fixture
def mock_refresh() -> Generator[MagicMock, None, None]:
    with patch(
        "client.utils.google.auth.impersonated_credentials.IDTokenCredentials.refresh"
    ) as mock_refresh:
        mock_refresh.return_value = None
        yield mock_refresh


@pytest.fixture
def mock_verify_token() -> Generator[MagicMock, None, None]:
    with patch("client.utils.google.oauth2.id_token.verify_token") as mock_verify_token:
        mock_verify_token.return_value = {"exp": 9999999999}
        yield mock_verify_token


@pytest.fixture
def mock_log_attributes() -> Generator[MagicMock, None, None]:
    with patch("client.utils.UtilHandler._log_attributes") as mock_log_attributes:
        yield mock_log_attributes


@pytest.fixture
def patch_k_revision() -> Generator[None, None, None]:
    with patch.dict(os.environ, {"K_REVISION": "test"}):
        yield


@pytest.fixture
def patch_target_principal() -> Generator[None, None, None]:
    with patch.dict(
        os.environ,
        {"TF_VAR_terraform_service_account": "test-sa@projct.iam.gserviceaccount.com"},
    ):
        yield


@pytest.fixture
def patch_audience() -> Generator[None, None, None]:
    with patch.dict(os.environ, {"AUDIENCE": "https://app.example.com"}):
        yield


@pytest.fixture
def mock_util_handler(
    mock_client_google_auth_default: MagicMock,
    mock_google_auth_transport_requests: MagicMock,
    mock_fetch_id_token: MagicMock,
    mock_verify_token: MagicMock,
    mock_log_attributes: MagicMock,
) -> UtilHandler:
    return UtilHandler(log_level="DEBUG")


@pytest.fixture
def mock_requests_post() -> Generator[MagicMock, None, None]:
    with patch("client.utils.requests.post") as mock_post:
        yield mock_post
