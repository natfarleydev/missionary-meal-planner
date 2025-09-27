import json
import streamlit as st
from datetime import datetime, timedelta
import base64
from io import BytesIO
from jinja2 import Template
from weasyprint import HTML, CSS
from PIL import Image
import os
import tempfile
import uuid
import streamlit.components.v1 as st_components
from components import missionary_input_field
from state_model import (
    AppState,
    DEFAULT_MISSIONARIES_PER_COMPANIONSHIP,
    LOCAL_STORAGE_KEY,
    create_companionship,
)

# Page configuration
st.set_page_config(
    page_title="Missionary Meal Planner",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    st.title("🍽️ Missionary Meal Planner")

    # Initialize session state
    if "companionships_data" not in st.session_state:
        default_state = AppState.create_default()
        st.session_state.update(default_state.to_session_state())

    normalize_session_state()

    # Sidebar for basic settings
    with st.sidebar:
        st.header("Settings")
        num_companionships = st.number_input(
            "Number of Companionships",
            min_value=1,
            max_value=10,
            value=st.session_state.num_companionships,
            key="num_companionships_input"
        )

        if num_companionships != st.session_state.num_companionships:
            st.session_state.num_companionships = num_companionships
            st.session_state.companionships_data = []
            st.session_state.missionary_counts = {}
            st.rerun()

        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown("""
        1. Set the number of companionships
        2. For each companionship, set the number of missionaries (2 or 3)
        3. Upload photos and enter names for each missionary
        4. Enter dates for each day of the week
        5. Click 'Generate Meal Planner' to create the image
        """)

    # Main content
    st.subheader("📸 Missionary Information")

    # Initialize companionships data structure
    if len(st.session_state.companionships_data) != num_companionships:
        st.session_state.companionships_data = [
            create_companionship(
                st.session_state.missionary_counts.get(i, DEFAULT_MISSIONARIES_PER_COMPANIONSHIP)
            ).model_dump()
            for i in range(num_companionships)
        ]

    # Input forms for each companionship
    for i in range(num_companionships):
        st.subheader(f"Companionship {i + 1}")

        # Number of missionaries selector for this companionship
        # Ensure companionship data exists
        while i >= len(st.session_state.companionships_data):
            st.session_state.companionships_data.append(
                create_companionship(DEFAULT_MISSIONARIES_PER_COMPANIONSHIP).model_dump()
            )

        current_count = len(st.session_state.companionships_data[i]['missionaries'])
        missionary_count = st.radio(
            f"Number of Missionaries in Companionship {i + 1}",
            options=[2, 3],
            index=0 if current_count == 2 else 1,
            key=f"missionary_count_{i}",
            horizontal=True
        )

        # Update the missionary count for this companionship
        if missionary_count != current_count:
            st.session_state.missionary_counts[i] = missionary_count
            if i < len(st.session_state.companionships_data):
                refreshed_companionship = create_companionship(missionary_count).model_dump()
                st.session_state.companionships_data[i]['missionaries'] = refreshed_companionship['missionaries']
            st.rerun()

        # Missionary inputs
        missionaries_data = []
        for j in range(missionary_count):
            st.markdown(f"**Missionary {j + 1}**")

            # Photo upload
            photo = st.file_uploader(
                f"Photo for Missionary {j + 1}",
                type=['png', 'jpg', 'jpeg'],
                key=f"photo_{i}_{j}",
                help="Upload a clear photo of the missionary"
            )

            # Combined title and name input
            current_title = "Elder"
            current_name = ""
            current_photo = None
            if (i < len(st.session_state.companionships_data) and
                'missionaries' in st.session_state.companionships_data[i] and
                j < len(st.session_state.companionships_data[i]['missionaries'])):

                missionary_data = st.session_state.companionships_data[i]['missionaries'][j]
                current_title = missionary_data.get('title', current_title)
                current_name = missionary_data.get('name', current_name)
                current_photo = missionary_data.get('photo')

            # Use custom component for combined title and name input
            missionary_input_field(
                label=f"Missionary {j + 1}",
                default_title="Elder",
                current_title=current_title,
                current_name=current_name,
                key_prefix=f"missionary_{i}_{j}"
            )

            title_key = f"missionary_{i}_{j}_title"
            name_key = f"missionary_{i}_{j}_name"
            selected_title = st.session_state.get(title_key, current_title) or "Elder"
            selected_name = st.session_state.get(name_key, current_name) or ""

            # Process and save photo
            photo_path = current_photo
            if photo is not None:
                # Convert to PIL Image and save temporarily
                pil_image = Image.open(photo)
                # Resize to reasonable size for web display
                pil_image = pil_image.resize((200, 200))

                # Save to temp file
                temp_dir = tempfile.gettempdir()
                photo_filename = f"missionary_photo_{uuid.uuid4()}.png"
                photo_path = os.path.join(temp_dir, photo_filename)
                pil_image.save(photo_path, "PNG")

            missionaries_data.append({
                'title': selected_title,
                'name': selected_name.strip(),
                'photo': photo_path
            })

        # Phone number input
        phone_value = ""
        if (i < len(st.session_state.companionships_data) and
            'phone_number' in st.session_state.companionships_data[i]):
            phone_value = st.session_state.companionships_data[i]['phone_number']

        phone_number = st.text_input(
            f"Phone Number for Companionship {i + 1}",
            value=phone_value,
            key=f"phone_{i}",
            placeholder="Enter phone number"
        )

        # Update session state
        if i < len(st.session_state.companionships_data):
            st.session_state.companionships_data[i]['missionaries'] = missionaries_data
            st.session_state.companionships_data[i]['phone_number'] = phone_number

    # Date inputs section
    st.subheader("📅 Weekly Schedule")

    st.markdown("Enter the starting date for the week:")

    # Get the starting date
    start_date = st.date_input(
        "Starting Date",
        value=st.session_state.dates.get('start_date', datetime.now().date()),
        key="start_date_input"
    )

    # Calculate dates for the week (starting on Monday)
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    st.session_state.dates = {}

    # Find which day of the week the start_date is
    start_day_index = start_date.weekday()  # 0=Monday, 6=Sunday
    days_since_monday = start_day_index  # 0=Monday, 6=Sunday

    for i, day in enumerate(days_of_week):
        # Calculate the date for this day of the week
        days_to_add = (i - days_since_monday) % 7
        day_date = start_date + timedelta(days=days_to_add)
        st.session_state.dates[day] = day_date

    # Display the calculated dates
    st.markdown("**Week dates:**")
    for day in days_of_week:
        st.markdown(f"- **{day}:** {st.session_state.dates[day].strftime('%B %d, %Y')}")

    # Generate button
    if st.button("🍽️ Generate Meal Planner", type="primary", width='stretch'):
        generate_meal_planner()

    st.markdown("---")
    if st.button("💾 Save Planner State", key="save_state_button"):
        save_state_to_local_storage()
        st.success("State saved to your browser storage.")

    # Display generated PDF if available
    if st.session_state.generated_pdf:
        st.subheader("📋 Generated Meal Planner")

        # Display the PDF using an iframe
        pdf_b64 = base64.b64encode(st.session_state.generated_pdf).decode()
        pdf_html = f'''
        <iframe src="data:application/pdf;base64,{pdf_b64}"
                width="100%"
                height="600"
                style="border: none;">
        </iframe>
        '''
        st.components.v1.html(pdf_html, height=600)

        # Download button
        st.download_button(
            label="💾 Download PDF",
            data=st.session_state.generated_pdf,
            file_name="missionary_meal_planner.pdf",
            mime="application/pdf",
            width='stretch'
        )

def generate_meal_planner():
    """Generate the meal planner image using WeasyPrint"""
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    try:
        # Prepare data for template - now we need companionships with phone numbers
        companionships = []

        for i, comp_data in enumerate(st.session_state.companionships_data):
            companionship = {
                'missionaries': [],
                'phone_number': comp_data['phone_number'] if comp_data['phone_number'] else f"Phone {i+1}"
            }

            # Process missionaries
            for missionary in comp_data['missionaries']:
                title = missionary.get('title', 'Elder')
                name = missionary.get('name', '')
                if not isinstance(title, str) or not title:
                    title = 'Elder'
                if not isinstance(name, str):
                    name = ''
                display_name = f"{title} {name}".strip() if name else title
                comp_missionary = {
                    'name': display_name if display_name else f"Missionary {i+1}",
                    'photo': missionary.get('photo')
                }
                companionship['missionaries'].append(comp_missionary)

            companionships.append(companionship)

        # Load and render template
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'meal_planner.html')
        with open(template_path, 'r') as f:
            template_content = f.read()

        template = Template(template_content)
        html_content = template.render(companionships=companionships)

        # Generate image using WeasyPrint
        # Create HTML with embedded images using base64 encoding
        html_with_images = html_content

        # Convert images to base64 for embedding in HTML
        for i, comp in enumerate(companionships):
            for j, missionary in enumerate(comp['missionaries']):
                if missionary['photo'] and os.path.exists(missionary['photo']):
                    try:
                        with open(missionary['photo'], "rb") as img_file:
                            img_data = img_file.read()
                            img_b64 = base64.b64encode(img_data).decode()
                            # Replace the photo path with base64 data URL
                            old_src = f"{{{{ missionary.photo }}}}"
                            new_src = f"data:image/png;base64,{img_b64}"
                            html_with_images = html_with_images.replace(
                                f'src="{missionary["photo"]}"',
                                f'src="data:image/png;base64,{img_b64}"'
                            )
                    except Exception as e:
                        print(f"Error processing image for companionship {i}, missionary {j}: {e}")

        # Generate PDF from HTML
        html_doc = HTML(string=html_with_images)

        # For Streamlit, we'll create a PNG from the PDF
        # WeasyPrint can render to PNG using the CSS @page and @media print
        css_string = """
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

        # Write PDF first
        html_doc.write_pdf("temp_planner.pdf", stylesheets=[CSS(string=css_string)])

        # Read the generated PDF
        with open("temp_planner.pdf", "rb") as f:
            pdf_data = f.read()

        # Store PDF in session state
        st.session_state.generated_pdf = pdf_data

        # Clean up temp files
        try:
            os.remove("temp_planner.pdf")
        except:
            pass

        st.success("✅ Meal planner generated successfully!")

    except Exception as e:
        st.error(f"❌ Error generating meal planner: {str(e)}")
        print(f"Error: {e}")


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
                    full_name = missionary.get("name") if isinstance(missionary.get("name"), str) else ""
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


def save_state_to_local_storage() -> None:
    """Persist the current planner state into the browser's localStorage."""

    app_state = AppState.from_session_state(st.session_state)
    payload = app_state.to_storage_payload()
    payload_json = json.dumps(payload)

    st_components.html(
        f"""
        <script>
        const storageKey = "{LOCAL_STORAGE_KEY}";
        const payload = {payload_json};
        window.localStorage.setItem(storageKey, JSON.stringify(payload));
        </script>
        """,
        height=0,
    )

if __name__ == "__main__":
    main()
