import os
from pathlib import Path
from typing import Generator
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from google.auth.credentials import Credentials

# Mock Google Auth and all cloud services at the source before any imports
with patch("google.auth.default") as mock_auth:
    mock_credentials = MagicMock(spec=Credentials)
    mock_auth.return_value = (mock_credentials, "test-project-id")
    
    with patch("google.cloud.bigquery.Client"), \
         patch("google.cloud.discoveryengine_v1.ConversationalSearchServiceAsyncClient"), \
         patch("google.oauth2.id_token.fetch_id_token", return_value="mock-token"), \
         patch("google.auth.impersonated_credentials.Credentials"), \
         patch("google.auth.impersonated_credentials.IDTokenCredentials"), \
         patch("google.auth.transport.requests.Request"), \
         patch("client.utils.load_dotenv"), \
         patch("client.utils.google.auth.default", return_value=(mock_credentials, "test-project-id")):
        
        # Import modules after comprehensive mocking is in place
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
    with patch("answer_app.utils.UtilHandler._setup_logging"):
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
def mock_fetch_id_token() -> Generator[MagicMock, None, None]:
    with patch(
        "client.utils.google.oauth2.id_token.fetch_id_token"
    ) as mock_fetch_id_token:
        mock_fetch_id_token.return_value = "default-token"
        yield mock_fetch_id_token


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
def mock_load_dotenv() -> Generator[MagicMock, None, None]:
    with patch("client.utils.load_dotenv") as mock_load_dotenv:
        mock_load_dotenv.return_value = True
        yield mock_load_dotenv


@pytest.fixture
def mock_client_google_auth_default() -> Generator[MagicMock, None, None]:
    with patch("client.utils.google.auth.default") as mock_default:
        mock_credentials = MagicMock(spec=Credentials)
        mock_default.return_value = (mock_credentials, "test-project-id")
        yield mock_default


@pytest.fixture
def mock_google_auth_transport_requests() -> Generator[MagicMock, None, None]:
    with patch("client.utils.google.auth.transport.requests.Request") as mock_request:
        yield mock_request


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


# Fixtures for Streamlit app tests
@pytest.fixture
def mock_streamlit() -> Generator[MagicMock, None, None]:
    """Mock Streamlit components and context."""
    with patch("client.streamlit_app.st") as mock_st:
        # Mock experimental_user as a dict-like object
        mock_st.experimental_user = {
            "email": "test@example.com",
            "name": "Test User",
            "is_logged_in": True,
        }
        mock_st.session_state = {}
        mock_st.context = MagicMock(
            cookies=MagicMock(to_dict=MagicMock(return_value={})),
            headers=MagicMock(to_dict=MagicMock(return_value={})),
        )
        mock_st.set_page_config = MagicMock()
        mock_st.title = MagicMock()
        mock_st.sidebar = MagicMock()
        mock_st.chat_message = MagicMock()
        mock_st.chat_input = MagicMock()
        mock_st.success = MagicMock()
        mock_st.error = MagicMock()
        mock_st.stop = MagicMock()
        mock_st.button = MagicMock()
        mock_st.logout = MagicMock()
        mock_st.login = MagicMock()
        mock_st.empty = MagicMock()
        yield mock_st


@pytest.fixture
def mock_streamlit_utils() -> Generator[MagicMock, None, None]:
    """Mock the utils module for Streamlit app."""
    with patch("client.streamlit_app.utils") as mock_utils:
        mock_utils.send_request = AsyncMock()
        yield mock_utils


# Fixtures for client script tests
@pytest.fixture
def mock_client_utils() -> Generator[MagicMock, None, None]:
    """Mock utils instance for client script."""
    with patch("client.client.utils") as mock_utils:
        # Mock send_request as a regular function that returns values, not coroutines
        mock_utils.send_request = MagicMock()
        yield mock_utils


@pytest.fixture
def mock_client_console() -> Generator[MagicMock, None, None]:
    """Mock rich console for client script."""
    with patch("client.client.console") as mock_console:
        yield mock_console


@pytest.fixture
def mock_client_input() -> Generator[MagicMock, None, None]:
    """Mock input function for client script."""
    with patch("client.client.input") as mock_input:
        yield mock_input


@pytest.fixture
def mock_builtin_open() -> Generator[MagicMock, None, None]:
    """Mock builtin open function."""
    from unittest.mock import mock_open

    with patch("builtins.open", mock_open()) as mock_file_open:
        yield mock_file_open


@pytest.fixture
def mock_os_path_dirname() -> Generator[MagicMock, None, None]:
    """Mock os.path.dirname."""
    with patch("os.path.dirname") as mock_dirname:
        mock_dirname.return_value = "/test/dir"
        yield mock_dirname


@pytest.fixture
def mock_os_path_abspath() -> Generator[MagicMock, None, None]:
    """Mock os.path.abspath."""
    with patch("os.path.abspath") as mock_abspath:
        mock_abspath.return_value = "/test/dir/client.py"
        yield mock_abspath


