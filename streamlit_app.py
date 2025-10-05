import binascii
from enum import Enum, auto

import streamlit as st
import structlog

from generate_pdf import generate_meal_planner_pdf, pdf_bytes_to_base64
from local_storage import (
    get_app_state_from_local_storage,
    save_app_state_to_local_storage,
)
from photo_processing import (
    UnsupportedImageTypeError,
    process_uploaded_photo,
)
from state_model import AppState
from utils import is_valid_photo_data_uri, photo_data_uri_to_bytes


class PhotoState(Enum):
    EMPTY = auto()
    INVALID = auto()
    READY = auto()


def _get_photo_state(photo_value: object) -> PhotoState:
    if not is_valid_photo_data_uri(photo_value):
        if isinstance(photo_value, str) and photo_value.strip():
            return PhotoState.INVALID
        return PhotoState.EMPTY
    return PhotoState.READY


def handle_uploaded_photo(photo_path: str, uploaded_file: object) -> None:
    try:
        processed = process_uploaded_photo(uploaded_file)
    except UnsupportedImageTypeError as exc:
        st.error(str(exc))
        return
    except (ValueError, TypeError) as exc:
        st.error(f"Error processing uploaded file: {exc}")
        return
    except Exception as exc:
        st.error(f"Unexpected error processing photo: {exc}")
        return

    st.session_state[photo_path] = processed.data_uri
    st.rerun()


def display_uploaded_photo(
    *,
    base64_payload: str,
    companionship_index: int,
    missionary_index: int,
    photo_state_key: str,
) -> None:
    try:
        photo_data_uri_to_bytes(base64_payload)
    except (binascii.Error, ValueError):
        st.warning(
            "Saved photo data is invalid. Please upload a new image.",
            icon="⚠️",
        )
        st.session_state[photo_state_key] = ""
        st.rerun()
        return

    photo_html = f"""
    <div style='display: flex; align-items: center; justify-content: center; padding: 0.25rem 0;'>
        <img
            src="{base64_payload}"
            alt="Missionary {missionary_index + 1} photo"
            style="
                width: 50px;
                height: 50px;
                max-width: 50px;
                max-height: 50px;
                object-fit: cover;
                border-radius: 50%;
                border: 2px solid #ddd;
            "
        />
    </div>
    """
    preview_col, delete_col = st.columns(2)

    with preview_col:
        st.markdown(photo_html, unsafe_allow_html=True)

    with delete_col:
        if st.button(
            "🗑️ Delete photo",
            key=f"delete_photo_{companionship_index}_{missionary_index}",
            help="Delete photo",
        ):
            st.session_state[photo_state_key] = ""
            st.rerun()


log = structlog.get_logger()


# Config stuff
st.session_state["#should_fetch_from_local_storage"] = st.session_state.get(
    "#should_fetch_from_local_storage", True
)
if (
    st.session_state["#should_fetch_from_local_storage"]
    and (local_storage_data := get_app_state_from_local_storage()) is not None
):
    # this is a one time check, so we indicate that we've done it
    st.session_state["#should_fetch_from_local_storage"] = False
    # OK, here we check if the session state is empty, if so, we create a default state
    log.info("Found data in local storage", local_storage_data=local_storage_data)
    for key, value in local_storage_data.to_session_state().items():
        log.info("Setting session state", key=key, value=value)
        st.session_state[key] = value

default_state = AppState.create_default()
for key, value in default_state.to_session_state().items():
    if key not in st.session_state:
        st.session_state[key] = value

# Set up generated pdf bytes
st.session_state["#generated_pdf_bytes"] = st.session_state.get(
    "#generated_pdf_bytes", None
)


