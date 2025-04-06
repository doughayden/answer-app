import os
import pytest
from typing import Generator
from unittest.mock import patch, AsyncMock, MagicMock

from google.auth.credentials import Credentials

from answer_app.utils import UtilHandler as AnswerAppUtilHandler
from answer_app.discoveryengine_utils import DiscoveryEngineHandler
from client.utils import UtilHandler as ClientUtilHandler


# Fixtures for test_main.py
@pytest.fixture
def mock_util_handler_methods() -> Generator[MagicMock, None, None]:
    """Mock the methods of UtilHandler class instance answer_app.main.utils."""
    with patch("answer_app.main.utils") as mock_utils:
        mock_utils.answer_query = AsyncMock()
        mock_utils.get_user_sessions = AsyncMock()
        mock_utils.delete_session = AsyncMock()
        mock_utils.bq_insert_row_data = AsyncMock()
        yield mock_utils


@pytest.fixture()
def patch_my_env_var() -> Generator[None, None, None]:
    """Mock the environment variable MY_ENV_VAR."""
    with patch.dict(os.environ, {"MY_ENV_VAR": "test_value"}):
        yield


# Fixtures for test_utils.py
@pytest.fixture
def mock_load_config() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.UtilHandler._load_config") as mock_load_config:
        mock_load_config.return_value = {
            "location": "test-location",
            "search_engine_id": "test-engine-id",
            "dataset_id": "test-dataset",
            "table_id": "test-table",
            "feedback_table_id": "test-feedback-table",
        }
        yield mock_load_config


@pytest.fixture
def mock_utils_google_auth_default() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.google.auth.default") as mock_default:
        mock_credentials = MagicMock(spec=Credentials)
        mock_default.return_value = (mock_credentials, "test-project-id")
        yield mock_default


@pytest.fixture
def mock_bigquery_client() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.bigquery.Client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_utils_discoveryengine_handler() -> Generator[MagicMock, None, None]:
    with patch("answer_app.utils.DiscoveryEngineHandler") as mock_handler:
        yield mock_handler


@pytest.fixture
def mock_answer_app_util_handler(
    mock_load_config: MagicMock,
    mock_utils_google_auth_default: MagicMock,
    mock_bigquery_client: MagicMock,
    mock_utils_discoveryengine_handler: MagicMock,
) -> AnswerAppUtilHandler:
    """Mock the answer_app.utils.UtilHandler class instance."""
    return AnswerAppUtilHandler(log_level="DEBUG")


# Fixtures for test_discoveryengine_utils.py
@pytest.fixture
def mock_discoveryengine_utils_google_auth_default() -> (
    Generator[MagicMock, None, None]
):
    with patch("answer_app.discoveryengine_utils.google.auth.default") as mock_default:
        mock_credentials = MagicMock(spec=Credentials)
        mock_default.return_value = (mock_credentials, "test-project-id")
        yield mock_default


@pytest.fixture
def mock_discoveryengine_client() -> Generator[MagicMock, None, None]:
    with patch(
        "answer_app.discoveryengine_utils.discoveryengine.ConversationalSearchServiceAsyncClient"
    ) as mock_client:
        yield mock_client


@pytest.fixture
def mock_discoveryengine_handler(
    mock_discoveryengine_utils_google_auth_default: MagicMock,
    mock_discoveryengine_client: MagicMock,
) -> DiscoveryEngineHandler:
    """Mock the answer_app.discoveryengine_utils.DiscoveryEngineHandler class instance."""
    return DiscoveryEngineHandler(
        location="test-location",
        engine_id="test-engine-id",
        preamble="test-preamble",
    )


# Fixtures for test_client_utils.py
@pytest.fixture
def mock_load_dotenv() -> Generator[MagicMock, None, None]:
    with patch("client.utils.load_dotenv") as mock_load_dotenv:
        mock_load_dotenv.return_value = True
        yield mock_load_dotenv


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
def patch_k_revision() -> Generator[None, None, None]:
    with patch.dict(os.environ, {"K_REVISION": "test"}):
        yield


@pytest.fixture
def patch_target_principal() -> Generator[None, None, None]:
    with patch.dict(
        os.environ,
        {
            "TF_VAR_terraform_service_account": "test-sa@test-project.iam.gserviceaccount.com"
        },
    ):
        yield


@pytest.fixture
def patch_audience() -> Generator[None, None, None]:
    with patch.dict(os.environ, {"AUDIENCE": "https://app.example.com"}):
        yield


@pytest.fixture
def mock_client_util_handler(
    mock_load_dotenv: MagicMock,
    mock_client_google_auth_default: MagicMock,
    mock_google_auth_transport_requests: MagicMock,
    mock_fetch_id_token: MagicMock,
    mock_id_token_creds: MagicMock,
    mock_impersonated_creds: MagicMock,
    mock_refresh: MagicMock,
) -> ClientUtilHandler:
    """Mock the client.utils UtilHandler class instance."""
    return ClientUtilHandler(log_level="DEBUG")
