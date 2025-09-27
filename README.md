# Missionary Meal Planner

A Streamlit application for creating visual meal planner schedules for missionary companionships. This app allows you to input missionary information, photos, and dates to generate a professional-looking meal planner image.

## Features

- **Multiple Companionships**: Support for 1-10 missionary companionships
- **Photo Integration**: Upload photos for each missionary
- **Phone Numbers**: Add phone numbers for each companionship
- **Date Management**: Set dates for each day of the week
- **Table Format**: Clean table layout with lines for manual entry
- **Professional Output**: Generates a styled image using WeasyPrint
- **Easy Download**: Download the generated planner as a PNG image

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone <repository-url>
cd missionary-meal-planner

# Install dependencies with uv
uv sync

# Run the app
uv run streamlit run streamlit_app.py
```

### Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

## Deployment on Streamlit Cloud

1. Push your code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set the main file path to `streamlit_app.py`
5. Add the following secrets if needed:
   - No API keys required for this application

## System Dependencies

For PDF to PNG conversion, you may need to install poppler-utils:

```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Windows
# Download from: https://blog.alivate.com.au/poppler-windows/
```

## Usage

1. **Set Companionship Count**: Use the sidebar to set the number of companionships
2. **Add Missionary Information**:
   - Upload photos for each missionary
   - Enter names for each missionary
   - Add phone numbers for each companionship
3. **Set Dates**: Enter dates for each day of the week
4. **Generate**: Click "Generate Meal Planner" to create the image
5. **Download**: Download the generated image as a PNG file

## Project Structure

```
missionary-meal-planner/
├── streamlit_app.py          # Main Streamlit application
├── templates/
│   └── meal_planner.html     # HTML template for the planner
├── pyproject.toml            # Project configuration (uv)
├── requirements.txt          # Python dependencies (pip)
└── README.md                 # This file
```

## Dependencies

- **streamlit**: Web app framework
- **weasyprint**: HTML to PDF conversion
- **pillow**: Image processing
- **jinja2**: HTML templating
- **pdf2image**: PDF to image conversion
- **reportlab**: Fallback PDF generation
- **python-dateutil**: Date utilities

## Troubleshooting

### Common Issues

1. **PDF to PNG conversion fails**:
   - Ensure poppler-utils is installed
   - Check that pdf2image can find the poppler binaries

2. **Font rendering issues**:
   - The app will fallback to default fonts if system fonts are not available
   - Install DejaVu fonts for better rendering: `sudo apt-get install fonts-dejavu`

3. **Large image uploads**:
   - Images are automatically resized to 200x200 pixels
   - Supported formats: PNG, JPG, JPEG

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the application
5. Submit a pull request

## License

This project is open source and available under the MIT License.
