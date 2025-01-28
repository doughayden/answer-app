import os
import pytest
from typing import Generator
from unittest.mock import patch, MagicMock

from google.auth.credentials import Credentials


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
