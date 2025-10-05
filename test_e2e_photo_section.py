from __future__ import annotations

import base64
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.e2e


def _data_uri_for_jpeg(data: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("utf-8")


def test_photo_section_demo_preview_and_delete():
    at = AppTest.from_file("photo_section_app.py")
    at.run()

    photo_path = "/companionships_data/0/missionaries/0/photo"
    # Initially no preview
    assert not any(
        hasattr(n, "value") and isinstance(n.value, str) and "<img" in n.value
        for n in at.markdown
    )

    # Set a valid data URI and rerun
    sample = Path("face_example.jpg").read_bytes()
    at.session_state[photo_path] = _data_uri_for_jpeg(sample)
    at.run()

    # Preview appears
    assert any(
        hasattr(n, "value") and isinstance(n.value, str) and "<img" in n.value
        for n in at.markdown
    )

    # Click delete and rerun; preview disappears
    [btn] = [b for b in at.button if getattr(b, "key", "") == "delete_photo_0_0"]
    btn.click().run()
    assert not any(
        hasattr(n, "value") and isinstance(n.value, str) and "<img" in n.value
        for n in at.markdown
    )
