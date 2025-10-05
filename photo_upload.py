"""Photo upload functionality for the Missionary Meal Planner application.

This module provides functions for handling photo uploads, processing uploaded files,
and retrieving uploaded files from session state. It separates the photo upload logic
from the Streamlit UI code for better testability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from photo_processing import (
    UnsupportedImageTypeError,
    process_uploaded_photo,
)


def handle_photo_upload(
    photo_path: str,
    uploader_key: str,
    get_session_state_value: Callable[[str], Any],
    set_session_state_value: Callable[[str, Any], None],
    error_handler: Callable[[str], None] | None = None,
) -> None:
    """Handle photo upload by processing the uploaded file and storing the result.

    This function retrieves an uploaded file from session state using the uploader_key,
    processes it using the photo processing pipeline, and stores the processed result
    in the photo_path location in session state.

    Args:
        photo_path: The session state key where the processed photo data URI will be stored
        uploader_key: The key of the file uploader widget to retrieve the uploaded file from
        get_session_state_value: Function to get a value from session state
        set_session_state_value: Function to set a value in session state
        error_handler: Optional function to handle errors (receives error message as string)
    """
    uploaded_file = get_session_state_value(uploader_key)

    # If no file is uploaded or file was cleared, do nothing
    if uploaded_file is None:
        return

    try:
        processed = process_uploaded_photo(uploaded_file)
        set_session_state_value(photo_path, processed.data_uri)
    except UnsupportedImageTypeError as exc:
        error_msg = str(exc)
        if error_handler:
            error_handler(error_msg)
        else:
            raise
    except (ValueError, TypeError) as exc:
        error_msg = f"Error processing uploaded file: {exc}"
        if error_handler:
            error_handler(error_msg)
        else:
            raise
    except Exception as exc:
        error_msg = f"Unexpected error processing photo: {exc}"
        if error_handler:
            error_handler(error_msg)
        else:
            raise


def get_uploaded_file_from_session_state(
    uploader_key: str,
    get_session_state_value: Callable[[str], Any],
) -> Any:
    """Retrieve an uploaded file from session state.

    Args:
        uploader_key: The key of the file uploader widget
        get_session_state_value: Function to get a value from session state

    Returns:
        The uploaded file object from session state, or None if not found
    """
    return get_session_state_value(uploader_key)