# Page configuration
st.set_page_config(
    page_title="Missionary Meal Planner",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# def _remove_old_companionships():


def main():
    # OK, here we check if the session state is empty, if so, we create a default state
    default_state = AppState.create_default()
    for key, value in default_state.to_session_state().items():
        if key not in st.session_state:
            st.session_state[key] = value

    for k in st.session_state:
        if (k.startswith("/companionships_data")) and (
            not any(
                k.startswith(f"/companionships_data/{i}")
                for i in range(st.session_state["/num_companionships"])
            )
        ):
            del st.session_state[k]

    st.title("🍽️ Missionary Meal Planner")

    with st.sidebar:
        st.header("Settings")
        st.number_input(
            "Number of Companionships",
            min_value=1,
            max_value=10,
            key="/num_companionships",
        )

        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown(
            """
        1. Set the number of companionships
        1. For each companionship, set the number of missionaries (2 or 3)
        1. Upload photos and enter names for each missionary
        1. Click 'Generate Meal Planner' to create the image
        """
        )

    # Main content
    st.subheader("📸 Missionary Information")

    # Input forms for each companionship
    for companionship_index in range(st.session_state["/num_companionships"]):
        st.subheader(f"Companionship {companionship_index + 1}")

        companionship_config_cols = st.columns(2)
        with companionship_config_cols[0]:
            missionary_count = st.segmented_control(
                f"Number of Missionaries in Companionship {companionship_index + 1}",
                options=[2, 3],
                default=2,
                key=f"/missionary_counts/{companionship_index}",
            )
        with companionship_config_cols[1]:
            gender_of_companionship = st.segmented_control(
                f"Gender of Companionship {companionship_index + 1}",
                options=["Elders", "Sisters", "Elder and Sister"],
                default="Elders",
                selection_mode="single",
                key=f"#component/companionships_data/{companionship_index}/missionaries/*/title",
            )
            match gender_of_companionship:
                case "Elders":
                    for i in range(missionary_count):
                        st.session_state[
                            f"/companionships_data/{companionship_index}/missionaries/{i}/title"
                        ] = "Elder"
                case "Sisters":
                    for i in range(missionary_count):
                        st.session_state[
                            f"/companionships_data/{companionship_index}/missionaries/{i}/title"
                        ] = "Sister"
                case "Elder and Sister":
                    st.session_state[
                        f"/companionships_data/{companionship_index}/missionaries/0/title"
                    ] = "Elder"
                    st.session_state[
                        f"/companionships_data/{companionship_index}/missionaries/1/title"
                    ] = "Sister"

        st.text_input(
            f"Phone Number for Companionship {companionship_index + 1}",
            key=f"/companionships_data/{companionship_index}/phone_number",
            placeholder="07800 314 ...",
        )

        # Missionary inputs
        for missionary_index in range(missionary_count):
            # Photo upload
            photo_path = f"/companionships_data/{companionship_index}/missionaries/{missionary_index}/photo"
            uploader_key = f"#component/companionships_data/{companionship_index}/missionaries/{missionary_index}/photo_uploader"

            photo_status = _get_photo_state(st.session_state.get(photo_path))

            name_col, photo_col = st.columns(2)

            with name_col:
                st.text_input(
                    st.session_state[
                        f"/companionships_data/{companionship_index}/missionaries/{missionary_index}/title"
                    ],
                    key=f"/companionships_data/{companionship_index}/missionaries/{missionary_index}/name",
                    placeholder="Missionary last name (e.g. Smith)",
                )

            with photo_col:
                if photo_status is PhotoState.READY:
                    display_uploaded_photo(
                        base64_payload=st.session_state[photo_path],
                        companionship_index=companionship_index,
                        missionary_index=missionary_index,
                        photo_state_key=photo_path,
                    )
                else:
                    if photo_status is PhotoState.INVALID:
                        st.warning(
                            "Saved photo data is invalid. Please upload a new image.",
                            icon="⚠️",
                        )
                        st.session_state[photo_path] = None
                        st.rerun()

                    uploaded_file = st.file_uploader(
                        f"Photo for Missionary {missionary_index + 1} (optional)",
                        type=["png", "jpg", "jpeg", "gif", "webp"],
                        help="Upload a clear photo of the missionary",
                        key=uploader_key,
                    )

                    if uploaded_file is not None:
                        handle_uploaded_photo(photo_path, uploaded_file)

    # Generate button
    if st.button("🍽️ Generate Meal Planner", type="primary", width="stretch"):
        generate_meal_planner()

    # Display generated PDF if available
    if st.session_state["/generated_pdf"]:
        st.subheader("📋 Generated Meal Planner")

        # Download button
        st.download_button(
            label="💾 Download PDF",
            data=st.session_state["#generated_pdf_bytes"],
            file_name="missionary_meal_planner.pdf",
            mime="application/pdf",
            width="stretch",
        )

        # Display the PDF using an iframe
        pdf_html = f"""
        <iframe src="data:application/pdf;base64,{st.session_state["/generated_pdf"]}"
                width="100%"
                height="600"
                style="border: none;">
        </iframe>
        """
        st.components.v1.html(pdf_html, height=600)


def generate_meal_planner():
    """Generate the meal planner image using WeasyPrint"""

    try:
        app_state = AppState.from_session_state(
            {k: v for k, v in st.session_state.items() if k.startswith("/")}
        )

        save_app_state_to_local_storage(app_state)

        pdf_data: bytes = generate_meal_planner_pdf(app_state)
        st.session_state["#generated_pdf_bytes"] = pdf_data
        st.session_state["/generated_pdf"] = pdf_bytes_to_base64(pdf_data)

        st.success("✅ Meal planner generated successfully!")

    except Exception as e:
        st.error(f"❌ Error generating meal planner: {e!s}")


def split_full_name(value: str) -> tuple[str, str]:
    """Split a formatted name into title and name components."""

    if not value:
        return "Elder", ""

    trimmed = value.strip()
    if not trimmed:
        return "Elder", ""

    parts = trimmed.split(" ", 1)
    potential_title = parts[0]
    if potential_title in {"Elder", "Sister"}:
        title = potential_title
        remainder = parts[1] if len(parts) > 1 else ""
        return title, remainder.strip()

    return "Elder", trimmed


def normalize_session_state() -> None:
    """Ensure session state data conforms to the current schema."""

    companionships = st.session_state.get("companionships_data", [])
    for companionship in companionships:
        missionaries = companionship.get("missionaries", [])
        if not isinstance(missionaries, list):
            missionaries = []
            companionship["missionaries"] = missionaries

        for index, missionary in enumerate(missionaries):
            if isinstance(missionary, dict):
                if "title" not in missionary:
                    full_name = (
                        missionary.get("name")
                        if isinstance(missionary.get("name"), str)
                        else ""
                    )
                    title, name = split_full_name(full_name)
                    missionary["title"] = title
                    missionary["name"] = name
                else:
                    missionary["title"] = missionary.get("title") or "Elder"
                    name_value = missionary.get("name")
                    if not isinstance(name_value, str):
                        missionary["name"] = ""
                missionary.setdefault("photo", None)
            else:
                title, name = split_full_name(str(missionary))
                missionaries[index] = {"title": title, "name": name, "photo": None}

        companionship.setdefault("phone_number", "")
        companionship.setdefault("schedule", [])


if __name__ == "__main__":
    main()
