from __future__ import annotations

import base64
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


pytestmark = pytest.mark.e2e


def _data_uri_for_jpeg(data: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("utf-8")


def test_photo_uploader_visibility_and_preview(tmp_path: Path):
    at = AppTest.from_file("streamlit_app.py")

    # Prime session state to avoid AppTest segmented_control value-type mismatch
    at.session_state["/num_companionships"] = 1
    at.session_state["/missionary_counts/0"] = [2]
    at.session_state[
        "#component/companionships_data/0/missionaries/*/title"
    ] = ["Elders"]

    # First run to build the widget tree
    at.run()

    # Work around AppTest expecting list-valued selection for button groups
    # by normalizing current single selections into lists before the next run.
    for bg in at.button_group:
        current = getattr(bg, "value", None)
        if isinstance(current, (int, str)):
            try:
                bg.set_value([current])
            except Exception:
                pass
    at.run()

    # Locate first missionary photo path
    photo_path = "/companionships_data/0/missionaries/0/photo"

    # Ensure no photo initially
    at.session_state[photo_path] = None
    at.run()

    # When no photo is present, we expect a file_uploader widget exists.
    # AppTest does not expose file_uploader directly, so we rely on its presence in widget tree
    # by querying generic element names and ensuring no preview image markdown is present.
    found_preview = any(
        (
            hasattr(node, "value") and isinstance(node.value, str) and "<img" in node.value
        )
        for node in at.markdown
    )
    assert not found_preview, "Preview should not be shown before upload"

    # Simulate an uploaded image by directly setting the processed data URI in session state
    # (The on_change handler and processing are covered by unit tests.)
    sample = Path("face_example.jpg").read_bytes()
    at.session_state[photo_path] = _data_uri_for_jpeg(sample)
    at.run()

    # Now preview markdown with an <img> tag should be rendered
    found_preview = any(
        (
            hasattr(node, "value") and isinstance(node.value, str) and "<img" in node.value
        )
        for node in at.markdown
    )
    assert found_preview, "Preview should be shown after upload"

    # Click the delete button and expect the uploader to reappear (no preview)
    # Button key is deterministic: delete_photo_{companionship_index}_{missionary_index}
    delete_buttons = [
        b for b in at.button if getattr(b, "key", "").startswith("delete_photo_0_0")
    ]
    assert delete_buttons, "Delete button should be present when preview is shown"
    delete_buttons[0].click().run()

    # After deletion, we should not find the preview image
    found_preview = any(
        (
            hasattr(node, "value") and isinstance(node.value, str) and "<img" in node.value
        )
        for node in at.markdown
    )
    assert not found_preview, "Preview should be hidden after deletion"
