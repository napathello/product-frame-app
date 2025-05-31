# Product Frame Generator

A Streamlit web application for adding frames and product codes to product images.

## Features

- Upload multiple product images
- Two frame styles:
  - Square frame (1:1)
  - Portrait frame (4:5)
- Automatic image cropping to match frame aspect ratio
- Add product code with:
  - Customizable font size
  - White background text box
  - Automatic positioning
- Batch processing with:
  - Multiple image upload
  - Single product code for all images
  - ZIP file download
  - Organized folder structure based on product code
- Modern and clean user interface
- Real-time preview of frame and product code

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
2. Select frame style (1:1 or 4:5)
3. Adjust font size if needed
4. Enter product code (will be applied to all images)
5. Click "สร้างภาพพร้อมกรอบ" to generate
6. Download the ZIP file containing all processed images

## Version

Current version: v1.1.4 