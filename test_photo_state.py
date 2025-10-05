from __future__ import annotations

from photo_state import PhotoState, get_photo_state


def test_get_photo_state_classifies_values():
    assert get_photo_state(None) is PhotoState.EMPTY
    assert get_photo_state("") is PhotoState.EMPTY
    assert get_photo_state("   ") is PhotoState.EMPTY
    assert get_photo_state("not-a-data-uri") is PhotoState.INVALID
    assert (
        get_photo_state("data:image/jpeg;base64,aGVsbG8=") is PhotoState.READY
    )
