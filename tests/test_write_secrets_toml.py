import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from package_scripts.write_secrets_toml import WebConfig
from package_scripts.write_secrets_toml import OAuthClientSecrets
from package_scripts.write_secrets_toml import SecretsTomlData
from package_scripts.write_secrets_toml import find_client_secrets_file
from package_scripts.write_secrets_toml import process_client_secrets
from package_scripts.write_secrets_toml import run
from package_scripts.write_secrets_toml import SECRETS_TOML_TEMPLATE
from package_scripts.write_secrets_toml import DEFAULT_SECRETS_DIR
from package_scripts.write_secrets_toml import DEFAULT_OUTPUT_PATH


class TestModels:
    """Test Pydantic models for OAuth client secrets configuration."""

    def test_web_config_valid(
        self, sample_oauth_secrets: dict[str, dict[str, str | list[str]]]
    ) -> None:
        """Test WebConfig model validation with valid OAuth data.

        Args:
            sample_oauth_secrets: Valid OAuth client secrets data from fixture.
        """
        web_data = sample_oauth_secrets["web"]
        config = WebConfig(**web_data)
        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_secret"
        assert len(config.redirect_uris) == 2

    def test_oauth_client_secrets_valid(
        self, sample_oauth_secrets: dict[str, dict[str, str | list[str]]]
    ) -> None:
        """Test OAuthClientSecrets model validation with valid OAuth data.

        Args:
            sample_oauth_secrets: Valid OAuth client secrets data from fixture.
        """
        secrets = OAuthClientSecrets(**sample_oauth_secrets)
        assert secrets.web.client_id == "test_client_id"

    def test_secrets_toml_data_default_cookie_secret(self) -> None:
        """Test SecretsTomlData generates random cookie secret by default.

        Validates that the SecretsTomlData model automatically generates a secure
        cookie secret when none is explicitly provided.
        """
        data = SecretsTomlData(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080",
        )
        assert len(data.cookie_secret) > 0
        assert data.client_id == "test_id"

    def test_secrets_toml_data_custom_cookie_secret(self) -> None:
        """Test SecretsTomlData accepts and preserves custom cookie secret.

        Validates that when a custom cookie secret is provided, it is used
        instead of generating a random one.
        """
        custom_secret = "custom_cookie_secret"
        data = SecretsTomlData(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080",
            cookie_secret=custom_secret,
        )
        assert data.cookie_secret == custom_secret

    def test_first_localhost_uri_found(self) -> None:
        """Test finding first localhost URI from a list of redirect URIs.

        Validates that the first localhost URI is correctly identified from
        a mixed list of production and development redirect URIs.
        """
        uris = ["https://example.com", "http://localhost:8080", "http://localhost:3000"]
        result = SecretsTomlData.first_localhost_uri(uris)
        assert result == "http://localhost:8080"

    def test_first_localhost_uri_not_found(self) -> None:
        """Test behavior when no localhost URI exists in redirect URI list.

        Validates that None is returned when the redirect URI list contains
        only production URIs without localhost entries.
        """
        uris = ["https://example.com", "https://other.com"]
        result = SecretsTomlData.first_localhost_uri(uris)
        assert result is None

    def test_first_localhost_uri_empty_list(self) -> None:
        """Test behavior with empty redirect URI list.

        Validates that None is returned when an empty redirect URI list
        is provided to the localhost detection function.
        """
        result = SecretsTomlData.first_localhost_uri([])
        assert result is None

    def test_from_oauth_data_success(
        self, sample_oauth_secrets: dict[str, dict[str, str | list[str]]]
    ) -> None:
        """Test successful SecretsTomlData creation from valid OAuth data.

        Validates the conversion process from OAuth client secrets to TOML configuration
        when a localhost redirect URI is available.

        Args:
            sample_oauth_secrets: Valid OAuth client secrets data from fixture.
        """
        oauth_data = OAuthClientSecrets(**sample_oauth_secrets)

        result = SecretsTomlData.from_oauth_data(oauth_data)

        assert result.client_id == "test_client_id"
        assert result.client_secret == "test_secret"
        assert result.redirect_uri == "http://localhost:8080"
        assert len(result.cookie_secret) > 0

    def test_from_oauth_data_no_localhost_uri(
        self, sample_oauth_secrets_no_localhost: dict[str, dict[str, str | list[str]]]
    ) -> None:
        """Test SecretsTomlData creation failure when no localhost URI found.

        Validates that the conversion process properly raises ValueError when
        OAuth client secrets contain no localhost redirect URI suitable for development.

        Args:
            sample_oauth_secrets_no_localhost: OAuth client secrets without localhost URI from fixture.

        Raises:
            ValueError: When no localhost redirect URI is found in the OAuth configuration.
        """
        oauth_data = OAuthClientSecrets(**sample_oauth_secrets_no_localhost)

        with pytest.raises(ValueError, match="No localhost redirect URI"):
            SecretsTomlData.from_oauth_data(oauth_data)


