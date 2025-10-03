"""Pytest tests for utility functions."""

from utils import flatten_to_json_pointers, unflatten_from_json_pointers


class TestFlattenToJsonPointers:
    """Test cases for the flatten_to_json_pointers function."""

    def test_flatten_simple_dict(self):
        """Test flattening a simple dictionary."""
        data = {"name": "John", "age": 25, "active": True}
        result = flatten_to_json_pointers(data)

        expected = {"/name": "John", "/age": 25, "/active": True}
        assert result == expected

    def test_flatten_nested_dict(self):
        """Test flattening a nested dictionary."""
        data = {
            "person": {"name": "John", "details": {"age": 25, "city": "Boston"}},
            "active": True,
        }
        result = flatten_to_json_pointers(data)

        expected = {
            "/person/name": "John",
            "/person/details/age": 25,
            "/person/details/city": "Boston",
            "/active": True,
        }
        assert result == expected

    def test_flatten_with_list(self):
        """Test flattening a structure containing lists."""
        data = {
            "name": "John",
            "hobbies": ["reading", "coding", "gaming"],
            "scores": [95, 87, 92],
        }
        result = flatten_to_json_pointers(data)

        expected = {
            "/name": "John",
            "/hobbies/0": "reading",
            "/hobbies/1": "coding",
            "/hobbies/2": "gaming",
            "/scores/0": 95,
            "/scores/1": 87,
            "/scores/2": 92,
        }
        assert result == expected

    def test_flatten_list_only(self):
        """Test flattening a list structure."""
        data = [1, 2, {"nested": True, "value": 42}]
        result = flatten_to_json_pointers(data)

        expected = {"/0": 1, "/1": 2, "/2/nested": True, "/2/value": 42}
        assert result == expected

    def test_flatten_empty_structures(self):
        """Test flattening empty dicts and lists."""
        # Empty dict
        data = {}
        result = flatten_to_json_pointers(data)
        assert result == {}

        # Empty list
        data = []
        result = flatten_to_json_pointers(data)
        assert result == {}

    def test_flatten_with_special_characters(self):
        """Test flattening with keys containing special JSON Pointer characters."""
        data = {
            "key~with~tildes": "value1",
            "key/with/slashes": "value2",
            "normal_key": "value3",
        }
        result = flatten_to_json_pointers(data)

        expected = {
            "/key~0with~0tildes": "value1",
            "/key~1with~1slashes": "value2",
            "/normal_key": "value3",
        }
        assert result == expected

    def test_flatten_mixed_nested_structure(self):
        """Test flattening a complex mixed structure."""
        data = {
            "users": [
                {"name": "Alice", "active": True},
                {"name": "Bob", "active": False},
            ],
            "settings": {
                "theme": "dark",
                "notifications": {"email": True, "push": False},
            },
        }
        result = flatten_to_json_pointers(data)

        expected = {
            "/users/0/name": "Alice",
            "/users/0/active": True,
            "/users/1/name": "Bob",
            "/users/1/active": False,
            "/settings/theme": "dark",
            "/settings/notifications/email": True,
            "/settings/notifications/push": False,
        }
        assert result == expected

    def test_flatten_with_none_values(self):
        """Test flattening with None values."""
        data = {
            "name": "John",
            "nickname": None,
            "details": {"age": 25, "description": None},
        }
        result = flatten_to_json_pointers(data)

        expected = {
            "/name": "John",
            "/nickname": None,
            "/details/age": 25,
            "/details/description": None,
        }
        assert result == expected

    def test_flatten_numeric_keys(self):
        """Test flattening with numeric dictionary keys."""
        data = {"0": "zero", "1": "one", "items": {"0": "first", "1": "second"}}
        result = flatten_to_json_pointers(data)

        expected = {
            "/0": "zero",
            "/1": "one",
            "/items/0": "first",
            "/items/1": "second",
        }
        assert result == expected

    def test_flatten_root_path_parameter(self):
        """Test that the parent_path parameter works correctly."""
        data = {"nested": {"value": 42}}

        # Test with default root path
        result1 = flatten_to_json_pointers(data)
        expected1 = {"/nested/value": 42}

        # Test with custom root path
        result2 = flatten_to_json_pointers(data, "custom/")
        expected2 = {"custom/nested/value": 42}

        assert result1 == expected1
        assert result2 == expected2


