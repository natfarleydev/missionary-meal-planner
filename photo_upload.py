"""Photo upload orchestration for Streamlit, extracted for testability.

This module provides a thin layer between Streamlit widgets and the
`photo_processing` helpers. Functions are designed to accept injectable
dependencies (session state mapping and error reporter) to enable unit tests
without requiring a Streamlit runtime.
"""

from __future__ import annotations

from typing import Any, Callable, MutableMapping

# Avoid importing heavy dependencies (e.g. OpenCV via photo_processing) at module
# import time to keep tests lightweight. Provide lazy-imported fallbacks and
# module-level names for easy monkeypatching in tests.


class UploadedImageError(Exception):
    """Fallback base error for image upload issues.

    Used when real exceptions from `photo_processing` are not imported.
    """


# Exposed names that tests can monkeypatch without importing heavy deps
process_uploaded_photo: Any | None = None
UnsupportedImageTypeError: type[Exception] = UploadedImageError


def _get_streamlit():
    # Lazy import to avoid heavyweight dependencies during test collection
    import streamlit as st  # type: ignore

    return st


def get_uploaded_file_from_session_state(
    uploader_key: str,
    *,
    session_state: MutableMapping[str, Any] | None = None,
) -> Any | None:
    """Return the uploaded file-like object stored by Streamlit.

    This helper exists to isolate direct access to `st.session_state` and makes
    it easy to unit test logic by injecting a plain dict in place of the real
    Streamlit session state mapping.
    """
    state = (
        session_state if session_state is not None else _get_streamlit().session_state
    )
    return state.get(uploader_key)


def handle_photo_upload(
    photo_state_key: str,
    uploader_key: str,
    *,
    session_state: MutableMapping[str, Any] | None = None,
    error: Callable[[str], None] | None = None,
) -> None:
    """Callback to process an uploaded file and store the photo data URI.

    Intended to be used as `on_change` for a `st.file_uploader`:

        st.file_uploader(
            ..., key=uploader_key, on_change=handle_photo_upload,
            args=(photo_state_key, uploader_key)
        )
    """

    # Determine state mapping lazily to avoid importing Streamlit when injected
    if session_state is None:
        st = _get_streamlit()
        state = st.session_state
    else:
        st = None  # type: ignore[assignment]
        state = session_state

    # Determine error reporter lazily
    if error is None:
        if st is None:
            st = _get_streamlit()
        report_error = st.error  # type: ignore[assignment]
    else:
        report_error = error

    uploaded_file = get_uploaded_file_from_session_state(uploader_key, session_state=state)

    # If no file is uploaded or file was cleared, do nothing
    if uploaded_file is None:
        return

    # Resolve processing function and specific error lazily to avoid importing
    # heavy dependencies during test collection.
    _process = process_uploaded_photo
    _unsupported_err = UnsupportedImageTypeError
    if _process is None or _unsupported_err is UploadedImageError:
        from photo_processing import (
            process_uploaded_photo as _real_process,
            UnsupportedImageTypeError as _real_unsupported,
        )

        _process = _real_process
        _unsupported_err = _real_unsupported

    try:
        processed = _process(uploaded_file)
    except _unsupported_err as exc:  # type: ignore[misc]
        report_error(str(exc))
        return
    except (ValueError, TypeError) as exc:
        report_error(f"Error processing uploaded file: {exc}")
        return
    except Exception as exc:  # pragma: no cover - defensive
        report_error(f"Unexpected error processing photo: {exc}")
        return

    state[photo_state_key] = processed.data_uri
