"""Unit tests for photo_upload.py module."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from photo_processing import UnsupportedImageTypeError
from photo_upload import get_uploaded_file_from_session_state, handle_photo_upload


class TestHandlePhotoUpload:
    """Test cases for handle_photo_upload function."""

    def test_successful_photo_upload(self):
        """Test successful photo upload and processing."""
        # Arrange
        mock_uploaded_file = Mock()
        mock_processed_photo = Mock()
        mock_processed_photo.data_uri = "data:image/jpeg;base64,processed_image_data"

        mock_get_session_state = Mock(return_value=mock_uploaded_file)
        mock_set_session_state = Mock()

        with patch("photo_upload.process_uploaded_photo", return_value=mock_processed_photo) as mock_process:
            # Act
            handle_photo_upload(
                photo_path="/test/photo",
                uploader_key="test_uploader",
                get_session_state_value=mock_get_session_state,
                set_session_state_value=mock_set_session_state,
            )

            # Assert
            mock_process.assert_called_once_with(mock_uploaded_file)
            mock_set_session_state.assert_called_once_with("/test/photo", "data:image/jpeg;base64,processed_image_data")

    def test_no_file_uploaded_early_return(self):
        """Test that function returns early when no file is uploaded."""
        # Arrange
        mock_get_session_state = Mock(return_value=None)
        mock_set_session_state = Mock()

        # Act
        handle_photo_upload(
            photo_path="/test/photo",
            uploader_key="test_uploader",
            get_session_state_value=mock_get_session_state,
            set_session_state_value=mock_set_session_state,
        )

        # Assert
        mock_get_session_state.assert_called_once_with("test_uploader")
        mock_set_session_state.assert_not_called()

    def test_unsupported_image_type_error_with_handler(self):
        """Test handling of UnsupportedImageTypeError with custom error handler."""
        # Arrange
        mock_uploaded_file = Mock()
        mock_get_session_state = Mock(return_value=mock_uploaded_file)
        mock_set_session_state = Mock()
        mock_error_handler = Mock()

        with patch("photo_upload.process_uploaded_photo", side_effect=UnsupportedImageTypeError("Invalid image type")):
            # Act
            handle_photo_upload(
                photo_path="/test/photo",
                uploader_key="test_uploader",
                get_session_state_value=mock_get_session_state,
                set_session_state_value=mock_set_session_state,
                error_handler=mock_error_handler,
            )

            # Assert
            mock_error_handler.assert_called_once_with("Invalid image type")
            mock_set_session_state.assert_not_called()

    def test_unsupported_image_type_error_without_handler(self):
        """Test that UnsupportedImageTypeError is raised when no error handler provided."""
        # Arrange
        mock_uploaded_file = Mock()
        mock_get_session_state = Mock(return_value=mock_uploaded_file)
        mock_set_session_state = Mock()

        with patch("photo_upload.process_uploaded_photo", side_effect=UnsupportedImageTypeError("Invalid image type")):
            # Act & Assert
            with pytest.raises(UnsupportedImageTypeError, match="Invalid image type"):
                handle_photo_upload(
                    photo_path="/test/photo",
                    uploader_key="test_uploader",
                    get_session_state_value=mock_get_session_state,
                    set_session_state_value=mock_set_session_state,
                )

            mock_set_session_state.assert_not_called()

    def test_value_error_with_handler(self):
        """Test handling of ValueError with custom error handler."""
        # Arrange
        mock_uploaded_file = Mock()
        mock_get_session_state = Mock(return_value=mock_uploaded_file)
        mock_set_session_state = Mock()
        mock_error_handler = Mock()

        with patch("photo_upload.process_uploaded_photo", side_effect=ValueError("Processing failed")):
            # Act
            handle_photo_upload(
                photo_path="/test/photo",
                uploader_key="test_uploader",
                get_session_state_value=mock_get_session_state,
                set_session_state_value=mock_set_session_state,
                error_handler=mock_error_handler,
            )

            # Assert
            mock_error_handler.assert_called_once_with("Error processing uploaded file: Processing failed")
            mock_set_session_state.assert_not_called()

    def test_type_error_with_handler(self):
        """Test handling of TypeError with custom error handler."""
        # Arrange
        mock_uploaded_file = Mock()
        mock_get_session_state = Mock(return_value=mock_uploaded_file)
        mock_set_session_state = Mock()
        mock_error_handler = Mock()

        with patch("photo_upload.process_uploaded_photo", side_effect=TypeError("Type error")):
            # Act
            handle_photo_upload(
                photo_path="/test/photo",
                uploader_key="test_uploader",
                get_session_state_value=mock_get_session_state,
                set_session_state_value=mock_set_session_state,
                error_handler=mock_error_handler,
            )

            # Assert
            mock_error_handler.assert_called_once_with("Error processing uploaded file: Type error")
            mock_set_session_state.assert_not_called()

    def test_generic_exception_with_handler(self):
        """Test handling of generic Exception with custom error handler."""
        # Arrange
        mock_uploaded_file = Mock()
        mock_get_session_state = Mock(return_value=mock_uploaded_file)
        mock_set_session_state = Mock()
        mock_error_handler = Mock()

        with patch("photo_upload.process_uploaded_photo", side_effect=Exception("Unexpected error")):
            # Act
            handle_photo_upload(
                photo_path="/test/photo",
                uploader_key="test_uploader",
                get_session_state_value=mock_get_session_state,
                set_session_state_value=mock_set_session_state,
                error_handler=mock_error_handler,
            )

            # Assert
            mock_error_handler.assert_called_once_with("Unexpected error processing photo: Unexpected error")
            mock_set_session_state.assert_not_called()

    def test_generic_exception_without_handler(self):
        """Test that generic Exception is raised when no error handler provided."""
        # Arrange
        mock_uploaded_file = Mock()
        mock_get_session_state = Mock(return_value=mock_uploaded_file)
        mock_set_session_state = Mock()

        with patch("photo_upload.process_uploaded_photo", side_effect=Exception("Unexpected error")):
            # Act & Assert
            with pytest.raises(Exception, match="Unexpected error"):
                handle_photo_upload(
                    photo_path="/test/photo",
                    uploader_key="test_uploader",
                    get_session_state_value=mock_get_session_state,
                    set_session_state_value=mock_set_session_state,
                )

            mock_set_session_state.assert_not_called()


class TestGetUploadedFileFromSessionState:
    """Test cases for get_uploaded_file_from_session_state function."""

    def test_successful_file_retrieval(self):
        """Test successful retrieval of uploaded file from session state."""
        # Arrange
        mock_uploaded_file = Mock()
        mock_get_session_state = Mock(return_value=mock_uploaded_file)

        # Act
        result = get_uploaded_file_from_session_state(
            uploader_key="test_uploader",
            get_session_state_value=mock_get_session_state,
        )

        # Assert
        assert result is mock_uploaded_file
        mock_get_session_state.assert_called_once_with("test_uploader")

    def test_file_not_found_returns_none(self):
        """Test that None is returned when no file exists in session state."""
        # Arrange
        mock_get_session_state = Mock(return_value=None)

        # Act
        result = get_uploaded_file_from_session_state(
            uploader_key="test_uploader",
            get_session_state_value=mock_get_session_state,
        )

        # Assert
        assert result is None
        mock_get_session_state.assert_called_once_with("test_uploader")
