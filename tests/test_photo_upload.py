import types
import pytest

import photo_upload


class ErrorRecorder:
    def __init__(self):
        self.messages = []

    def __call__(self, msg: str) -> None:
        self.messages.append(str(msg))


def test_get_uploaded_file_from_session_state_returns_value():
    fake_file = object()
    state = {"uploader": fake_file}
    got = photo_upload.get_uploaded_file_from_session_state(
        "uploader", session_state=state
    )
    assert got is fake_file


def test_get_uploaded_file_from_session_state_missing_returns_none():
    got = photo_upload.get_uploaded_file_from_session_state(
        "missing", session_state={}
    )
    assert got is None


def test_handle_photo_upload_sets_state_on_success(monkeypatch):
    state = {"uploader": object()}
    recorder = ErrorRecorder()

    def fake_processor(uploaded_file):
        assert uploaded_file is state["uploader"]
        return types.SimpleNamespace(data_uri="data:image/png;base64,AAAA")

    monkeypatch.setattr(photo_upload, "process_uploaded_photo", fake_processor)

    photo_upload.handle_photo_upload(
        "photo_state", "uploader", session_state=state, error=recorder
    )

    assert state["photo_state"] == "data:image/png;base64,AAAA"
    assert recorder.messages == []


def test_handle_photo_upload_no_file_does_nothing(monkeypatch):
    state = {}
    recorder = ErrorRecorder()

    # Should not be called, but provide a stub anyway
    monkeypatch.setattr(
        photo_upload, "process_uploaded_photo", lambda uploaded_file: None
    )

    photo_upload.handle_photo_upload(
        "photo_state", "uploader", session_state=state, error=recorder
    )

    assert "photo_state" not in state
    assert recorder.messages == []


def test_handle_photo_upload_reports_unsupported_image_type(monkeypatch):
    state = {"uploader": object()}
    recorder = ErrorRecorder()

    def raiser(_):  # noqa: ANN001
        raise photo_upload.UnsupportedImageTypeError("bad type")

    monkeypatch.setattr(photo_upload, "process_uploaded_photo", raiser)

    photo_upload.handle_photo_upload(
        "photo_state", "uploader", session_state=state, error=recorder
    )

    assert "photo_state" not in state
    assert recorder.messages and "bad type" in recorder.messages[0]


def test_handle_photo_upload_reports_value_error(monkeypatch):
    state = {"uploader": object()}
    recorder = ErrorRecorder()

    def raiser(_):  # noqa: ANN001
        raise ValueError("boom")

    monkeypatch.setattr(photo_upload, "process_uploaded_photo", raiser)

    photo_upload.handle_photo_upload(
        "photo_state", "uploader", session_state=state, error=recorder
    )

    assert "photo_state" not in state
    assert recorder.messages and "boom" in recorder.messages[0]


def test_handle_photo_upload_reports_generic_exception(monkeypatch):
    state = {"uploader": object()}
    recorder = ErrorRecorder()

    def raiser(_):  # noqa: ANN001
        raise RuntimeError("kaboom")

    monkeypatch.setattr(photo_upload, "process_uploaded_photo", raiser)

    photo_upload.handle_photo_upload(
        "photo_state", "uploader", session_state=state, error=recorder
    )

    assert "photo_state" not in state
    assert recorder.messages and "kaboom" in recorder.messages[0]
