"""Utility functions for the Missionary Meal Planner application."""

from __future__ import annotations

import base64
import contextlib
from typing import Any


def flatten_to_json_pointers(
    data: dict[str, Any] | list[Any], parent_path: str = "/"
) -> dict[str, Any]:
    """
    Flatten a nested dict or list into a flat dictionary with JSON pointer keys.

    This function recursively traverses nested data structures and creates a flat
    dictionary where each key is a JSON Pointer (RFC 6901) to the original location
    of the value, and the value is the primitive value itself.

    Args:
        data: The nested dict or list structure to flatten
        parent_path: The current JSON pointer path (used internally for recursion)

    Returns:
        A flat dictionary with JSON pointer keys and primitive values

    Examples:
        >>> data = {"name": "John", "details": {"age": 25, "hobbies": ["reading", "coding"]}}
        >>> flatten_to_json_pointers(data)
        {'/name': 'John', '/details/age': 25, '/details/hobbies/0': 'reading', '/details/hobbies/1': 'coding'}

        >>> flatten_to_json_pointers([1, 2, {"nested": True}])
        {'/0': 1, '/1': 2, '/2/nested': True}
    """
    result: dict[str, Any] = {}

    if isinstance(data, dict):
        for key, value in data.items():
            # Escape special characters in key for JSON Pointer compliance
            escaped_key = str(key).replace("~", "~0").replace("/", "~1")
            current_path = f"{parent_path}{escaped_key}"

            if isinstance(value, dict | list):
                # Recursively flatten nested structures
                nested_result = flatten_to_json_pointers(value, f"{current_path}/")
                result.update(nested_result)
            else:
                # Add primitive value to result
                result[current_path] = value

    elif isinstance(data, list):
        for index, item in enumerate(data):
            current_path = f"{parent_path}{index}"

            if isinstance(item, dict | list):
                # Recursively flatten nested structures
                nested_result = flatten_to_json_pointers(item, f"{current_path}/")
                result.update(nested_result)
            else:
                # Add primitive value to result
                result[current_path] = item

    return result


def unflatten_from_json_pointers(
    flat_dict: dict[str, Any],
) -> dict[str, Any] | list[Any]:
    """
    Reconstruct a nested dict or list from a flat dictionary with JSON pointer keys.

    This function takes a flat dictionary where keys are JSON Pointers (RFC 6901)
    and values are primitive values, then reconstructs the original nested structure.

    Args:
        flat_dict: A flat dictionary with JSON pointer keys and primitive values

    Returns:
        The reconstructed nested dict or list structure

    Examples:
        >>> flat_data = {
        ...     "/name": "John",
        ...     "/details/age": 25,
        ...     "/details/hobbies/0": "reading",
        ...     "/details/hobbies/1": "coding",
        ...     "/active": True
        ... }
        >>> unflatten_from_json_pointers(flat_data)
        {'name': 'John', 'details': {'age': 25, 'hobbies': ['reading', 'coding']}, 'active': True}

        >>> unflatten_from_json_pointers({"/0": "first", "/1": "second"})
        ['first', 'second']
    """
    if not flat_dict:
        return {}

    # Group paths by their structure to determine the root type
    root_paths = {}
    max_depth = 0

    for pointer in flat_dict:
        # Parse the JSON pointer path
        path_parts = _parse_json_pointer(pointer)
        root_paths[pointer] = path_parts
        max_depth = max(max_depth, len(path_parts))

    if not root_paths:
        return {}

    # Determine if root should be a dict or list
    # Check if all root segments are numeric (indicating a list)
    root_segments = set()
    for path_parts in root_paths.values():
        if path_parts:
            root_segments.add(path_parts[0])

    # If all root segments are numeric strings, it's likely a list
    try:
        numeric_segments = {int(seg) for seg in root_segments if seg.isdigit()}
        if numeric_segments and len(numeric_segments) == len(root_segments):
            # It's a list - find the maximum index
            max_index = max(numeric_segments)
            result = [None] * (max_index + 1)

            # Fill in the list values
            for pointer, path_parts in root_paths.items():
                if path_parts and path_parts[0].isdigit():
                    index = int(path_parts[0])
                    remaining_path = path_parts[1:]

                    if not remaining_path:
                        # Direct value at this index
                        result[index] = flat_dict[pointer]
                    # Nested structure at this index
                    elif result[index] is None:
                        result[index] = _create_nested_structure(
                            remaining_path, flat_dict[pointer]
                        )
                    else:
                        _set_nested_value(
                            result[index], remaining_path, flat_dict[pointer]
                        )

            return result
    except (ValueError, AttributeError):
        pass

    # Default to dict structure
    result = {}

    for pointer, path_parts in root_paths.items():
        value = flat_dict[pointer]
        if not path_parts:
            # Root level value - this represents the entire structure
            return value
        _set_nested_value(result, path_parts, value)

    return result


