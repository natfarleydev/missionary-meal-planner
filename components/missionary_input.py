import streamlit as st

class MissionaryInputField:
    def __init__(self, label, default_title="Elder", current_title="Elder", current_name="", key_prefix="missionary"):
        self.label = label
        self.default_title = default_title
        self.current_title = current_title
        self.current_name = current_name
        self.key_prefix = key_prefix

    def render(self):
        """Render the missionary input field with segmented control for title"""
        st.markdown(f"""
        <div style="
            margin: 10px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #f9f9f9;
        """, unsafe_allow_html=True)

        # Create columns for side-by-side layout
        col1, col2 = st.columns([1, 3])  # 1:3 ratio for dropdown vs text input

        with col1:
            # Title segmented button
            title_options = ["Elder", "Sister"]
            title = st.segmented_control(
                f"{self.label} Title",
                options=title_options,
                selection_mode="single",
                default=self.current_title,
                key=f"{self.key_prefix}/title",
                label_visibility="collapsed"
            )

        with col2:
            # Name input
            name = st.text_input(
                f"{self.label} Name",
                value=self.current_name,
                key=f"{self.key_prefix}/name",
                label_visibility="collapsed",
                placeholder="Enter missionary name"
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Return the combined full name
        if title and name:
            return f"{title} {name}"
        elif title:
            return title
        else:
            return self.default_title

def missionary_input_field(label="Missionary", default_title="Elder", current_title="Elder", current_name="", key_prefix="missionary"):
    """
    Convenience function to create and render a missionary input field

    Args:
        label: Label for the input field
        default_title: Default title selection
        current_title: Current title value
        current_name: Current name value
        key_prefix: Prefix for widget keys

    Returns:
        str: Combined "Title Name" string
    """
    field = MissionaryInputField(
        label=label,
        default_title=default_title,
        current_title=current_title,
        current_name=current_name,
        key_prefix=key_prefix
    )
    return field.render()