@pytest.fixture
def mock_os_path_join() -> Generator[MagicMock, None, None]:
    """Mock os.path.join."""
    with patch("os.path.join") as mock_join:
        mock_join.side_effect = lambda *args: "/".join(args)
        yield mock_join


@pytest.fixture
def mock_client_file_operations(
    mock_builtin_open: MagicMock,
    mock_os_path_dirname: MagicMock,
    mock_os_path_abspath: MagicMock,
    mock_os_path_join: MagicMock,
) -> dict[str, MagicMock]:
    """Composed fixture for client file operations."""
    return {
        "open": mock_builtin_open,
        "dirname": mock_os_path_dirname,
        "abspath": mock_os_path_abspath,
        "join": mock_os_path_join,
    }


# Fixtures for client test data


# Fixtures for write_secrets_toml tests
@pytest.fixture
def sample_oauth_secrets() -> dict[str, dict[str, str | list[str]]]:
    """Sample OAuth client secrets data for testing write_secrets_toml functionality.

    Provides a realistic OAuth client configuration with localhost redirect URI
    for testing successful OAuth secret processing scenarios.

    Returns:
        dict[str, dict[str, str | list[str]]]: OAuth client secrets structure containing:
            - web: OAuth web application configuration with client_id, client_secret,
              and redirect_uris including localhost for development testing
    """
    return {
        "web": {
            "client_id": "test_client_id",
            "client_secret": "test_secret",
            "redirect_uris": ["http://localhost:8080", "https://example.com"],
        }
    }


@pytest.fixture
def sample_oauth_secrets_no_localhost() -> dict[str, dict[str, str | list[str]]]:
    """Sample OAuth client secrets data without localhost URI for error testing.

    Provides OAuth client configuration lacking localhost redirect URI to test
    error handling when no development-friendly redirect is available.

    Returns:
        dict[str, dict[str, str | list[str]]]: OAuth client secrets structure containing:
            - web: OAuth web application configuration with only production redirect URIs,
              deliberately excluding localhost to trigger validation errors
    """
    return {
        "web": {
            "client_id": "test_id",
            "client_secret": "test_secret",
            "redirect_uris": ["https://example.com", "https://other.com"],
        }
    }


@pytest.fixture
def mock_json_files() -> dict[str, list[Path]]:
    """Mock file paths for testing OAuth client secrets file discovery.

    Provides different file discovery scenarios to test the find_client_secrets_file
    function's prioritization logic and error handling.

    Returns:
        dict[str, list[Path]]: Dictionary containing file path lists for different scenarios:
            - with_client_secret: List including a file with 'client_secret' in name (prioritized)
            - without_client_secret: List of generic JSON files (alphabetical fallback)
            - empty: Empty list for testing no-files-found error condition
    """
    return {
        "with_client_secret": [
            Path("other.json"),
            Path("client_secret_oauth.json"),
            Path("another.json"),
        ],
        "without_client_secret": [
            Path("a_first.json"),
            Path("b_middle.json"),
            Path("z_last.json"),
        ],
        "empty": [],
    }


@pytest.fixture
def mock_click_confirm() -> Generator[MagicMock, None, None]:
    """Mock click.confirm for write_secrets_toml tests."""
    with patch("package_scripts.write_secrets_toml.click.confirm") as mock_confirm:
        yield mock_confirm


@pytest.fixture
def mock_click_secho() -> Generator[MagicMock, None, None]:
    """Mock click.secho for write_secrets_toml tests."""
    with patch("package_scripts.write_secrets_toml.click.secho") as mock_secho:
        yield mock_secho


@pytest.fixture
def mock_path_operations() -> Generator[dict[str, MagicMock], None, None]:
    """Mock common Path operations for write_secrets_toml tests.

    Provides a consolidated fixture that mocks all Path operations commonly used
    in write_secrets_toml testing, reducing the need for individual patches
    and improving test maintainability.

    Yields:
        dict[str, MagicMock]: Dictionary containing mocked Path methods:
            - exists: Mock for Path.exists() file existence checks
            - read_text: Mock for Path.read_text() file reading
            - write_text: Mock for Path.write_text() file writing
            - mkdir: Mock for Path.mkdir() directory creation
            - glob: Mock for Path.glob() file pattern matching
    """
    with (
        patch.object(Path, "exists") as mock_exists,
        patch.object(Path, "read_text") as mock_read_text,
        patch.object(Path, "write_text") as mock_write_text,
        patch.object(Path, "mkdir") as mock_mkdir,
        patch.object(Path, "glob") as mock_glob,
    ):
        yield {
            "exists": mock_exists,
            "read_text": mock_read_text,
            "write_text": mock_write_text,
            "mkdir": mock_mkdir,
            "glob": mock_glob,
        }
