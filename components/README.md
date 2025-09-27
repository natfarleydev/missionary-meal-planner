# Custom Components

This directory contains custom Streamlit components for the Missionary Meal Planner application.

## MissionaryInput Component

The `MissionaryInput` component combines a title dropdown (Elder/Sister) and name text input into a single visual component that appears as one cohesive input field.

### Features

- **Unified Design**: Dropdown and text input appear as one component with shared styling
- **Custom CSS**: Includes styling to make the component look seamless
- **Session State Support**: Maintains current values and selections
- **Flexible Configuration**: Supports custom labels, default values, and unique keys

### Usage

```python
from components.missionary_input import missionary_input_field

# Basic usage - returns combined string
full_name = missionary_input_field(
    label="Missionary 1",
    current_title="Elder",
    current_name="Smith",
    key_prefix="missionary_1"
)
# Returns: "Elder Smith" or just "Elder" if name is empty

# Advanced usage with MissionaryInput class
from components.missionary_input import MissionaryInput

component = MissionaryInput(label="Missionary", key_prefix="unique_key")
full_name = component.render(current_title="Sister", current_name="Johnson")
# Returns: "Sister Johnson" or just "Sister" if name is empty
```

### Parameters

- `label`: Display label for the component
- `default_title`: Default title selection ("Elder" or "Sister")
- `current_title`: Currently selected title value
- `current_name`: Current name value
- `key_prefix`: Prefix for unique component keys

### Returns

Returns a single string combining title and name (e.g., "Elder Smith" or just "Elder" if name is empty).
