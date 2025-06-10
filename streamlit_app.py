import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from collections import defaultdict

# --- Configuration ---
APP_VERSION = "v1.1.5"
DEFAULT_THAI_FONT = "default_thai_font.ttf" # Ensure this font file is in the same directory
FRAME_OPTIONS = {
    "กรอบสี่เหลี่ยมจัตุรัส (1:1)": {"file": "frame_1.png", "ratio": "1:1"},
    "กรอบแนวตั้ง (4:5)": {"file": "frame_2.png", "ratio": "4:5"},
    "กรอบ 1:1 (ลายน้ำ)": {"file": "frame_3.png", "ratio": "1:1"},
    "กรอบ 4:5 (ลายน้ำ)": {"file": "frame_4.png", "ratio": "4:5"}
}

# --- Image Processing Functions ---

def crop_to_ratio(img, ratio):
    """Crops the image to the specified aspect ratio (e.g., "1:1", "4:5")."""
    width, height = img.size
    target_ratio = 1.0 if ratio == "1:1" else 0.8  # 4:5 = 0.8
    current_ratio = width / height

    if current_ratio > target_ratio:
        # Image is too wide, crop the sides
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        box = (left, 0, left + new_width, height)
    else:
        # Image is too tall, crop the top and bottom
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        box = (0, top, width, top + new_height)

    cropped = img.crop(box)
    return cropped

def fit_image_to_frame(img, frame_size):
    """Fits the image into the frame size while maintaining the aspect ratio."""
    img_w, img_h = img.size
    frame_w, frame_h = frame_size

    # Calculate scaling factor
    scale = min(frame_w / img_w, frame_h / img_h)
    new_w, new_h = int(img_w * scale), int(img_h * scale)

    # Resize image
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Create a new blank image with the frame's dimensions
    new_img = Image.new('RGBA', frame_size, (0, 0, 0, 0))

    # Paste the resized image into the center of the blank image
    x = (frame_w - new_w) // 2
    y = (frame_h - new_h) // 2
    new_img.paste(resized, (x, y))

    return new_img

def add_product_code_box(draw, image_size, text, font):
    """Draws a white box with the product code at the bottom right."""
    if not text.strip():
        return

    # --- Calculate Text and Box Size ---
    # Bounding box for the text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Padding for the box
    padding_x = 30
    padding_y = 20

    # Box dimensions
    box_width = text_width + (padding_x * 2)
    box_height = text_height + (padding_y * 2)

    # --- Calculate Position ---
    # Margins from the edge of the image
    bottom_margin = 115
    right_margin = 40

    # Box position (top-left corner)
    box_x = image_size[0] - box_width - right_margin
    box_y = image_size[1] - box_height - bottom_margin

    # --- Draw Elements ---
    # Draw the rounded white rectangle
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_width, box_y + box_height],
        radius=12,
        fill=(255, 255, 255, 255)
    )

    # Text position (centered within the box)
    text_x = box_x + padding_x
    text_y = box_y + padding_y - (text_bbox[1]) # Adjust for font's internal top bearing
    
    # Draw the text
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0, 255))


# --- Streamlit App UI ---
st.set_page_config(page_title="Product Frame Generator", layout="centered")

# Custom CSS for styling
st.markdown("""
<style>
    /* Hide the fullscreen button on images */
    button[title="View fullscreen"] {
        display: none !important;
    }
    /* Center the small preview images */
    .stImage {
        text-align: center;
    }
    .stImage > img {
        width: 100px; /* Control size of thumbnail previews */
        margin: auto;
    }
</style>
""", unsafe_allow_html=True)


# --- Header ---
st.title("🖼️ Product Frame Generator")
st.caption(f"เวอร์ชัน {APP_VERSION}")
st.caption("สร้างภาพสินค้าใส่กรอบพร้อมรหัสสินค้า")


# --- User Inputs ---
uploaded_images = st.file_uploader(
    "อัปโหลดภาพสินค้า (รองรับหลายไฟล์)",
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=True
)

col1, col2 = st.columns(2)
with col1:
    frame_choice = st.selectbox("เลือกกรอบตกแต่ง", list(FRAME_OPTIONS.keys()))
with col2:
    font_size = st.number_input("ขนาดฟอนต์", value=36, min_value=10, max_value=200)

product_code = st.text_input("📝 รหัสสินค้า (จะถูกนำไปใช้กับทุกรูป)", value="")


