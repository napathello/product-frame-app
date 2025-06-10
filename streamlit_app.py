import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from collections import defaultdict

# --- Configuration ---
# กำหนดเวอร์ชันของแอปพลิเคชัน
APP_VERSION = "v1.1.6" # อัปเดตเวอร์ชัน
# กำหนดชื่อไฟล์ฟอนต์ภาษาไทยเริ่มต้น (ต้องแน่ใจว่าไฟล์นี้อยู่ในไดเรกทอรีเดียวกันกับสคริปต์)
DEFAULT_THAI_FONT = "default_thai_font.ttf" 
# ตัวเลือกกรอบและอัตราส่วนภาพ
FRAME_OPTIONS = {
    "กรอบสี่เหลี่ยมจัตุรัส (1:1)": {"file": "frame_1.png", "ratio": "1:1"},
    "กรอบแนวตั้ง (4:5)": {"file": "frame_2.png", "ratio": "4:5"},
    "กรอบ 1:1 (ลายน้ำ)": {"file": "frame_3.png", "ratio": "1:1"},
    "กรอบ 4:5 (ลายน้ำ)": {"file": "frame_4.png", "ratio": "4:5"}
}

# --- Image Processing Functions ---

def crop_to_ratio(img, ratio):
    """
    ครอบตัดรูปภาพให้เป็นอัตราส่วนที่กำหนด (เช่น "1:1", "4:5")
    Args:
        img (PIL.Image.Image): วัตถุรูปภาพ PIL
        ratio (str): อัตราส่วนที่ต้องการ เช่น "1:1", "4:5"
    Returns:
        PIL.Image.Image: รูปภาพที่ถูกครอบตัด
    """
    width, height = img.size
    # กำหนดอัตราส่วนเป้าหมาย (4:5 = 0.8)
    target_ratio = 1.0 if ratio == "1:1" else 0.8  
    current_ratio = width / height

    if current_ratio > target_ratio:
        # รูปภาพกว้างเกินไป ให้ครอบตัดด้านข้าง
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        box = (left, 0, left + new_width, height)
    else:
        # รูปภาพสูงเกินไป ให้ครอบตัดด้านบนและด้านล่าง
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        box = (0, top, width, top + new_height)

    cropped = img.crop(box)
    return cropped

def fit_image_to_frame(img, frame_size):
    """
    ปรับขนาดรูปภาพให้พอดีกับขนาดกรอบโดยยังคงรักษาอัตราส่วน
    Args:
        img (PIL.Image.Image): วัตถุรูปภาพ PIL
        frame_size (tuple): ขนาดของกรอบ (width, height)
    Returns:
        PIL.Image.Image: รูปภาพที่ปรับขนาดและจัดวางในกรอบ
    """
    img_w, img_h = img.size
    frame_w, frame_h = frame_size

    # คำนวณอัตราส่วนการปรับขนาด
    scale = min(frame_w / img_w, frame_h / img_h)
    new_w, new_h = int(img_w * scale), int(img_h * scale)

    # ปรับขนาดรูปภาพ
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # สร้างรูปภาพเปล่าใหม่ที่มีขนาดเท่ากรอบ
    new_img = Image.new('RGBA', frame_size, (0, 0, 0, 0))

    # วางรูปภาพที่ปรับขนาดแล้วไว้ตรงกลางของรูปภาพเปล่า
    x = (frame_w - new_w) // 2
    y = (frame_h - new_h) // 2
    new_img.paste(resized, (x, y))

    return new_img

def add_product_code_box(draw, image_size, text, font):
    """
    วาดกล่องสีขาวพร้อมรหัสสินค้าที่มุมขวาล่างของรูปภาพ
    Args:
        draw (PIL.ImageDraw.ImageDraw): วัตถุ ImageDraw
        image_size (tuple): ขนาดของรูปภาพ (width, height)
        text (str): ข้อความรหัสสินค้า
        font (PIL.ImageFont.FreeTypeFont): วัตถุฟอนต์
    """
    if not text.strip():
        return

    # --- Calculate Text and Box Size ---
    # ขนาดของข้อความ
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Padding สำหรับกล่อง
    padding_x = 30
    padding_y = 20

    # ขนาดของกล่อง
    box_width = text_width + (padding_x * 2)
    box_height = text_height + (padding_y * 2)

    # --- Calculate Position ---
    # ระยะขอบจากขอบรูปภาพ
    bottom_margin = 115
    right_margin = 40

    # ตำแหน่งของกล่อง (มุมบนซ้าย)
    box_x = image_size[0] - box_width - right_margin
    box_y = image_size[1] - box_height - bottom_margin

    # --- Draw Elements ---
    # วาดสี่เหลี่ยมสีขาวมุมโค้ง
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_width, box_y + box_height],
        radius=12,
        fill=(255, 255, 255, 255)
    )

    # ตำแหน่งข้อความ (จัดกึ่งกลางในกล่อง)
    text_x = box_x + padding_x
    text_y = box_y + padding_y - (text_bbox[1]) # ปรับสำหรับค่า top bearing ของฟอนต์
    
    # วาดข้อความ
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0, 255))


# --- Streamlit App UI ---
# กำหนดค่าหน้าเพจของ Streamlit
st.set_page_config(page_title="Product Frame Generator", layout="centered")

# Custom CSS สำหรับการจัดสไตล์
st.markdown("""
<style>
    /* ซ่อนปุ่ม fullscreen บนรูปภาพ */
    button[title="View fullscreen"] {
        display: none !important;
    }
    /* จัดกึ่งกลางรูปภาพพรีวิวขนาดเล็ก */
    .stImage {
        text-align: center;
    }
    .stImage > img {
        width: 100px; /* ควบคุมขนาดของรูปภาพย่อ */
        margin: auto;
    }
</style>
""", unsafe_allow_html=True)


