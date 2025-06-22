import logging
from unittest.mock import MagicMock

import pytest

logger = logging.getLogger(__name__)


class TestStreamlitApp:
    """Test cases for Streamlit application functions."""

    def test_log_context(self, mock_streamlit: MagicMock) -> None:
        """Test log_context function."""
        from client.streamlit_app import log_context

        mock_streamlit.context.cookies.to_dict.return_value = {"session": "test"}
        mock_streamlit.context.headers.to_dict.return_value = {"user-agent": "test"}

        log_context()

        mock_streamlit.context.cookies.to_dict.assert_called_once()
        mock_streamlit.context.headers.to_dict.assert_called_once()

    def test_setup_app(self, mock_streamlit: MagicMock) -> None:
        """Test setup_app function."""
        from src.client.streamlit_app import setup_app

        setup_app()

        mock_streamlit.set_page_config.assert_called_once_with(
            page_title="Conversational Search",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        mock_streamlit.title.assert_called_once_with("Answer App")

    @pytest.mark.asyncio
    async def test_get_session_history_success(
        self,
        mock_streamlit: MagicMock,
        mock_streamlit_utils: MagicMock,
    ) -> None:
        """Test get_session_history function with successful response."""
        mock_streamlit_utils.send_request.return_value = {
            "sessions": [
                {"turns": [{"query": {"text": "Test question 1"}}]},
                {"turns": [{"query": {"text": "Test question 2"}}]},
            ]
        }

        from src.client.streamlit_app import get_session_history

        result = await get_session_history()

        mock_streamlit_utils.send_request.assert_called_once_with(
            route="/sessions/", data={"user_id": "test@example.com"}, method="GET"
        )
        assert result == ["Test question 1", "Test question 2"]

    @pytest.mark.asyncio
    async def test_get_session_history_empty(
        self,
        mock_streamlit: MagicMock,
        mock_streamlit_utils: MagicMock,
    ) -> None:
        """Test get_session_history with empty response."""
        mock_streamlit_utils.send_request.return_value = {}

        from src.client.streamlit_app import get_session_history

        result = await get_session_history()

        assert result == []

    def test_display_chat_history(self, mock_streamlit: MagicMock) -> None:
        """Test display_chat_history function."""
        from src.client.streamlit_app import display_chat_history

        mock_streamlit.session_state = {
            "chat_history": [
                {"type": "user", "content": "Hello"},
                {"type": "assistant", "content": "Hi there!"},
            ],
            "avatars": {"user": "🦖", "assistant": "🤖"},
        }

        display_chat_history()

        assert mock_streamlit.chat_message.call_count == 2

    @pytest.mark.asyncio
    async def test_send_feedback_positive(
        self,
        mock_streamlit: MagicMock,
        mock_streamlit_utils: MagicMock,
    ) -> None:
        """Test send_feedback function with positive feedback."""
        mock_streamlit.session_state = {
            "answer_query_token": "token123",
            "question": "Test question",
            "answer_text": "Test answer",
        }
        mock_streamlit_utils.send_request.return_value = {"status": "success"}

        from src.client.streamlit_app import send_feedback

        feedback = {"score": "👍", "text": "Great answer!"}
        await send_feedback(feedback)

        mock_streamlit_utils.send_request.assert_called_once_with(
            route="/feedback",
            data={
                "answer_query_token": "token123",
                "question": "Test question",
                "answer_text": "Test answer",
                "feedback_value": 1,
                "feedback_text": "Great answer!",
            },
            method="POST",
        )
        mock_streamlit.success.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_feedback_negative(
        self,
        mock_streamlit: MagicMock,
        mock_streamlit_utils: MagicMock,
    ) -> None:
        """Test send_feedback with negative feedback."""
        mock_streamlit.session_state = {
            "answer_query_token": "token123",
            "question": "Test question",
            "answer_text": "Test answer",
        }
        mock_streamlit_utils.send_request.return_value = {"status": "success"}

        from src.client.streamlit_app import send_feedback

        feedback = {"score": "👎", "text": "Not helpful"}
        await send_feedback(feedback)

        expected_data = {
            "answer_query_token": "token123",
            "question": "Test question",
            "answer_text": "Test answer",
            "feedback_value": 0,
            "feedback_text": "Not helpful",
        }

        mock_streamlit_utils.send_request.assert_called_once_with(
            route="/feedback", data=expected_data, method="POST"
        )
