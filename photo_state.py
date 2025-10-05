"""Pure photo state utilities for deciding UI rendering.

These helpers contain no Streamlit imports so they can be unit tested easily.
"""

from __future__ import annotations

from enum import Enum, auto

from utils import is_valid_photo_data_uri


class PhotoState(Enum):
    EMPTY = auto()
    INVALID = auto()
    READY = auto()


def get_photo_state(photo_value: object) -> PhotoState:
    """Classify a stored photo value into a simple UI state.

    - EMPTY: value is None or blank string
    - INVALID: non-empty string that is not a valid data URI
    - READY: valid data URI string
    """
    if not is_valid_photo_data_uri(photo_value):
        if isinstance(photo_value, str) and photo_value.strip():
            return PhotoState.INVALID
        return PhotoState.EMPTY
    return PhotoState.READY
