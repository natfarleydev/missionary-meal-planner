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

# Page configuration
st.set_page_config(
    page_title="Missionary Meal Planner",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #ecf0f1;
        border-radius: 5px;
    }
    .companionship-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .missionary-input {
        display: flex;
        gap: 1rem;
        align-items: center;
        margin-bottom: 1rem;
    }
    .photo-upload {
        flex: 0 0 100px;
    }
    .name-input {
        flex: 1;
    }
    .date-inputs {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    .date-input {
        padding: 0.5rem;
        border: 1px solid #ddd;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header">🍽️ Missionary Meal Planner</div>', unsafe_allow_html=True)

    # Initialize session state
    if 'companionships_data' not in st.session_state:
        st.session_state.companionships_data = []
    if 'num_companionships' not in st.session_state:
        st.session_state.num_companionships = 2
    if 'dates' not in st.session_state:
        st.session_state.dates = {}
    if 'generated_image' not in st.session_state:
        st.session_state.generated_image = None

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
            st.rerun()

        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown("""
        1. Set the number of companionships
        2. Upload photos and enter names for each missionary
        3. Enter dates for each day of the week
        4. Click 'Generate Meal Planner' to create the image
        """)

    # Main content
    st.markdown('<div class="section-header">📸 Missionary Information</div>', unsafe_allow_html=True)

    # Initialize companionships data structure
    while len(st.session_state.companionships_data) < num_companionships:
        st.session_state.companionships_data.append({
            'missionaries': [{'name': '', 'photo': None} for _ in range(2)],
            'phone_number': '',
            'schedule': []
        })

    # Input forms for each companionship
    for i in range(num_companionships):
        with st.container():
            st.markdown(f"""
            <div class="companionship-card">
            <h4>Companionship {i + 1}</h4>
            </div>
            """, unsafe_allow_html=True)

            # Missionary inputs
            missionaries_data = []
            cols = st.columns(2)
            for j in range(2):
                with cols[j]:
                    st.markdown(f"**Missionary {j + 1}**")

                    # Photo upload
                    photo = st.file_uploader(
                        f"Photo for Missionary {j + 1}",
                        type=['png', 'jpg', 'jpeg'],
                        key=f"photo_{i}_{j}",
                        help="Upload a clear photo of the missionary"
                    )

                    # Name input
                    name = st.text_input(
                        f"Name of Missionary {j + 1}",
                        value=st.session_state.companionships_data[i]['missionaries'][j]['name'],
                        key=f"name_{i}_{j}",
                        placeholder="Enter missionary name"
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
                        'name': name,
                        'photo': photo_path
                    })

            # Phone number input
            phone_number = st.text_input(
                f"Phone Number for Companionship {i + 1}",
                value=st.session_state.companionships_data[i]['phone_number'],
                key=f"phone_{i}",
                placeholder="Enter phone number"
            )

            # Update session state
            st.session_state.companionships_data[i]['missionaries'] = missionaries_data
            st.session_state.companionships_data[i]['phone_number'] = phone_number

    # Date inputs section
    st.markdown('<div class="section-header">📅 Weekly Schedule</div>', unsafe_allow_html=True)

    st.markdown("Enter the dates for each day of the week:")

    # This should be defined at the top of the function or as a global variable
    days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    date_cols = st.columns(7)
    for i, day in enumerate(days_of_week):
        with date_cols[i]:
            date_value = st.session_state.dates.get(day, datetime.now().date())
            date_input = st.date_input(
                day,
                value=date_value,
                key=f"date_{day}",
                label_visibility="collapsed"
            )
            st.session_state.dates[day] = date_input

    # Generate button
    if st.button("🍽️ Generate Meal Planner", type="primary", use_container_width=True):
        generate_meal_planner()

    # Display generated image if available
    if st.session_state.generated_image:
        st.markdown('<div class="section-header">📋 Generated Meal Planner</div>', unsafe_allow_html=True)

        # Display the image
        st.image(st.session_state.generated_image, use_column_width=True)

        # Download button
        st.download_button(
            label="💾 Download Image",
            data=st.session_state.generated_image,
            file_name="missionary_meal_planner.png",
            mime="image/png",
            use_container_width=True
        )

def generate_meal_planner():
    """Generate the meal planner image using WeasyPrint"""
    days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

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

        # Convert PDF to PNG using PIL/PDF2Image if available
        try:
            from pdf2image import convert_from_path
            images = convert_from_path("temp_planner.pdf", dpi=150)
            if images:
                # Save first page as PNG
                temp_img_path = "temp_planner.png"
                images[0].save(temp_img_path, "PNG")

                # Read the generated PNG
                with open(temp_img_path, "rb") as f:
                    image_data = f.read()

                # Clean up temp file
                try:
                    os.remove(temp_img_path)
                except:
                    pass
            else:
                raise Exception("No images generated from PDF")
        except ImportError:
            # Fallback: create a simple text-based image
            from PIL import Image, ImageDraw, ImageFont

            # Create a simple image
            img = Image.new('RGB', (800, 1000), color='white')
            draw = ImageDraw.Draw(img)

            # Try to use a system font
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()

            y_position = 50

            # Title
            draw.text((50, y_position), "Missionary Meal Planner", fill='black', font=font_large)
            y_position += 50

            # Create table header
            draw.text((50, y_position), "Missionary Dinner List", fill='black', font=font_large)
            y_position += 40
            draw.text((50, y_position), "Please write your name, time and telephone number", fill='black', font=font_small)
            y_position += 50

            # Draw table headers
            headers = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            header_y = y_position
            x_pos = 50

            for header in headers:
                draw.text((x_pos, header_y), header, fill='black', font=font_medium)
                x_pos += 100

            y_position += 40

            # Draw rows for each companionship (one row per companionship)
            for i, comp in enumerate(companionships):
                row_y = y_position

                # Draw companionship info (left column) - both missionaries
                y_offset = 0
                for j, missionary in enumerate(comp['missionaries']):
                    name = missionary['name'] or f"Missionary {j+1}"
                    draw.text((60, row_y + y_offset), name, fill='black', font=font_small)
                    y_offset += 15

                # Draw phone number
                draw.text((60, row_y + y_offset + 5), comp['phone_number'], fill='black', font=font_small)

                # Draw day columns (simple lines)
                x_pos = 150
                for day in headers[1:]:  # Skip empty header
                    # Draw three lines for name, time, phone
                    line_y = row_y + 10
                    for line in range(3):
                        draw.line((x_pos + 10, line_y, x_pos + 80, line_y), fill='black', width=1)
                        line_y += 20

                    x_pos += 100

                y_position += 80

            # Save image
            img.save("temp_planner.png")

            # Read the generated PNG
            with open("temp_planner.png", "rb") as f:
                image_data = f.read()

        # Store in session state
        st.session_state.generated_image = image_data

        # Clean up temp files
        try:
            os.remove("temp_planner.pdf")
            os.remove("temp_planner.png")
        except:
            pass

        st.success("✅ Meal planner generated successfully!")

    except Exception as e:
        st.error(f"❌ Error generating meal planner: {str(e)}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
