"""Local storage utilities for persisting app state using streamlit-js-eval."""

import json
import streamlit as st
import structlog

from streamlit_js_eval import streamlit_js_eval

from state_model import AppState

# localStorage key for app data
STORAGE_KEY = "app_data"

log = structlog.get_logger()

def get_app_state_from_local_storage() -> AppState | None | bool:
    """
    Retrieve app state from localStorage.

    Returns:
        AppState | None: The app state object from localStorage, or None if no data exists.

    Raises:
        ValueError: If data exists but is invalid JSON.
    """
    loading_msg = st.info("🔍 Retrieving saved data...")

    try:
        # Retrieve the JSON string from localStorage
        js_expression = f"localStorage.getItem('{STORAGE_KEY}') ?? false"
        log.info("Retrieving app state from localStorage", js_expression=js_expression)
        json_string = streamlit_js_eval(js_expressions=js_expression, key="get_app_data")
        log.info("Retrieved app state from localStorage", json_string=json_string)

        if json_string is None:
            log.info("No app state found in localStorage", json_string=json_string)
            loading_msg.success("✅ No saved data found!")
            return None

        # Parse the JSON string
        app_state_dict = json.loads(json_string)
        log.info("Parsed app state from localStorage", app_state_dict=app_state_dict)

        # Create and return AppState object
        app_state = AppState.model_validate(app_state_dict)
        log.info("Created AppState object from localStorage", app_state=app_state)

        loading_msg.success("✅ Saved data restored!")

        return app_state
    except (json.JSONDecodeError, TypeError) as e:
        loading_msg.error(f"❌ Error retrieving app state from localStorage: {e}")
        raise ValueError(f"Invalid JSON data in localStorage: {e}")
    except Exception as e:
        loading_msg.error(f"❌ Error retrieving data from localStorage: {e}")
        raise ValueError(f"Error retrieving data from localStorage: {e}")


def save_app_state_to_local_storage(app_state: AppState) -> None:
    """
    Save app state to localStorage.

    Args:
        app_state: The AppState object to save.

    Raises:
        ValueError: If the app state cannot be serialized or saved.
    """
    try:
        # Convert the AppState to a JSON string
        app_state_dict = app_state.model_dump_json(exclude_none=False)

        # Save to localStorage
        js_expression = f"localStorage.setItem('{STORAGE_KEY}', '{app_state_dict}')"
        streamlit_js_eval(js_expressions=js_expression, key="save_app_data")
        st.success("✅ App state saved to localStorage successfully!")


    except (TypeError, ValueError) as e:
        raise ValueError(f"Error serializing app state: {e}")
    except Exception as e:
        raise ValueError(f"Error saving data to localStorage: {e}")
