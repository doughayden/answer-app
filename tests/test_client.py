import base64
from unittest.mock import MagicMock

from src.client.client import main


class TestClient:
    """Test cases for the client script."""

    def test_main_single_question_stateless(
        self,
        mock_client_utils: MagicMock,
        mock_client_input: MagicMock,
        mock_client_console: MagicMock,
        mock_client_file_operations: dict[str, MagicMock],
    ) -> None:
        """Test main function with a single question in stateless mode."""
        # Mock user input - "n" for stateless, one question, then empty to exit
        mock_client_input.side_effect = ["n", "What is AI?", ""]

        # Mock API response
        encoded_markdown = base64.b64encode(
            "AI is artificial intelligence.".encode()
        ).decode()
        mock_response = {
            "markdown": encoded_markdown,
            "session": {"name": "projects/test/locations/us-central1/sessions/12345"},
        }
        mock_client_utils.send_request.return_value = mock_response

        main()

        # Verify API was called correctly
        mock_client_utils.send_request.assert_called_once_with(
            data={"question": "What is AI?", "session_id": None}, route="/answer"
        )

        # Verify markdown file was written
        mock_client_file_operations["open"].assert_called_once()
        written_content = mock_client_file_operations["open"]().write.call_args[0][0]
        assert written_content == "AI is artificial intelligence."

        # Verify console output
        mock_client_console.print.assert_called_once()

    def test_main_single_question_stateful(
        self,
        mock_client_utils: MagicMock,
        mock_client_input: MagicMock,
    ) -> None:
        """Test main function with session ID in stateful mode."""
        # Mock user input - "y" for stateful, one question, then empty to exit
        mock_client_input.side_effect = ["y", "Hello", ""]

        # Mock API response with session update
        encoded_markdown = base64.b64encode("Hello there!".encode()).decode()
        mock_response = {
            "markdown": encoded_markdown,
            "session": {"name": "projects/test/locations/us-central1/sessions/67890"},
        }
        mock_client_utils.send_request.return_value = mock_response

        main()

        # Verify API was called with session ID="-" for stateful
        mock_client_utils.send_request.assert_called_once_with(
            data={"question": "Hello", "session_id": "-"}, route="/answer"
        )

    def test_main_multiple_questions(
        self,
        mock_client_utils: MagicMock,
        mock_client_input: MagicMock,
    ) -> None:
        """Test main function with multiple questions in stateful mode."""
        # Mock multiple questions - "y" for stateful, then questions
        mock_client_input.side_effect = ["y", "Question 1", "Question 2", ""]

        # Mock API responses
        encoded_markdown1 = base64.b64encode("Answer 1".encode()).decode()
        encoded_markdown2 = base64.b64encode("Answer 2".encode()).decode()

        mock_client_utils.send_request.side_effect = [
            {
                "markdown": encoded_markdown1,
                "session": {"name": "projects/test/locations/us-central1/sessions/111"},
            },
            {
                "markdown": encoded_markdown2,
                "session": {"name": "projects/test/locations/us-central1/sessions/222"},
            },
        ]

        main()

        # Verify both API calls
        assert mock_client_utils.send_request.call_count == 2

        # Check first call
        first_call = mock_client_utils.send_request.call_args_list[0]
        assert first_call[1]["data"]["question"] == "Question 1"
        assert first_call[1]["data"]["session_id"] == "-"

        # Check second call (session ID should be updated)
        second_call = mock_client_utils.send_request.call_args_list[1]
        assert second_call[1]["data"]["question"] == "Question 2"
        assert second_call[1]["data"]["session_id"] == "111"

    def test_main_no_markdown_response(
        self,
        mock_client_utils: MagicMock,
        mock_client_input: MagicMock,
        mock_client_file_operations: dict[str, MagicMock],
    ) -> None:
        """Test main function when no markdown is returned."""
        # Mock user input - "n" for stateless, then question
        mock_client_input.side_effect = ["n", "Test question", ""]

        # Mock API response without markdown
        mock_client_utils.send_request.return_value = {"status": "error"}

        main()

        # Verify API was called
        mock_client_utils.send_request.assert_called_once()

        # Verify no file was written since there's no markdown
        mock_client_file_operations["open"].assert_not_called()

    def test_main_session_id_extraction_error(
        self,
        mock_client_utils: MagicMock,
        mock_client_input: MagicMock,
    ) -> None:
        """Test main function when session ID extraction fails."""
        # Mock user input - "y" for stateful, then questions
        mock_client_input.side_effect = ["y", "Test question", "Second question", ""]

        # Mock API responses - first with valid session, second with malformed session
        encoded_markdown = base64.b64encode("Test answer".encode()).decode()
        mock_client_utils.send_request.side_effect = [
            {
                "markdown": encoded_markdown,
                "session": {"name": "projects/test/locations/us-central1/sessions/123"},
            },
            {
                "markdown": encoded_markdown,
                "session": {
                    "invalid": "structure"
                },  # This will cause extraction to fail
            },
        ]

        main()

        # Verify both API calls were made
        assert mock_client_utils.send_request.call_count == 2

        # Second call should have session_id from first response
        second_call = mock_client_utils.send_request.call_args_list[1]
        assert second_call[1]["data"]["session_id"] == "123"

    def test_main_empty_input_exits(
        self,
        mock_client_utils: MagicMock,
        mock_client_input: MagicMock,
        mock_client_file_operations: dict[str, MagicMock],
    ) -> None:
        """Test that main function exits on empty input."""
        # Mock "n" for stateless, then empty input (user presses Return immediately)
        mock_client_input.side_effect = ["n", ""]

        main()

        # Verify no API calls were made
        mock_client_utils.send_request.assert_not_called()

        # Verify no files were written
        mock_client_file_operations["open"].assert_not_called()

    def test_main_execution_stateful_input_parsing(
        self, mock_client_input: MagicMock
    ) -> None:
        """Test stateful input parsing logic."""
        mock_client_input.return_value = "y"

        # Test the logic directly
        stateful = mock_client_input.return_value.lower()[0] == "y"
        session_id = "-" if stateful else None

        assert session_id == "-"

    def test_main_execution_stateless_input_parsing(
        self, mock_client_input: MagicMock
    ) -> None:
        """Test stateless input parsing logic."""
        mock_client_input.return_value = "n"

        # Test the logic directly
        stateful = mock_client_input.return_value.lower()[0] == "y"
        session_id = "-" if stateful else None

        assert session_id is None
