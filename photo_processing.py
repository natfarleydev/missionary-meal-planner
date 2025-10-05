"""Photo processing helpers using PyFaceCrop's simple API."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Final

import cv2
import numpy as np
from PyFaceCrop.face_crop import get_haarcascade_path

if TYPE_CHECKING:
    import streamlit as st

from utils import guess_image_mime_type, read_uploaded_file_bytes


class PhotoProcessingError(Exception):
    """Base error raised when cropping a photo fails."""


class UnsupportedImageTypeError(PhotoProcessingError):
    """Raised when an uploaded file is not a supported image type."""


class ImageDecodingError(PhotoProcessingError):
    """Raised when the uploaded bytes cannot be decoded into an image."""


class CascadeLoadingError(PhotoProcessingError):
    """Raised when Haar cascade resources cannot be loaded."""


@dataclass(frozen=True)
class ProcessedPhoto:
    """High-level result describing the processed photo."""

    data_uri: str
    mime_type: str
    cropped: bool


_DEFAULT_PADDING: Final[int] = 240
_FALLBACK_MIME: Final[str] = "image/jpeg"


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

    cropped_bytes = _crop_face_to_bytes(image, padding=max(padding, 0))

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


def _crop_face_to_bytes(image: np.ndarray, padding: int) -> bytes | None:
    try:
        face_cascade, eye_cascade = _load_classifiers()
    except cv2.error as exc:  # pragma: no cover - defensive
        raise CascadeLoadingError("Unable to initialise face detectors") from exc

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    for x, y, w, h in faces:
        roi_gray = gray[y : y + h, x : x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        if len(eyes) == 0:
            continue

        start_x = max(x - padding, 0)
        start_y = max(y - padding, 0)
        end_x = min(x + w + padding, image.shape[1])
        end_y = min(y + h + padding, image.shape[0])

        cropped = image[start_y:end_y, start_x:end_x]
        success, buffer = cv2.imencode(".jpg", cropped)
        if success:
            return bytes(buffer)

    return None


@lru_cache(maxsize=1)
def _load_classifiers() -> tuple[cv2.CascadeClassifier, cv2.CascadeClassifier]:
    try:
        face_path = get_haarcascade_path("haarcascade_frontalface_default.xml")
        eye_path = get_haarcascade_path("haarcascade_eye.xml")
    except (
        FileNotFoundError,
        TypeError,
        ValueError,
    ) as exc:  # pragma: no cover - defensive
        raise CascadeLoadingError("Unable to locate Haar cascade resources") from exc

    face_cascade = cv2.CascadeClassifier(face_path)
    eye_cascade = cv2.CascadeClassifier(eye_path)

    if (
        face_cascade.empty() or eye_cascade.empty()
    ):  # pragma: no cover - depends on cv2 data
        raise CascadeLoadingError("Unable to load Haar cascade resources")

    return face_cascade, eye_cascade
