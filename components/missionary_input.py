import streamlit as st

class MissionaryInput:
    """Custom component that combines title dropdown and name input into a single visual component."""

    def __init__(self, label="Missionary", default_title="Elder", key_prefix="missionary"):
        self.label = label
        self.default_title = default_title
        self.key_prefix = key_prefix

    def render(self, current_title=None, current_name="", title_key=None, name_key=None):
        """
        Render the combined title and name input component.

        Args:
            current_title (str): Current title value
            current_name (str): Current name value
            title_key (str): Unique key for the title dropdown
            name_key (str): Unique key for the name input

        Returns:
            str: Combined title and name string (e.g., "Elder Smith" or just "Elder" if name is empty)
        """
        if current_title is None:
            current_title = self.default_title

        # Add custom CSS to make it look like a single component
        st.markdown("""
        <style>
        .missionary-input-container {
            display: flex;
            border: 1px solid #ccc;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 1rem;
        }
        .missionary-input-dropdown {
            border: none !important;
            border-right: 1px solid #ddd !important;
            border-radius: 0 !important;
            flex: 0 0 auto;
            min-width: 80px;
        }
        .missionary-input-text {
            border: none !important;
            border-radius: 0 !important;
            flex: 1;
        }
        .missionary-input-text:focus {
            box-shadow: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Create columns for side-by-side layout
        col1, col2 = st.columns([1, 3])  # 1:3 ratio for dropdown vs text input

        with col1:
            # Title dropdown
            title_options = ["Elder", "Sister"]
            title_index = 0 if current_title == "Elder" else 1
            title = st.radio(
                f"{self.label} Title",
                options=title_options,
                index=title_index,
                key=f"{self.key_prefix}_title",
                label_visibility="collapsed"
            )

        with col2:
            # Name input
            name = st.text_input(
                f"{self.label} Name",
                value=current_name,
                key=name_key or f"{self.key_prefix}_name",
                placeholder="Enter name",
                label_visibility="collapsed"
            )

        # Return combined string
        if name.strip():
            return f"{title} {name}".strip()
        else:
            return title

def missionary_input_field(label="Missionary", default_title="Elder", current_title=None, current_name="", key_prefix="missionary"):
    """
    Convenience function to create a missionary input component.

    Args:
        label (str): Label for the component
        default_title (str): Default title selection
        current_title (str): Current title value
        current_name (str): Current name value
        key_prefix (str): Prefix for component keys

    Returns:
        str: Combined title and name string (e.g., "Elder Smith" or just "Elder" if name is empty)
    """
    component = MissionaryInput(
        label=label,
        default_title=default_title,
        key_prefix=key_prefix
    )
    return component.render(current_title, current_name)
