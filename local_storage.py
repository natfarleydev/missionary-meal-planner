"""Local storage utilities for persisting app state using streamlit-js-eval."""

from __future__ import annotations

import base64
import binascii
import io
import json
import re
from typing import Any

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import structlog

from state_model import AppState

# localStorage key for app data
STORAGE_KEY = "app_data"

# Pattern for data URI validation
_PHOTO_DATA_URI_PATTERN = re.compile(
    r"^data:image/[a-zA-Z0-9]+;base64,[A-Za-z0-9+/=]+$"
)

# Mapping from image kind to MIME type
_IMAGE_KIND_TO_MIME = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "webp": "image/webp",
    "tiff": "image/tiff",
}

log = structlog.get_logger()


def get_app_state_from_local_storage() -> AppState | None | bool:
    """
    Retrieve app state from localStorage.

    Returns:
        AppState | None: The app state object from localStorage, or None if no data exists.

    Raises:
        ValueError: If data exists but is invalid JSON.
    """

    try:
        # Retrieve the JSON string from localStorage
        js_expression = f"localStorage.getItem('{STORAGE_KEY}') ?? false"
        log.info("Retrieving app state from localStorage", js_expression=js_expression)
        json_string = streamlit_js_eval(
            js_expressions=js_expression, key="get_app_data"
        )
        log.info("Retrieved app state from localStorage", json_string=json_string)

        if not json_string:
            log.info("No app state found in localStorage", json_string=json_string)
            return None
        # Parse the JSON string
        app_state_dict = json.loads(json_string)
        log.info("Parsed app state from localStorage", app_state_dict=app_state_dict)

        # Create and return AppState object
        app_state = AppState.model_validate(app_state_dict)
        log.info("Created AppState object from localStorage", app_state=app_state)

        st.success("✅ Saved data restored!")

    except (json.JSONDecodeError, TypeError):
        st.exception("❌ Error retrieving app state from localStorage")
        raise
    except Exception as e:
        st.error(f"❌ Error retrieving data from localStorage: {e}")
        raise ValueError("Error retrieving data from localStorage") from e
    else:
        return app_state


def save_app_state_to_local_storage(app_state: AppState) -> None:
    """
    Save app state to localStorage.

    Args:
        app_state: The AppState object to save.

    Raises:
        ValueError: If the app state cannot be serialized or saved.
    """
    try:
        # Convert the AppState to a JSON string
        app_state_dict = app_state.model_dump_json(exclude_none=False)

        # Save to localStorage
        js_expression = f"localStorage.setItem('{STORAGE_KEY}', '{app_state_dict}')"
        streamlit_js_eval(js_expressions=js_expression, key="save_app_data")

    except (TypeError, ValueError) as e:
        raise ValueError("Error serializing app state") from e
    except Exception as e:
        raise ValueError("Error saving data to localStorage") from e


def _normalize_photo_fields(payload: Any) -> None:
    if not isinstance(payload, dict):
        return

    companionships = payload.get("companionships_data")
    if not isinstance(companionships, list):
        return

    for companionship in companionships:
        if not isinstance(companionship, dict):
            continue

        missionaries = companionship.get("missionaries")
        if not isinstance(missionaries, list):
            continue

        for missionary in missionaries:
            if not isinstance(missionary, dict):
                continue

            missionary["photo"] = _coerce_photo_value(missionary.get("photo"))


def _coerce_photo_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    if not stripped:
        return None

    if _PHOTO_DATA_URI_PATTERN.fullmatch(stripped):
        return stripped

    try:
        decoded = base64.b64decode(stripped, validate=True)
    except (binascii.Error, ValueError):
        return None

    mime_type = _guess_mime_type(decoded)
    if mime_type is None:
        return None

    encoded = base64.b64encode(decoded).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _guess_mime_type(data: bytes) -> str | None:
    try:
        from PIL import Image
        with io.BytesIO(data) as f:
            img = Image.open(f)
            format_name = img.format.lower() if img.format else None
            if format_name:
                return _IMAGE_KIND_TO_MIME.get(format_name)
    except Exception:
        pass
    return None
