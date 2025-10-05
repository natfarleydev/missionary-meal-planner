from __future__ import annotations

import binascii

import streamlit as st

from photo_state import PhotoState, get_photo_state
from photo_upload import handle_photo_upload
from utils import photo_data_uri_to_bytes


def main() -> None:
    """Minimal app that renders a single missionary photo section.

    This isolates the photo upload/preview logic for E2E testing without
    other widgets (e.g., segmented controls) that complicate test harness state.
    """
    st.title("Photo Section Demo")

    photo_path = "/companionships_data/0/missionaries/0/photo"
    uploader_key = (
        "#component/companionships_data/0/missionaries/0/photo_uploader"
    )

    value = st.session_state.get(photo_path)
    state = get_photo_state(value)

    if state is PhotoState.READY and isinstance(value, str):
        try:
            photo_data_uri_to_bytes(value)
        except (binascii.Error, ValueError):
            st.warning("Saved photo data is invalid. Please upload a new image.")
            st.session_state[photo_path] = None
            st.rerun()
            return

        st.markdown(
            f"<img src=\"{value}\" alt=\"Preview\" style=\"width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #ddd;\" />",
            unsafe_allow_html=True,
        )
        if st.button("🗑️ Delete photo", key="delete_photo_0_0"):
            st.session_state[photo_path] = ""
            st.rerun()
    else:
        st.file_uploader(
            "Photo (optional)",
            type=["png", "jpg", "jpeg", "gif", "webp"],
            key=uploader_key,
            on_change=handle_photo_upload,
            args=(photo_path, uploader_key),
        )


if __name__ == "__main__":
    main()