# --- Header ---
st.title("🖼️ Product Frame Generator")
st.caption(f"เวอร์ชัน {APP_VERSION}")
st.caption("สร้างภาพสินค้าใส่กรอบพร้อมรหัสสินค้า")


# --- User Inputs ---
# อัปโหลดรูปภาพสินค้า
uploaded_images = st.file_uploader(
    "อัปโหลดภาพสินค้า (รองรับหลายไฟล์)",
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=True
)

# จัดแบ่งหน้าจอเป็น 2 คอลัมน์สำหรับตัวเลือกกรอบและขนาดฟอนต์
col1, col2 = st.columns(2)
with col1:
    frame_choice = st.selectbox("เลือกกรอบตกแต่ง", list(FRAME_OPTIONS.keys()))
with col2:
    font_size = st.number_input("ขนาดฟอนต์", value=36, min_value=10, max_value=200)

# ช่องป้อนรหัสสินค้า
product_code = st.text_input("📝 รหัสสินค้า (จะถูกนำไปใช้กับทุกรูป)", value="")


# --- Main Logic ---
if uploaded_images:
    selected_frame_info = FRAME_OPTIONS[frame_choice]
    selected_frame_path = selected_frame_info["file"]
    aspect_ratio = selected_frame_info["ratio"]

    # --- Display Uploaded Thumbnails ---
    st.markdown("---")
    st.markdown("### 🖼️ ภาพที่อัปโหลด:")
    cols = st.columns(6) # แสดงรูปภาพย่อสูงสุด 6 รูปต่อแถว
    for i, img_file in enumerate(uploaded_images):
        with cols[i % 6]:
            st.image(img_file, width=100)

    # --- Display Live Preview ---
    st.markdown("---")
    st.markdown("##### 👁️ ตัวอย่าง:")
    try:
        # ใช้รูปภาพที่อัปโหลดล่าสุดสำหรับพรีวิว
        preview_img_file = uploaded_images[-1]
        preview_img = Image.open(preview_img_file).convert("RGBA")
        preview_frame = Image.open(selected_frame_path).convert("RGBA")

        # ประมวลผลรูปภาพพรีวิว
        preview_cropped = crop_to_ratio(preview_img, aspect_ratio)
        preview_combined = fit_image_to_frame(preview_cropped, preview_frame.size)
        preview_combined = Image.alpha_composite(preview_combined, preview_frame)
        preview_draw = ImageDraw.Draw(preview_combined)

        # โหลดฟอนต์สำหรับพรีวิว
        try:
            preview_font = ImageFont.truetype(DEFAULT_THAI_FONT, font_size)
        except IOError:
            st.warning(f"⚠️ ไม่พบไฟล์ฟอนต์ '{DEFAULT_THAI_FONT}' กำลังใช้ฟอนต์เริ่มต้น")
            preview_font = ImageFont.load_default()

        # เพิ่มรหัสสินค้าลงในพรีวิว
        add_product_code_box(preview_draw, preview_combined.size, product_code, preview_font)

        # แสดงรูปภาพพรีวิวสุดท้าย (แก้ไขจาก use_column_width เป็น use_container_width)
        st.image(preview_combined, caption="ตัวอย่างรูปที่จะได้ (อาจแตกต่างจากภาพจริงเล็กน้อย)", use_container_width=True)

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
                    # โหลดกรอบและฟอนต์เพียงครั้งเดียวเพื่อประสิทธิภาพ
                    frame = Image.open(selected_frame_path).convert("RGBA")
                    try:
                        font = ImageFont.truetype(DEFAULT_THAI_FONT, font_size)
                    except IOError:
                        font = ImageFont.load_default()

                    progress_bar = st.progress(0, text="เริ่มต้น...")
                    total_images = len(uploaded_images)

                    for idx, uploaded_file in enumerate(uploaded_images):
                        # อัปเดตแถบความคืบหน้า
                        progress_percentage = (idx + 1) / total_images
                        progress_text = f"กำลังประมวลผลภาพที่ {idx + 1}/{total_images}..."
                        progress_bar.progress(progress_percentage, text=progress_text)

                        # สร้างชื่อไฟล์ที่ไม่ซ้ำกันโดยใช้รหัสสินค้าและชื่อไฟล์เดิม
                        original_filename = uploaded_file.name.split('.')[0]
                        code_prefix = product_code.strip() if product_code.strip() else 'image'
                        new_filename = f"{code_prefix}_{original_filename}.png"

                        # ประมวลผลรูปภาพแต่ละภาพ
                        img = Image.open(uploaded_file).convert("RGBA")
                        cropped = crop_to_ratio(img, aspect_ratio)
                        combined = fit_image_to_frame(cropped, frame.size)
                        combined = Image.alpha_composite(combined, frame)
                        draw = ImageDraw.Draw(combined)

                        # เพิ่มกล่องรหัสสินค้า
                        add_product_code_box(draw, combined.size, product_code, font)

                        # บันทึกรูปภาพลงใน buffer ของไบต์
                        img_bytes = io.BytesIO()
                        combined.save(img_bytes, format='PNG')
                        img_bytes.seek(0)

                        # เขียนรูปภาพลงในไฟล์ zip
                        zf.writestr(new_filename, img_bytes.getvalue())

                progress_bar.empty() # ลบแถบความคืบหน้าเมื่อเสร็จสิ้น
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
