"""Photo upload handling for the Streamlit app.

This module provides functions for handling photo uploads through Streamlit's
file uploader widget, including callback functions and session state management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from photo_processing import (
    UnsupportedImageTypeError,
    process_uploaded_photo,
)

if TYPE_CHECKING:
    from streamlit.runtime.uploaded_file_manager import UploadedFile


def get_uploaded_file_from_session_state(uploader_key: str) -> UploadedFile | None:
    """Retrieve an uploaded file from the session state.

    Args:
        uploader_key: The key of the file uploader widget in session state

    Returns:
        The uploaded file object, or None if no file is present
    """
    return st.session_state.get(uploader_key)


def handle_photo_upload(photo_path: str, uploader_key: str) -> None:
    """Handle photo upload using the file uploader's on_change callback.

    This function is called as a callback when the file uploader changes.
    It retrieves the uploaded file from the session state using the uploader_key,
    processes it, and stores the result in the photo_path.

    Args:
        photo_path: The session state key where the processed photo data URI will be stored
        uploader_key: The key of the file uploader widget to retrieve the uploaded file from
    """
    uploaded_file = get_uploaded_file_from_session_state(uploader_key)

    # If no file is uploaded or file was cleared, do nothing
    if uploaded_file is None:
        return

    try:
        processed = process_uploaded_photo(uploaded_file)
    except UnsupportedImageTypeError as exc:
        st.error(str(exc))
        return
    except (ValueError, TypeError) as exc:
        st.error(f"Error processing uploaded file: {exc}")
        return
    except Exception as exc:
        st.error(f"Unexpected error processing photo: {exc}")
        return

    st.session_state[photo_path] = processed.data_uri