class TestUnflattenFromJsonPointers:
    """Test cases for the unflatten_from_json_pointers function."""

    def test_unflatten_simple_dict(self):
        """Test unflattening a simple flat dict back to nested dict."""
        flat_data = {"/name": "John", "/age": 25, "/active": True}
        result = unflatten_from_json_pointers(flat_data)

        expected = {"name": "John", "age": 25, "active": True}
        assert result == expected

    def test_unflatten_nested_dict(self):
        """Test unflattening a nested structure."""
        flat_data = {
            "/person/name": "John",
            "/person/details/age": 25,
            "/person/details/city": "Boston",
            "/active": True,
        }
        result = unflatten_from_json_pointers(flat_data)

        expected = {
            "person": {"name": "John", "details": {"age": 25, "city": "Boston"}},
            "active": True,
        }
        assert result == expected

    def test_unflatten_with_list(self):
        """Test unflattening a structure containing lists."""
        flat_data = {
            "/name": "John",
            "/hobbies/0": "reading",
            "/hobbies/1": "coding",
            "/hobbies/2": "gaming",
            "/scores/0": 95,
            "/scores/1": 87,
            "/scores/2": 92,
        }
        result = unflatten_from_json_pointers(flat_data)

        expected = {
            "name": "John",
            "hobbies": ["reading", "coding", "gaming"],
            "scores": [95, 87, 92],
        }
        assert result == expected

    def test_unflatten_list_only(self):
        """Test unflattening a list structure."""
        flat_data = {"/0": 1, "/1": 2, "/2": 3}
        result = unflatten_from_json_pointers(flat_data)

        expected = [1, 2, 3]
        assert result == expected

    def test_unflatten_list_with_nested_objects(self):
        """Test unflattening a list containing nested objects."""
        flat_data = {
            "/0/name": "Alice",
            "/0/active": True,
            "/1/name": "Bob",
            "/1/active": False,
            "/2/setting/enabled": True,
        }
        result = unflatten_from_json_pointers(flat_data)

        expected = [
            {"name": "Alice", "active": True},
            {"name": "Bob", "active": False},
            {"setting": {"enabled": True}},
        ]
        assert result == expected

    def test_unflatten_empty_dict(self):
        """Test unflattening an empty dict."""
        flat_data = {}
        result = unflatten_from_json_pointers(flat_data)

        expected = {}
        assert result == expected

    def test_unflatten_with_special_characters(self):
        """Test unflattening with keys containing special JSON Pointer characters."""
        flat_data = {
            "/key~0with~0tildes": "value1",
            "/key~1with~1slashes": "value2",
            "/normal_key": "value3",
        }
        result = unflatten_from_json_pointers(flat_data)

        expected = {
            "key~with~tildes": "value1",
            "key/with/slashes": "value2",
            "normal_key": "value3",
        }
        assert result == expected

    def test_unflatten_mixed_complex_structure(self):
        """Test unflattening a complex mixed structure."""
        flat_data = {
            "/users/0/name": "Alice",
            "/users/0/active": True,
            "/users/1/name": "Bob",
            "/users/1/active": False,
            "/settings/theme": "dark",
            "/settings/notifications/email": True,
            "/settings/notifications/push": False,
            "/metadata/version": "1.0",
            "/metadata/features/0": "feature1",
            "/metadata/features/1": "feature2",
        }
        result = unflatten_from_json_pointers(flat_data)

        expected = {
            "users": [
                {"name": "Alice", "active": True},
                {"name": "Bob", "active": False},
            ],
            "settings": {
                "theme": "dark",
                "notifications": {"email": True, "push": False},
            },
            "metadata": {"version": "1.0", "features": ["feature1", "feature2"]},
        }
        assert result == expected

    def test_unflatten_with_none_values(self):
        """Test unflattening with None values."""
        flat_data = {
            "/name": "John",
            "/nickname": None,
            "/details/age": 25,
            "/details/description": None,
        }
        result = unflatten_from_json_pointers(flat_data)

        expected = {
            "name": "John",
            "nickname": None,
            "details": {"age": 25, "description": None},
        }
        assert result == expected

    def test_unflatten_numeric_dict_keys(self):
        """Test unflattening with numeric dictionary keys."""
        flat_data = {
            "/0": "zero",
            "/1": "one",
            "/items/0": "first",
            "/items/1": "second",
        }
        result = unflatten_from_json_pointers(flat_data)

        expected = {"0": "zero", "1": "one", "items": ["first", "second"]}
        assert result == expected

    def test_roundtrip_flatten_unflatten(self):
        """Test that flatten -> unflatten produces the original structure."""
        # Test with dict
        original_dict = {
            "name": "John",
            "details": {"age": 25, "hobbies": ["reading", "coding"]},
            "active": True,
        }

        flattened = flatten_to_json_pointers(original_dict)
        unflattened = unflatten_from_json_pointers(flattened)

        assert unflattened == original_dict

        # Test with list
        original_list = [1, 2, {"nested": True, "value": 42}]
        flattened_list = flatten_to_json_pointers(original_list)
        unflattened_list = unflatten_from_json_pointers(flattened_list)

        assert unflattened_list == original_list

    def test_unflatten_single_root_value(self):
        """Test unflattening a single root value."""
        flat_data = {"/": "root_value"}
        result = unflatten_from_json_pointers(flat_data)

        expected = "root_value"  # Root pointer returns the value directly
        assert result == expected