# --- Main Logic ---
if uploaded_images:
    selected_frame_info = FRAME_OPTIONS[frame_choice]
    selected_frame_path = selected_frame_info["file"]
    aspect_ratio = selected_frame_info["ratio"]

    # --- Display Uploaded Thumbnails ---
    st.markdown("---")
    st.markdown("### 🖼️ ภาพที่อัปโหลด:")
    cols = st.columns(6) # Display up to 6 thumbnails per row
    for i, img_file in enumerate(uploaded_images):
        with cols[i % 6]:
            st.image(img_file, width=100)

    # --- Display Live Preview ---
    st.markdown("---")
    st.markdown("##### 👁️ ตัวอย่าง:")
    try:
        # Use the last uploaded image for the preview
        preview_img_file = uploaded_images[-1]
        preview_img = Image.open(preview_img_file).convert("RGBA")
        preview_frame = Image.open(selected_frame_path).convert("RGBA")

        # Process the preview image
        preview_cropped = crop_to_ratio(preview_img, aspect_ratio)
        preview_combined = fit_image_to_frame(preview_cropped, preview_frame.size)
        preview_combined = Image.alpha_composite(preview_combined, preview_frame)
        preview_draw = ImageDraw.Draw(preview_combined)

        # Load font for preview
        try:
            preview_font = ImageFont.truetype(DEFAULT_THAI_FONT, font_size)
        except IOError:
            st.warning(f"⚠️ ไม่พบไฟล์ฟอนต์ '{DEFAULT_THAI_FONT}' กำลังใช้ฟอนต์เริ่มต้น")
            preview_font = ImageFont.load_default()

        # Add product code to preview
        add_product_code_box(preview_draw, preview_combined.size, product_code, preview_font)

        # Display the final preview image
        st.image(preview_combined, caption="ตัวอย่างรูปที่จะได้ (อาจแตกต่างจากภาพจริงเล็กน้อย)", use_column_width=True)

    except FileNotFoundError:
        st.error(f"❌ ไม่พบไฟล์กรอบ '{selected_frame_path}'! กรุณาตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์เดียวกับโปรแกรม")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการสร้างตัวอย่าง: {e}")

    # --- Generate Button ---
    st.markdown("---")
    if st.button("✅ สร้างภาพทั้งหมด", use_container_width=True, type="primary"):
        with st.spinner('⚙️ กำลังประมวลผลภาพทั้งหมด... กรุณารอสักครู่...'):
            try:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
                    # Load frame and font once
                    frame = Image.open(selected_frame_path).convert("RGBA")
                    try:
                        font = ImageFont.truetype(DEFAULT_THAI_FONT, font_size)
                    except IOError:
                        font = ImageFont.load_default()

                    progress_bar = st.progress(0, text="เริ่มต้น...")
                    total_images = len(uploaded_images)

                    for idx, uploaded_file in enumerate(uploaded_images):
                        # Update progress bar
                        progress_percentage = (idx + 1) / total_images
                        progress_text = f"กำลังประมวลผลภาพที่ {idx + 1}/{total_images}..."
                        progress_bar.progress(progress_percentage, text=progress_text)

                        # Create a unique filename based on product code and original filename
                        original_filename = uploaded_file.name.split('.')[0]
                        code_prefix = product_code.strip() if product_code.strip() else 'image'
                        new_filename = f"{code_prefix}_{original_filename}.png"

                        # Process each image
                        img = Image.open(uploaded_file).convert("RGBA")
                        cropped = crop_to_ratio(img, aspect_ratio)
                        combined = fit_image_to_frame(cropped, frame.size)
                        combined = Image.alpha_composite(combined, frame)
                        draw = ImageDraw.Draw(combined)

                        # Add product code box
                        add_product_code_box(draw, combined.size, product_code, font)

                        # Save image to a bytes buffer
                        img_bytes = io.BytesIO()
                        combined.save(img_bytes, format='PNG')
                        img_bytes.seek(0)

                        # Write image to zip file
                        zf.writestr(new_filename, img_bytes.getvalue())

                progress_bar.empty() # Remove progress bar on completion
                st.success("✅ สร้างภาพทั้งหมดเสร็จเรียบร้อย!")
                
                # --- Download Button ---
                st.download_button(
                    label="📦 ดาวน์โหลดภาพทั้งหมด (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"framed_{product_code.strip() or 'images'}.zip",
                    mime="application/zip",
                    use_container_width=True
                )

            except FileNotFoundError:
                st.error(f"❌ ไม่พบไฟล์กรอบ '{selected_frame_path}'! ไม่สามารถสร้างภาพได้")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดร้ายแรงระหว่างการประมวลผล: {e}")

else:
    st.info("☝️ กรุณาอัปโหลดภาพสินค้าเพื่อเริ่มต้น")
