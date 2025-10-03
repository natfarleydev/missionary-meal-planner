"""Pytest tests for local storage functions."""

import json
from unittest.mock import patch

import pytest

from local_storage import (
    STORAGE_KEY,
    get_app_state_from_local_storage,
    save_app_state_to_local_storage,
)
from state_model import AppState, Companionship, Missionary


class TestGetAppStateFromLocalStorage:
    """Test cases for the get_app_state_from_local_storage function."""

    def test_get_app_state_success(self):
        """Test successfully retrieving app state from localStorage."""
        # Create an AppState object that matches our expected data
        expected_app_state = AppState(num_companionships=2, companionships_data=[])
        json_string = json.dumps(expected_app_state.model_dump(exclude_none=False))

        with patch("local_storage.streamlit_js_eval") as mock_js_eval:
            mock_js_eval.return_value = json_string

            result = get_app_state_from_local_storage()

            assert isinstance(result, AppState)
            assert result.num_companionships == expected_app_state.num_companionships
            assert result.companionships_data == expected_app_state.companionships_data
            mock_js_eval.assert_called_once_with(
                js_expressions=f"localStorage.getItem('{STORAGE_KEY}') ?? false",
                key="get_app_data",
            )

    def test_get_app_state_no_data(self):
        """Test when no app data exists in localStorage."""
        with patch("local_storage.streamlit_js_eval") as mock_js_eval:
            mock_js_eval.return_value = None

            result = get_app_state_from_local_storage()
            assert result is None

    def test_get_app_state_invalid_json(self):
        """Test when localStorage contains invalid JSON."""
        with patch("local_storage.streamlit_js_eval") as mock_js_eval:
            mock_js_eval.return_value = "invalid json"

            with pytest.raises(ValueError, match="Invalid JSON data in localStorage"):
                get_app_state_from_local_storage()

    def test_get_app_state_none_returned(self):
        """Test when localStorage returns None."""
        with patch("local_storage.streamlit_js_eval") as mock_js_eval:
            mock_js_eval.return_value = None

            result = get_app_state_from_local_storage()
            assert result is None

    def test_get_app_state_js_eval_exception(self):
        """Test when streamlit_js_eval raises an exception."""
        with patch("local_storage.streamlit_js_eval") as mock_js_eval:
            mock_js_eval.side_effect = Exception("JavaScript error")

            with pytest.raises(
                ValueError, match="Error retrieving data from localStorage"
            ):
                get_app_state_from_local_storage()


class TestSaveAppStateToLocalStorage:
    """Test cases for the save_app_state_to_local_storage function."""

    def test_save_app_state_success(self):
        """Test successfully saving app state to localStorage."""
        app_state = AppState(num_companionships=3, companionships_data=[])

        with patch("local_storage.streamlit_js_eval") as mock_js_eval:
            save_app_state_to_local_storage(app_state)

            # Check that the data was properly serialized and escaped
            call_kwargs = mock_js_eval.call_args[1]
            actual_js_expression = call_kwargs["js_expressions"]
            expected_json = app_state.model_dump_json(exclude_none=False)
            expected_js_expression = (
                f"localStorage.setItem('{STORAGE_KEY}', '{expected_json}')"
            )

            assert actual_js_expression == expected_js_expression
            mock_js_eval.assert_called_once()
            assert call_kwargs["key"] == "save_app_data"

    def test_save_app_state_with_special_characters(self):
        """Test saving app state with special characters that need escaping."""

        # Create missionaries with special characters in names
        missionaries = [
            Missionary(name="O'Connor", title="Elder"),
            Missionary(name="Smith's", title="Sister"),
        ]
        companionship = Companionship(missionaries=missionaries)
        app_state = AppState(companionships_data=[companionship])

        with patch("local_storage.streamlit_js_eval") as mock_js_eval:
            save_app_state_to_local_storage(app_state)

            call_kwargs = mock_js_eval.call_args[1]
            actual_js_expression = call_kwargs["js_expressions"]
            # The JSON should contain the special characters properly escaped for JavaScript
            # model_dump_json() handles escaping differently than json.dumps()
            assert (
                "O'Connor" in actual_js_expression
            )  # Should be properly escaped in the JSON
            assert (
                "Smith's" in actual_js_expression
            )  # Should be properly escaped in the JSON
            # Also check that the JSON structure is correct
            assert '"companionships_data"' in actual_js_expression
            assert '"missionaries"' in actual_js_expression
            assert '"name"' in actual_js_expression
            assert '"title"' in actual_js_expression

    def test_save_app_state_serialization_error(self):
        """Test when app state cannot be serialized."""
        app_state = AppState()

        with patch.object(AppState, "model_dump_json") as mock_model_dump_json:
            mock_model_dump_json.side_effect = Exception("Serialization error")

            with pytest.raises(ValueError, match="Error saving data to localStorage"):
                save_app_state_to_local_storage(app_state)

    def test_save_app_state_js_eval_exception(self):
        """Test when streamlit_js_eval raises an exception during save."""
        app_state = AppState(num_companionships=2)

        with patch("local_storage.streamlit_js_eval") as mock_js_eval:
            mock_js_eval.side_effect = Exception("Storage quota exceeded")

            with pytest.raises(ValueError, match="Error saving data to localStorage"):
                save_app_state_to_local_storage(app_state)


class TestStorageKey:
    """Test that the storage key constant is correct."""

    def test_storage_key_value(self):
        """Test that STORAGE_KEY has the expected value."""
        assert STORAGE_KEY == "app_data"
