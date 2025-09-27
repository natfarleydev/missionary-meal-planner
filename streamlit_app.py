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
from components import missionary_input_field

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
    if 'companionships_data' not in st.session_state:
        st.session_state.companionships_data = []
    if 'num_companionships' not in st.session_state:
        st.session_state.num_companionships = 4
    if 'missionary_counts' not in st.session_state:
        st.session_state.missionary_counts = {}
    if 'dates' not in st.session_state:
        st.session_state.dates = {}
    if 'generated_pdf' not in st.session_state:
        st.session_state.generated_pdf = None

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
        st.session_state.companionships_data = []
        for i in range(num_companionships):
            # Default to 2 missionaries per companionship, but this can be changed per companionship
            missionary_count = st.session_state.missionary_counts.get(i, 2)
            st.session_state.companionships_data.append({
                'missionaries': [{'name': 'Elder', 'photo': None} for _ in range(missionary_count)],
                'phone_number': '',
                'schedule': []
            })

    # Input forms for each companionship
    for i in range(num_companionships):
        st.subheader(f"Companionship {i + 1}")

        # Number of missionaries selector for this companionship
        # Ensure companionship data exists
        while i >= len(st.session_state.companionships_data):
            st.session_state.companionships_data.append({
                'missionaries': [{'name': 'Elder', 'photo': None} for _ in range(2)],
                'phone_number': '',
                'schedule': []
            })

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
                st.session_state.companionships_data[i]['missionaries'] = [
                    {'name': 'Elder', 'photo': None} for _ in range(missionary_count)
                ]
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
            current_full_name = "Elder"
            if (i < len(st.session_state.companionships_data) and
                'missionaries' in st.session_state.companionships_data[i] and
                j < len(st.session_state.companionships_data[i]['missionaries'])):

                missionary_data = st.session_state.companionships_data[i]['missionaries'][j]
                if 'name' in missionary_data:
                    current_full_name = missionary_data['name']

            # Parse the current name to extract title and name parts for the component
            current_title = "Elder"
            current_name = ""
            if current_full_name != "Elder":  # Not the default empty value
                parts = current_full_name.split(" ", 1)
                if len(parts) >= 1:
                    current_title = parts[0]
                if len(parts) >= 2:
                    current_name = parts[1]

            # Use custom component for combined title and name input
            full_name = missionary_input_field(
                label=f"Missionary {j + 1}",
                default_title="Elder",
                current_title=current_title,
                current_name=current_name,
                key_prefix=f"missionary_{i}_{j}"
            )

            # Process and save photo
            photo_path = None
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
                'name': full_name,
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
                comp_missionary = {
                    'name': missionary['name'] if missionary['name'] else f"Missionary {i+1}",
                    'photo': missionary['photo']
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
            margin: 0.5in;
        }
        @media print {
            body {
                margin: 0;
                padding: 20px;
            }
            table {
                page-break-inside: avoid;
            }
            .header h1 {
                margin-bottom: 5px;
            }
            .header-subtitle {
                margin-bottom: 10px;
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

if __name__ == "__main__":
    main()
