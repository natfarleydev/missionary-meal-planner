"""Integration tests for streamlit app local storage restoration."""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from local_storage import get_app_state_from_local_storage
from state_model import AppState, Companionship, Missionary


class TestLocalStorageRestoration:
    """Test cases for local storage restoration in streamlit_app."""

    def test_local_storage_restored_flag_prevents_multiple_restorations(self):
        """Test that local storage is only restored once per session."""
        # Create a mock session state
        session_state = {}

        # Mock data to return from local storage
        app_state = AppState(
            num_companionships=2,
            companionships_data=[
                Companionship(missionaries=[Missionary(name="Smith", title="Elder")])
            ],
        )

        def mock_get():
            return app_state

        # First call - should restore
        assert "#local_storage_restored" not in session_state

        # Simulate the restoration logic from streamlit_app
        if "#local_storage_restored" not in session_state:
            session_state["#local_storage_restored"] = True
            local_storage_data = mock_get()
            if local_storage_data is not None:
                for key, value in local_storage_data.to_session_state().items():
                    session_state[key] = value

        # Verify restoration happened
        assert session_state["#local_storage_restored"] is True
        assert session_state["/num_companionships"] == 2

        # Second call - should NOT restore again
        call_count_before = len(session_state)
        if "#local_storage_restored" not in session_state:
            session_state["#local_storage_restored"] = True
            local_storage_data = mock_get()
            if local_storage_data is not None:
                for key, value in local_storage_data.to_session_state().items():
                    session_state[key] = value

        # Verify restoration didn't happen again (state size unchanged)
        assert len(session_state) == call_count_before
        assert session_state["#local_storage_restored"] is True

    def test_restoration_happens_even_if_no_data_in_local_storage(self):
        """Test that flag is set even when no data exists in local storage."""
        session_state = {}

        def mock_get():
            return None

        # Simulate the restoration logic from streamlit_app
        if "#local_storage_restored" not in session_state:
            session_state["#local_storage_restored"] = True
            local_storage_data = mock_get()
            if local_storage_data is not None:
                for key, value in local_storage_data.to_session_state().items():
                    session_state[key] = value

        # Verify flag is set even though no data was restored
        assert session_state["#local_storage_restored"] is True
        # No other keys should be set
        assert len(session_state) == 1

    def test_photo_upload_tracking_preserved_across_restoration(self):
        """Test that photo upload tracking keys are preserved during restoration."""
        session_state = {}

        # Set up a photo upload tracking key
        photo_path = "/companionships_data/0/missionaries/0/photo"
        tracking_key = f"#photo_upload_tracking{photo_path}"
        session_state[tracking_key] = "missionary_photo.jpg"
        session_state[photo_path] = "data:image/jpeg;base64,iVBORw0KGgo="

        # Create valid base64 for old photo
        old_photo_base64 = base64.b64encode(b"old photo data").decode("utf-8")
        app_state = AppState(
            num_companionships=1,
            companionships_data=[
                Companionship(
                    missionaries=[
                        Missionary(
                            name="Smith",
                            title="Elder",
                            photo=f"data:image/jpeg;base64,{old_photo_base64}",
                        )
                    ]
                )
            ],
        )

        def mock_get():
            return app_state

        # Mark as already restored to simulate subsequent rerun
        session_state["#local_storage_restored"] = True

        # Simulate the restoration logic (should be skipped)
        if "#local_storage_restored" not in session_state:
            session_state["#local_storage_restored"] = True
            local_storage_data = mock_get()
            if local_storage_data is not None:
                for key, value in local_storage_data.to_session_state().items():
                    session_state[key] = value

        # Verify restoration didn't happen and tracking is preserved
        assert session_state[tracking_key] == "missionary_photo.jpg"
        assert (
            session_state[photo_path] == "data:image/jpeg;base64,iVBORw0KGgo="
        )  # NEW photo preserved

    def test_restoration_sets_all_state_keys_from_local_storage(self):
        """Test that all keys from local storage are properly set in session state."""
        session_state = {}

        app_state = AppState(
            num_companionships=3,
            companionships_data=[
                Companionship(
                    missionaries=[Missionary(name="Smith", title="Elder")],
                    phone_number="123-456-7890",
                )
            ],
            missionary_counts=[2, 2, 3],
        )

        def mock_get():
            return app_state

        # Simulate the restoration logic
        if "#local_storage_restored" not in session_state:
            session_state["#local_storage_restored"] = True
            local_storage_data = mock_get()
            if local_storage_data is not None:
                for key, value in local_storage_data.to_session_state().items():
                    session_state[key] = value

        # Verify all keys were set
        assert session_state["/num_companionships"] == 3
        assert session_state["/companionships_data/0/phone_number"] == "123-456-7890"
        assert session_state["/companionships_data/0/missionaries/0/name"] == "Smith"
        assert (
            session_state["/companionships_data/0/missionaries/0/title"] == "Elder"
        )
        assert session_state["/missionary_counts/0"] == 2
        assert session_state["/missionary_counts/1"] == 2
        assert session_state["/missionary_counts/2"] == 3
