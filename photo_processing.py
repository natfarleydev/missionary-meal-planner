"""Photo processing helpers using PyFaceCrop's simple API."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import TYPE_CHECKING, Final

import cv2
import numpy as np
from PyFaceCrop.face_crop import FaceCrop

if TYPE_CHECKING:
    import streamlit as st

from utils import guess_image_mime_type, read_uploaded_file_bytes


class PhotoProcessingError(Exception):
    """Base error raised when cropping a photo fails."""


class UnsupportedImageTypeError(PhotoProcessingError):
    """Raised when an uploaded file is not a supported image type."""


class VideoEncodingError(PhotoProcessingError):
    """Raised when a temporary video cannot be created."""


class ImageDecodingError(PhotoProcessingError):
    """Raised when the uploaded bytes cannot be decoded into an image."""


@dataclass(frozen=True)
class ProcessedPhoto:
    """High-level result describing the processed photo."""

    data_uri: str
    mime_type: str
    cropped: bool


_DEFAULT_PADDING: Final[int] = 240
_FALLBACK_MIME: Final[str] = "image/jpeg"
_VIDEO_FOURCC: Final[int] = cv2.VideoWriter_fourcc(*"mp4v")


def process_uploaded_photo(
    uploaded_file: st.UploadedFile, *, padding: int = _DEFAULT_PADDING
) -> ProcessedPhoto:
    """Process an uploaded file, returning a data URI of the cropped photo."""

    mime_type = guess_image_mime_type(uploaded_file)
    if mime_type is None:
        raise UnsupportedImageTypeError(
            "Uploaded file must be an image (PNG, JPG, JPEG, GIF, WEBP)"
        )

    image_bytes = read_uploaded_file_bytes(uploaded_file)
    image = _bytes_to_image(image_bytes)

    with (
        tempfile.TemporaryDirectory() as root_dir,
        tempfile.TemporaryDirectory() as dest_dir,
    ):
        video_path = Path(root_dir) / "uploaded.mp4"
        _write_single_frame_video(video_path, image)

        face_cropper = FaceCrop(
            root_dir, dest_dir, interval_seconds=0, padding=max(padding, 0)
        )
        face_cropper.generate()

        cropped_bytes = _read_first_cropped_image(Path(dest_dir), video_path.stem)

    if cropped_bytes is None:
        payload = base64.b64encode(image_bytes).decode("utf-8")
        return ProcessedPhoto(f"data:{mime_type};base64,{payload}", mime_type, False)

    payload = base64.b64encode(cropped_bytes).decode("utf-8")
    return ProcessedPhoto(
        f"data:{_FALLBACK_MIME};base64,{payload}",
        _FALLBACK_MIME,
        True,
    )


def _bytes_to_image(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    if array.size == 0:
        raise ImageDecodingError("Image bytes are empty")

    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ImageDecodingError("Unable to decode image bytes")
    return image


def _write_single_frame_video(path: Path, image: np.ndarray) -> None:
    height, width = image.shape[:2]
    writer = cv2.VideoWriter(str(path), _VIDEO_FOURCC, 1, (width, height))
    if not writer.isOpened():  # pragma: no cover - depends on system codecs
        raise VideoEncodingError("Unable to create temporary video")

    try:
        # Write at least two frames to help detectors stabilise.
        for _ in range(2):
            writer.write(image)
    finally:
        writer.release()


def _read_first_cropped_image(destination_dir: Path, stem: str) -> bytes | None:
    target_dir = destination_dir / stem
    if not target_dir.exists():
        return None

    candidates = sorted(target_dir.glob("*.jpg"))
    if not candidates:
        return None

    try:
        return candidates[0].read_bytes()
    except OSError:  # pragma: no cover - unlikely but defensive
        return None
