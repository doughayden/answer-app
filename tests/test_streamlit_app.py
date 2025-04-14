# import logging
# import pytest
# from unittest.mock import MagicMock, patch

# from streamlit.testing.v1 import AppTest

# logger = logging.getLogger(__name__)


# @pytest.fixture
# def mock_utils_streamlit_app():
#     """Mock the utils module in the streamlit_app."""
#     with patch("src.client.streamlit_app.utils") as mock_utils:
#         logger.debug("Mock utils instance in streamlit_app")
#         yield mock_utils


# def test_app(
#     mock_utils_streamlit_app: MagicMock,
# ) -> None:
#     """Test the Streamlit app."""
#     at = AppTest.from_file("../src/client/streamlit_app.py")
#     at.run()
#     logging.debug(at.session_state)

#     assert not at.exception