def _parse_json_pointer(pointer: str) -> list[str]:
    """
    Parse a JSON pointer into its component parts.

    Args:
        pointer: A JSON pointer string (e.g., "/details/hobbies/0" or "/")

    Returns:
        List of path segments (e.g., ["details", "hobbies", "0"]) or empty list for root
    """
    if not pointer or pointer[0] != "/":
        return []

    # Remove leading slash and split by remaining slashes
    path = pointer[1:]
    if not path:
        # Root pointer "/"
        return []

    # Split by slash and unescape each segment
    parts = []
    for segment in path.split("/"):
        # Unescape JSON pointer special characters
        unescaped = segment.replace("~1", "/").replace("~0", "~")
        parts.append(unescaped)

    return parts


def _create_nested_structure(
    path_parts: list[str], value: Any
) -> dict[str, Any] | list[Any]:
    """
    Create a nested structure for the given path.

    Args:
        path_parts: List of path segments
        value: The value to place at the end of the path

    Returns:
        The nested structure
    """
    if not path_parts:
        return value

    first_part = path_parts[0]
    remaining_parts = path_parts[1:]

    # Check if first part is a number (indicates array)
    if first_part.isdigit():
        index = int(first_part)
        if not remaining_parts:
            # End of path - create list with this single value
            return [value] if index == 0 else [None] * index + [value]
        # Nested structure - create list and recurse
        result = [None] * (index + 1) if index > 0 else [None]
        result[index] = _create_nested_structure(remaining_parts, value)
        return result
    # Dictionary structure
    if not remaining_parts:
        return {first_part: value}
    return {first_part: _create_nested_structure(remaining_parts, value)}


def _set_nested_value(
    obj: dict[str, Any] | list[Any], path_parts: list[str], value: Any
) -> None:
    """
    Set a value in a nested structure following the given path.

    Args:
        obj: The object to modify (dict or list)
        path_parts: List of path segments to follow
        value: The value to set
    """
    if not path_parts:
        return

    first_part = path_parts[0]
    remaining_parts = path_parts[1:]

    if isinstance(obj, list):
        # For lists, first part should be an index
        if first_part.isdigit():
            index = int(first_part)
            # Extend list if necessary
            while len(obj) <= index:
                obj.append(
                    {} if remaining_parts and not remaining_parts[0].isdigit() else []
                )

            if not remaining_parts:
                obj[index] = value
            else:
                if obj[index] is None:
                    obj[index] = {} if not remaining_parts[0].isdigit() else []
                _set_nested_value(obj[index], remaining_parts, value)
    else:
        # For dicts, first part is a key
        if first_part not in obj:
            obj[first_part] = (
                {} if remaining_parts and not remaining_parts[0].isdigit() else []
            )

        if not remaining_parts:
            obj[first_part] = value
        else:
            _set_nested_value(obj[first_part], remaining_parts, value)


def uploaded_file_to_base64(uploaded_file: Any) -> str:
    """Return a base64-encoded representation of a file-like object.

    This helper normalises the behaviour of ``st.UploadedFile`` objects by
    reading their bytes, optionally rewinding the buffer, and returning the
    contents encoded as UTF-8 base64 text. The function accepts any object that
    exposes a ``read`` method, making it straightforward to unit-test with
    ``io.BytesIO`` or similar file-like implementations.
    """

    if uploaded_file is None:
        raise ValueError("No file provided")

    if not hasattr(uploaded_file, "read"):
        raise TypeError("Uploaded file must provide a read() method")

    data = uploaded_file.read()

    # Reset the cursor when possible to avoid surprising downstream behaviour.
    if hasattr(uploaded_file, "seek"):
        with contextlib.suppress(OSError, ValueError):
            uploaded_file.seek(0)

    if data is None:
        raise ValueError("Uploaded file produced no data")

    if isinstance(data, str):
        data = data.encode("utf-8")
    elif isinstance(data, memoryview):
        data = data.tobytes()

    if not isinstance(data, bytes | bytearray):
        raise TypeError("Uploaded file data must be bytes-like")

    if not data:
        raise ValueError("Uploaded file is empty")

    return base64.b64encode(bytes(data)).decode("utf-8")
