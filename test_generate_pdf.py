"""Tests for the PDF generation utilities."""

import base64

import pytest

from generate_pdf import generate_meal_planner_pdf, pdf_bytes_to_base64
from state_model import AppState, Companionship, Missionary


class TestGenerateMealPlannerPdf:
    """Tests for the PDF generation helper."""

    def test_pdf_generation_from_valid_app_state(self):
        """The helper should emit a PDF payload for a fully populated state."""

        missionary = Missionary(title="Elder", name="Smith", photo=None)
        companionship = Companionship(
            missionaries=[missionary],
            phone_number="555-1234",
        )

        app_state = AppState(
            num_companionships=1,
            companionships_data=[companionship],
            missionary_counts=[1],
            generated_pdf="",
        )

        pdf_bytes = generate_meal_planner_pdf(app_state)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")


class TestPdfBytesToBase64:
    """Tests for the bytes-to-base64 helper."""

    def test_converts_bytes_to_base64_string(self):
        """It should encode bytes and return a base64 string."""

        value = b"sample pdf payload"
        result = pdf_bytes_to_base64(value)

        assert isinstance(result, str)
        assert result == base64.b64encode(value).decode("utf-8")

    def test_handles_bytearray_inputs(self):
        """Bytearray inputs should also be accepted."""

        payload = bytearray(b"abc123")
        result = pdf_bytes_to_base64(payload)

        assert result == base64.b64encode(bytes(payload)).decode("utf-8")

    def test_returns_empty_string_for_empty_bytes(self):
        """Empty inputs should produce an empty string."""

        assert pdf_bytes_to_base64(b"") == ""

    def test_raises_type_error_for_invalid_input(self):
        """Non-bytes inputs should raise a ``TypeError``."""

        with pytest.raises(TypeError):
            pdf_bytes_to_base64("not-bytes")
