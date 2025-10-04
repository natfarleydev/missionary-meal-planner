"""PDF generation helpers for the Missionary Meal Planner."""

import base64
from pathlib import Path
from typing import Any

from jinja2 import Template
from weasyprint import CSS, HTML

from state_model import AppState

_MEAL_PLANNER_CSS = """
@page {
    size: A4 landscape;
    margin: 0.35in;
}
@media print {
    body {
        margin: 0;
        padding: 12px;
    }
    table {
        page-break-inside: avoid;
    }
    .header h1 {
        margin-bottom: 4px;
        font-size: 2.1em;
    }
    .header-subtitle {
        margin-bottom: 6px;
        font-size: 1em;
    }
}
"""


def generate_meal_planner_pdf(app_state: AppState) -> bytes:
    """Render the missionary meal planner PDF for the provided application state."""

    template_path = Path(__file__).resolve().parent / "templates" / "meal_planner.html"
    if not template_path.exists():
        raise FileNotFoundError

    template = Template(template_path.read_text(encoding="utf-8"))
    companionships_context = app_state.model_dump(exclude_none=False)[
        "companionships_data"
    ]

    html_content = template.render(companionships=companionships_context)
    html_doc = HTML(string=html_content, base_url=str(template_path.parent))

    return html_doc.write_pdf(stylesheets=[CSS(string=_MEAL_PLANNER_CSS)])


def pdf_bytes_to_base64(pdf_bytes: bytes) -> str:
    """Encode PDF bytes as a plain base64 string for browser embedding."""

    if not isinstance(pdf_bytes, bytes | bytearray):
        raise TypeError

    if not pdf_bytes:
        return ""

    return base64.b64encode(bytes(pdf_bytes)).decode("utf-8")


def _resolve_photo_source(photo: Any) -> str | None:  # noqa: PLR0911
    """Return a data URI suitable for embedding in HTML for the provided photo value."""

    if not photo:
        return None

    if isinstance(photo, bytes):
        return _encode_bytes_as_data_uri(photo)

    if isinstance(photo, str):
        if photo.startswith("data:"):
            return photo

        photo_path = Path(photo)
        if photo_path.exists():
            return _encode_file_as_data_uri(photo_path)

        try:
            decoded = base64.b64decode(photo, validate=True)
        except (ValueError, TypeError):
            return None
        else:
            return _encode_bytes_as_data_uri(decoded)

    if isinstance(photo, Path) and photo.exists():
        return _encode_file_as_data_uri(photo)

    return None


def _encode_file_as_data_uri(path: Path) -> str:
    """Convert a file path to a PNG data URI."""

    return _encode_bytes_as_data_uri(path.read_bytes())


def _encode_bytes_as_data_uri(data: bytes) -> str:
    """Encode raw bytes as a base64 PNG data URI."""

    encoded = base64.b64encode(data).decode("utf-8")
    return f"data:image/png;base64,{encoded}"
