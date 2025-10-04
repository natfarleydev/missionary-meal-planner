from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import pytest

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


def test_process_uploaded_photo_crops_face(sample_face_bytes: bytes) -> None:
    upload = MockUpload(sample_face_bytes, mime_type="image/jpeg", name="face.jpg")

    result = process_uploaded_photo(upload)

    assert isinstance(result, ProcessedPhoto)
    assert result.cropped is True
    assert result.mime_type == "image/jpeg"
    assert result.data_uri.startswith("data:image/jpeg;base64,")

    encoded_bytes = base64.b64decode(result.data_uri.split(",", 1)[1])
    assert len(encoded_bytes) < len(sample_face_bytes)


def test_process_uploaded_photo_returns_original_when_no_face_detected() -> None:
    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    blank_bytes = _encode_image(blank, ext=".png")
    upload = MockUpload(blank_bytes, mime_type="image/png", name="blank.png")

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
