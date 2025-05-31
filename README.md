# Product Frame Generator

A Streamlit web application for adding frames and product codes to multiple images simultaneously.

## Features

- Upload multiple product images
- Apply custom frame to all images
- Advanced image cropping:
  - Pre-crop with aspect ratio selection (1:1, 4:5, 3:4, 9:16)
  - Manual crop area selection with mouse
  - Adjustable crop box dimensions
  - Option to skip cropping per image
  - Visual crop preview
- Add product codes with customizable:
  - Font (TTF support with IBM Plex Sans Thai as default)
  - Font size
  - Text position (X, Y coordinates)
- Image aspect ratio options (1:1, 4:5, 3:4, 9:16, or original)
- Download all processed images in a ZIP file

## Requirements

- Python 3.x
- Streamlit
- Pillow (PIL)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/product-frame-app.git
cd product-frame-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run streamlit_app.py
```

## Usage

1. Upload your product images (JPG/PNG)
2. Upload your frame image (PNG with transparency)
3. (Optional) Upload a custom TTF font
4. Adjust font size and text position
5. Enter product codes for each image
6. Click "สร้างภาพพร้อมกรอบ" to generate
7. Download the ZIP file containing all processed images

## Version

Current version: v1.0.4 