class TestFindClientSecretsFile:
    """Test find_client_secrets_file function for OAuth client secrets file discovery."""

    def test_find_client_secrets_prioritizes_client_secret_name(
        self,
        mock_path_operations: dict[str, MagicMock],
        mock_json_files: dict[str, list[Path]],
    ) -> None:
        """Test that files with 'client_secret' in name are prioritized over other JSON files.

        Args:
            mock_path_operations: Mocked Path operations from fixture.
            mock_json_files: Collection of mock file paths from fixture.
        """
        mock_path_operations["glob"].return_value = mock_json_files[
            "with_client_secret"
        ]

        result = find_client_secrets_file(Path("test_dir"))
        assert result.name == "client_secret_oauth.json"

    def test_find_client_secrets_fallback_to_first(
        self,
        mock_path_operations: dict[str, MagicMock],
        mock_json_files: dict[str, list[Path]],
    ) -> None:
        """Test fallback to alphabetically first JSON file when no client_secret file exists.

        Args:
            mock_path_operations: Mocked Path operations from fixture.
            mock_json_files: Collection of mock file paths from fixture.
        """
        mock_path_operations["glob"].return_value = mock_json_files[
            "without_client_secret"
        ]

        result = find_client_secrets_file(Path("test_dir"))
        assert result.name == "a_first.json"  # Should be alphabetically first

    def test_find_client_secrets_no_json_files(
        self,
        mock_path_operations: dict[str, MagicMock],
        mock_json_files: dict[str, list[Path]],
    ) -> None:
        """Test proper error handling when no JSON files are found in directory.

        Args:
            mock_path_operations: Mocked Path operations from fixture.
            mock_json_files: Collection of mock file paths from fixture.

        Raises:
            click.ClickException: When no JSON files are found in the search directory.
        """
        mock_path_operations["glob"].return_value = mock_json_files["empty"]

        with pytest.raises(click.ClickException, match="No JSON files found"):
            find_client_secrets_file(Path("test_dir"))


