"""Unit tests for photo_upload module."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from photo_processing import ProcessedPhoto
from photo_upload import get_uploaded_file_from_session_state, handle_photo_upload


class MockUploadedFile:
    """Mock for Streamlit's UploadedFile."""

    def __init__(
        self, data: bytes, *, mime_type: str, name: str = "upload.jpg"
    ) -> None:
        self._buffer = BytesIO(data)
        self.type = mime_type
        self.name = name

    def read(self) -> bytes:
        return self._buffer.read()

    def seek(self, position: int) -> None:
        self._buffer.seek(position)


@pytest.fixture(scope="module")
def sample_face_bytes() -> bytes:
    """Load sample face image for testing."""
    return Path("face_example.jpg").read_bytes()


@pytest.fixture
def mock_session_state():
    """Create a mock session state."""
    return {}


def test_get_uploaded_file_from_session_state_returns_file(mock_session_state):
    """Test that get_uploaded_file_from_session_state returns file when present."""
    mock_file = MockUploadedFile(b"test", mime_type="image/png")
    mock_session_state["uploader_key"] = mock_file

    with patch("photo_upload.st.session_state", mock_session_state):
        result = get_uploaded_file_from_session_state("uploader_key")

    assert result == mock_file


def test_get_uploaded_file_from_session_state_returns_none_when_missing(
    mock_session_state,
):
    """Test that get_uploaded_file_from_session_state returns None when key missing."""
    with patch("photo_upload.st.session_state", mock_session_state):
        result = get_uploaded_file_from_session_state("nonexistent_key")

    assert result is None


def test_handle_photo_upload_clears_state_when_no_file(mock_session_state):
    """Test that handle_photo_upload clears state when no file is uploaded."""
    # Pre-populate with existing data
    mock_session_state["/photo_path"] = "data:image/jpeg;base64,existing"
    mock_session_state["uploader_key_last_processed"] = "old_file.jpg"

    with patch("photo_upload.st.session_state", mock_session_state):
        handle_photo_upload("/photo_path", "uploader_key")

    assert mock_session_state["/photo_path"] is None
    assert mock_session_state["uploader_key_last_processed"] is None


def test_handle_photo_upload_processes_valid_image(
    mock_session_state, sample_face_bytes
):
    """Test that handle_photo_upload successfully processes a valid image."""
    mock_file = MockUploadedFile(
        sample_face_bytes, mime_type="image/jpeg", name="test.jpg"
    )
    mock_session_state["uploader_key"] = mock_file

    with patch("photo_upload.st.session_state", mock_session_state):
        handle_photo_upload("/photo_path", "uploader_key")

    assert "/photo_path" in mock_session_state
    assert mock_session_state["/photo_path"].startswith("data:image/jpeg;base64,")
    assert mock_session_state["uploader_key_last_processed"] == "test.jpg"


def test_handle_photo_upload_skips_already_processed_file(
    mock_session_state, sample_face_bytes
):
    """Test that handle_photo_upload skips processing if file already processed."""
    mock_file = MockUploadedFile(
        sample_face_bytes, mime_type="image/jpeg", name="test.jpg"
    )
    mock_session_state["uploader_key"] = mock_file
    mock_session_state["uploader_key_last_processed"] = "test.jpg"
    mock_session_state["/photo_path"] = "data:image/jpeg;base64,existing"

    initial_photo = mock_session_state["/photo_path"]

    with patch("photo_upload.st.session_state", mock_session_state):
        handle_photo_upload("/photo_path", "uploader_key")

    # Photo should not be reprocessed
    assert mock_session_state["/photo_path"] == initial_photo


def test_handle_photo_upload_handles_unsupported_image_type(mock_session_state):
    """Test that handle_photo_upload handles UnsupportedImageTypeError gracefully."""
    mock_file = MockUploadedFile(
        b"not-an-image", mime_type="application/pdf", name="test.pdf"
    )
    mock_session_state["uploader_key"] = mock_file

    mock_st = MagicMock()
    mock_st.session_state = mock_session_state

    with patch("photo_upload.st", mock_st):
        handle_photo_upload("/photo_path", "uploader_key")

    # Error should be displayed
    mock_st.error.assert_called_once()
    # Photo path should be cleared
    assert mock_session_state["/photo_path"] is None


