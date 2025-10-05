from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import pytest

import photo_processing
from photo_processing import (
    ProcessedPhoto,
    UnsupportedImageTypeError,
    process_uploaded_photo,
)


class MockUpload:
    def __init__(
        self, data: bytes, *, mime_type: str, name: str = "upload.jpg"
    ) -> None:
        self._buffer = BytesIO(data)
        self.type = mime_type
        self.name = name

    def read(self) -> bytes:
        return self._buffer.read()

    def seek(self, position: int) -> None:
        self._buffer.seek(position)


def _encode_image(image: np.ndarray, *, ext: str) -> bytes:
    success, buffer = cv2.imencode(ext, image)
    assert success
    return bytes(buffer)


@pytest.fixture(scope="module")
def sample_face_bytes() -> bytes:
    return Path("face_example.jpg").read_bytes()


class DummyCascade:
    def __init__(self, detections: np.ndarray) -> None:
        self._detections = detections

    def detectMultiScale(self, *_: object, **__: object) -> np.ndarray:  # noqa: N802
        return self._detections


def test_process_uploaded_photo_crops_face(
    sample_face_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    upload = MockUpload(sample_face_bytes, mime_type="image/jpeg", name="face.jpg")

    faces = np.array([[10, 20, 30, 40]], dtype=np.int32)
    eyes = np.array([[5, 5, 10, 10]], dtype=np.int32)

    monkeypatch.setattr(
        photo_processing,
        "_load_classifiers",
        lambda: (DummyCascade(faces), DummyCascade(eyes)),
    )

    result = process_uploaded_photo(upload, padding=0)

    assert isinstance(result, ProcessedPhoto)
    assert result.cropped is True
    assert result.mime_type == "image/jpeg"
    assert result.data_uri.startswith("data:image/jpeg;base64,")

    encoded_bytes = base64.b64decode(result.data_uri.split(",", 1)[1])
    decoded = cv2.imdecode(
        np.frombuffer(encoded_bytes, dtype=np.uint8), cv2.IMREAD_COLOR
    )
    assert decoded is not None
    assert decoded.shape[:2] == (40, 30)


def test_process_uploaded_photo_returns_original_when_no_face_detected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    blank_bytes = _encode_image(blank, ext=".png")
    upload = MockUpload(blank_bytes, mime_type="image/png", name="blank.png")

    monkeypatch.setattr(
        photo_processing,
        "_load_classifiers",
        lambda: (
            DummyCascade(np.empty((0, 4), dtype=np.int32)),
            DummyCascade(np.empty((0, 4), dtype=np.int32)),
        ),
    )

    result = process_uploaded_photo(upload)

    assert result.cropped is False
    assert result.mime_type == "image/png"
    assert result.data_uri.startswith("data:image/png;base64,")
    decoded = base64.b64decode(result.data_uri.split(",", 1)[1])
    assert decoded == blank_bytes


def test_process_uploaded_photo_rejects_non_image() -> None:
    upload = MockUpload(b"not-image", mime_type="application/pdf", name="file.pdf")

    with pytest.raises(UnsupportedImageTypeError):
        process_uploaded_photo(upload)