class TestProcessClientSecrets:
    """Test process_client_secrets function for OAuth secrets file processing."""

    def test_process_client_secrets_file_not_found(
        self, mock_path_operations: dict[str, MagicMock]
    ) -> None:
        """Test proper error handling when input OAuth secrets file doesn't exist.

        Args:
            mock_path_operations: Mocked Path operations from fixture.

        Raises:
            FileNotFoundError: When the specified input file cannot be found.
        """
        input_path = Path("nonexistent.json")
        output_path = Path("secrets.toml")

        mock_path_operations["exists"].return_value = False

        with pytest.raises(FileNotFoundError):
            process_client_secrets(input_path, output_path)

    def test_process_client_secrets_overwrite_confirmed(
        self,
        mock_path_operations: dict[str, MagicMock],
        mock_click_secho: MagicMock,
        mock_click_confirm: MagicMock,
        sample_oauth_secrets: dict[str, dict[str, str | list[str]]],
    ) -> None:
        """Test successful file overwrite when user confirms the operation.

        Validates that when an output file already exists and the user confirms
        overwriting, the secrets processing completes successfully.

        Args:
            mock_path_operations: Mocked Path operations from fixture.
            mock_click_secho: Mocked click.secho for output messages.
            mock_click_confirm: Mocked click.confirm for user confirmation.
            sample_oauth_secrets: Valid OAuth client secrets data from fixture.
        """
        mock_click_confirm.return_value = True
        input_path = Path("client_secrets.json")
        output_path = Path("secrets.toml")

        mock_path_operations["exists"].return_value = True
        mock_path_operations["read_text"].return_value = json.dumps(
            sample_oauth_secrets
        )

        process_client_secrets(input_path, output_path)

        # Verify warning was shown and file was written
        mock_click_secho.assert_called()
        mock_click_confirm.assert_called_once()
        mock_path_operations["write_text"].assert_called_once()

        # Verify content contains expected values
        written_content = mock_path_operations["write_text"].call_args[0][0]
        assert "test_client_id" in written_content

    def test_process_client_secrets_overwrite_cancelled(
        self,
        mock_path_operations: dict[str, MagicMock],
        mock_click_secho: MagicMock,
        mock_click_confirm: MagicMock,
        sample_oauth_secrets: dict[str, dict[str, str | list[str]]],
    ) -> None:
        """Test operation cancellation when user rejects file overwrite.

        Validates that when an output file already exists and the user declines
        to overwrite it, the operation terminates gracefully without processing.

        Args:
            mock_path_operations: Mocked Path operations from fixture.
            mock_click_secho: Mocked click.secho for output messages.
            mock_click_confirm: Mocked click.confirm for user confirmation.
            sample_oauth_secrets: Valid OAuth client secrets data from fixture.
        """
        mock_click_confirm.return_value = False
        input_path = Path("client_secrets.json")
        output_path = Path("secrets.toml")

        mock_path_operations["exists"].return_value = True
        mock_path_operations["read_text"].return_value = json.dumps(
            sample_oauth_secrets
        )

        process_client_secrets(input_path, output_path)

        # Verify cancellation message was shown and no processing occurred
        mock_click_secho.assert_called()
        mock_click_confirm.assert_called_once()

    @patch("package_scripts.write_secrets_toml.OAuthClientSecrets.model_validate_json")
    def test_process_client_secrets_invalid_json(
        self,
        mock_model_validate_json: MagicMock,
        mock_path_operations: dict[str, MagicMock],
    ) -> None:
        """Test proper error handling when OAuth secrets file contains invalid JSON.

        Validates that malformed JSON in the input file is properly detected
        and results in a clear ValueError with descriptive message.

        Args:
            mock_model_validate_json: Mocked Pydantic model validation.
            mock_path_operations: Mocked Path operations from fixture.

        Raises:
            ValueError: When the input file contains invalid JSON that cannot be parsed.
        """
        input_path = Path("client_secrets.json")
        output_path = Path("secrets.toml")

        mock_path_operations["exists"].side_effect = [True, False]
        mock_path_operations["read_text"].return_value = "{ invalid json content"
        mock_model_validate_json.side_effect = json.JSONDecodeError(
            "test error", "doc", 1
        )

        with pytest.raises(
            ValueError, match="Invalid JSON format in client secrets file"
        ):
            process_client_secrets(input_path, output_path)