def test_handle_photo_upload_handles_value_error(mock_session_state, sample_face_bytes):
    """Test that handle_photo_upload handles ValueError gracefully."""
    mock_file = MockUploadedFile(
        sample_face_bytes, mime_type="image/jpeg", name="test.jpg"
    )
    mock_session_state["uploader_key"] = mock_file

    mock_st = MagicMock()
    mock_st.session_state = mock_session_state

    with (
        patch("photo_upload.st", mock_st),
        patch(
            "photo_upload.process_uploaded_photo",
            side_effect=ValueError("Test error"),
        ),
    ):
        handle_photo_upload("/photo_path", "uploader_key")

    # Error should be displayed with proper message
    mock_st.error.assert_called_once()
    assert "Error processing uploaded file" in str(mock_st.error.call_args)
    # Photo path should be cleared
    assert mock_session_state["/photo_path"] is None


def test_handle_photo_upload_handles_type_error(mock_session_state, sample_face_bytes):
    """Test that handle_photo_upload handles TypeError gracefully."""
    mock_file = MockUploadedFile(
        sample_face_bytes, mime_type="image/jpeg", name="test.jpg"
    )
    mock_session_state["uploader_key"] = mock_file

    mock_st = MagicMock()
    mock_st.session_state = mock_session_state

    with (
        patch("photo_upload.st", mock_st),
        patch(
            "photo_upload.process_uploaded_photo",
            side_effect=TypeError("Test type error"),
        ),
    ):
        handle_photo_upload("/photo_path", "uploader_key")

    # Error should be displayed with proper message
    mock_st.error.assert_called_once()
    assert "Error processing uploaded file" in str(mock_st.error.call_args)
    # Photo path should be cleared
    assert mock_session_state["/photo_path"] is None


def test_handle_photo_upload_handles_generic_exception(
    mock_session_state, sample_face_bytes
):
    """Test that handle_photo_upload handles generic exceptions gracefully."""
    mock_file = MockUploadedFile(
        sample_face_bytes, mime_type="image/jpeg", name="test.jpg"
    )
    mock_session_state["uploader_key"] = mock_file

    mock_st = MagicMock()
    mock_st.session_state = mock_session_state

    with (
        patch("photo_upload.st", mock_st),
        patch(
            "photo_upload.process_uploaded_photo",
            side_effect=RuntimeError("Unexpected error"),
        ),
    ):
        handle_photo_upload("/photo_path", "uploader_key")

    # Error should be displayed with proper message
    mock_st.error.assert_called_once()
    assert "Unexpected error processing photo" in str(mock_st.error.call_args)
    # Photo path should be cleared
    assert mock_session_state["/photo_path"] is None


def test_handle_photo_upload_stores_data_uri_on_success(
    mock_session_state, sample_face_bytes
):
    """Test that handle_photo_upload stores the data URI in session state on success."""
    mock_file = MockUploadedFile(
        sample_face_bytes, mime_type="image/jpeg", name="test.jpg"
    )
    mock_session_state["uploader_key"] = mock_file

    expected_data_uri = "data:image/jpeg;base64,abc123"
    mock_processed = ProcessedPhoto(
        data_uri=expected_data_uri, cropped=True, mime_type="image/jpeg"
    )

    mock_st = MagicMock()
    mock_st.session_state = mock_session_state

    with (
        patch("photo_upload.st", mock_st),
        patch("photo_upload.process_uploaded_photo", return_value=mock_processed),
    ):
        handle_photo_upload("/photo_path", "uploader_key")

    # Data URI should be stored in session state
    assert mock_session_state["/photo_path"] == expected_data_uri
    assert mock_session_state["uploader_key_last_processed"] == "test.jpg"