class TestCliCommand:
    """Test the CLI command interface for OAuth secrets processing."""

    @patch("package_scripts.write_secrets_toml.process_client_secrets")
    @patch("package_scripts.write_secrets_toml.find_client_secrets_file")
    def test_run_command_auto_detect_input(
        self, mock_find_file: MagicMock, mock_process: MagicMock
    ) -> None:
        """Test CLI command with auto-detected input file discovery.

        Validates that when no input file is explicitly provided, the CLI
        automatically discovers and uses an appropriate OAuth secrets file.

        Args:
            mock_find_file: Mocked file discovery function.
            mock_process: Mocked secrets processing function.
        """
        runner = CliRunner()

        # Mock auto-detection to return a file
        mock_input_file = Path("client_secret.json")
        mock_find_file.return_value = mock_input_file
        mock_process.return_value = None

        result = runner.invoke(run, ["-o", "output.toml"])

        assert result.exit_code == 0
        mock_find_file.assert_called_once()
        mock_process.assert_called_once_with(
            input_path=mock_input_file, output_path=Path("output.toml")
        )

    @patch("package_scripts.write_secrets_toml.process_client_secrets")
    def test_run_command_explicit_input(self, mock_process: MagicMock) -> None:
        """Test CLI command with explicitly specified input file.

        Validates that when an input file path is explicitly provided via command line,
        it is used directly without attempting auto-discovery.

        Args:
            mock_process: Mocked secrets processing function.
        """
        runner = CliRunner()

        mock_process.return_value = None

        result = runner.invoke(run, ["-i", "my_secrets.json", "-o", "output.toml"])

        assert result.exit_code == 0
        mock_process.assert_called_once_with(
            input_path=Path("my_secrets.json"), output_path=Path("output.toml")
        )

    @patch("package_scripts.write_secrets_toml.process_client_secrets")
    def test_run_command_error_handling(self, mock_process: MagicMock) -> None:
        """Test CLI command error handling for processing failures.

        Validates that when the underlying processing function raises an exception,
        the CLI properly catches it and exits with an appropriate error code.

        Args:
            mock_process: Mocked secrets processing function configured to raise an exception.
        """
        runner = CliRunner()

        # Mock process_client_secrets to raise an exception
        mock_process.side_effect = FileNotFoundError("File not found")

        result = runner.invoke(run, ["-i", "nonexistent.json", "-o", "output.toml"])

        assert result.exit_code == 1  # Should exit with error
        assert "Error:" in result.output

    @patch("package_scripts.write_secrets_toml.find_client_secrets_file")
    def test_run_command_no_json_files(self, mock_find_file: MagicMock) -> None:
        """Test CLI command behavior when no JSON files are found for auto-detection.

        Validates that when auto-detection fails to find any suitable OAuth secrets files,
        the CLI properly reports the error and exits with an appropriate code.

        Args:
            mock_find_file: Mocked file discovery function configured to raise ClickException.
        """
        runner = CliRunner()

        # Mock find_client_secrets_file to raise the expected exception
        mock_find_file.side_effect = click.ClickException("No JSON files found")

        result = runner.invoke(run, ["-o", "output.toml"])

        assert result.exit_code == 1
        assert "No JSON files found" in result.output


class TestConstants:
    """Test module constants and template formatting for OAuth secrets configuration."""

    def test_secrets_toml_template_format(self) -> None:
        """Test that TOML template has correct format placeholders and structure.

        Validates that the SECRETS_TOML_TEMPLATE constant contains all required
        placeholders and produces properly formatted TOML output when populated
        with OAuth configuration data.
        """
        test_data = {
            "redirect_uri": "http://localhost:8080",
            "cookie_secret": "test_secret",
            "client_id": "test_id",
            "client_secret": "test_secret_value",
        }

        formatted = SECRETS_TOML_TEMPLATE.format(**test_data)

        assert 'redirect_uri = "http://localhost:8080"' in formatted
        assert 'cookie_secret = "test_secret"' in formatted
        assert 'client_id = "test_id"' in formatted
        assert 'client_secret = "test_secret_value"' in formatted
        assert "[auth]" in formatted
        assert "[auth.google]" in formatted

    def test_default_paths(self) -> None:
        """Test that default path constants are correctly defined.

        Validates that the default directory and output file path constants
        match the expected Streamlit secrets directory structure.
        """
        assert DEFAULT_SECRETS_DIR == Path(".streamlit/secrets")
        assert DEFAULT_OUTPUT_PATH == DEFAULT_SECRETS_DIR / "secrets.toml"
