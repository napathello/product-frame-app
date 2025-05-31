import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, zipfile, os
from collections import defaultdict

APP_VERSION = "v1.1.4"
DEFAULT_THAI_FONT = "default_thai_font.ttf"
FRAME_OPTIONS = {
    "กรอบสี่เหลี่ยมจัตุรัส (1:1)": {"file": "frame_1.png", "ratio": "1:1"},
    "กรอบแนวตั้ง (4:5)": {"file": "frame_2.png", "ratio": "4:5"}
}

def crop_to_ratio(img, ratio):
    width, height = img.size
    target_ratio = 1.0 if ratio == "1:1" else 0.8  # 4:5 = 0.8
    current_ratio = width / height
    
    if current_ratio > target_ratio:
        # รูปกว้างเกินไป ต้องครอปด้านข้าง
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        box = (left, 0, left + new_width, height)
    else:
        # รูปสูงเกินไป ต้องครอปด้านบนล่าง
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        box = (0, top, width, top + new_height)
    
    cropped = img.crop(box)
    return cropped

def fit_image_to_frame(img, frame_size):
    """Fit image to frame while maintaining aspect ratio"""
    img_w, img_h = img.size
    frame_w, frame_h = frame_size
    
    # Calculate scaling factor to fit within frame while maintaining aspect ratio
    scale = min(frame_w/img_w, frame_h/img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    
    # Resize image
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Create new image with frame size
    new_img = Image.new('RGBA', frame_size, (0,0,0,0))
    
    # Paste resized image in center
    x = (frame_w - new_w) // 2
    y = (frame_h - new_h) // 2
    new_img.paste(resized, (x, y))
    
    return new_img

st.set_page_config(page_title="Product Frame Generator", layout="centered")

# Custom CSS for styling
st.markdown("""
<style>
    /* ซ่อนปุ่มขยายภาพ */
    button[title="View fullscreen"] {
        display: none !important;
    }
    /* จัดการรูปภาพ */
    .stImage {
        text-align: center;
        position: relative;
    }
    .stImage > img {
        width: 100px;
        margin: auto;
    }
</style>
""", unsafe_allow_html=True)

# แสดงส่วนหัวของแอป
st.title("🖼️ Product Frame Generator")
st.caption(f"เวอร์ชัน {APP_VERSION}")
st.caption("สร้างภาพสินค้าใส่กรอบพร้อมรหัสสินค้า")

# อัปโหลดไฟล์
uploaded_images = st.file_uploader(
    "อัปโหลดภาพสินค้า",
    type=["jpg", "png"],
    accept_multiple_files=True
)

font_size = st.number_input("ขนาดฟอนต์", value=16)

frame_choice = st.selectbox("เลือกกรอบตกแต่ง", list(FRAME_OPTIONS.keys()))
selected_frame = FRAME_OPTIONS[frame_choice]
selected_frame_path = selected_frame["file"]
aspect_ratio = selected_frame["ratio"]

# กรอกรหัสสินค้าครั้งเดียว ใช้กับทุกรูป
product_code = st.text_input("📝 รหัสสินค้า (ใช้กับทุกรูป)", value="")

# แสดงรูปภาพที่อัปโหลด
if uploaded_images:
    st.markdown("### 🖼️ ภาพที่อัปโหลด:")
    
    # คำนวณจำนวนแถวที่ต้องการ (6 รูปต่อแถว)
    images_per_row = 6
    num_rows = (len(uploaded_images) + images_per_row - 1) // images_per_row  # ปัดขึ้นเพื่อให้ได้จำนวนแถวที่ต้องการ
    
    # วนลูปแสดงรูปภาพทีละแถว
    for row in range(num_rows):
        # สร้าง columns สำหรับแต่ละแถว
        start_idx = row * images_per_row
        end_idx = min(start_idx + images_per_row, len(uploaded_images))
        num_images_in_row = end_idx - start_idx
        
        cols = st.columns(images_per_row)
        
        # แสดงรูปภาพในแต่ละ column
        for i, img in enumerate(uploaded_images[start_idx:end_idx]):
            with cols[i]:
                pil_img = Image.open(img).convert("RGBA")
                st.image(pil_img, width=100)
        
        # เติม column ที่เหลือด้วย columns ว่าง (ถ้ามี)
        if num_images_in_row < images_per_row:
            for i in range(num_images_in_row, images_per_row):
                with cols[i]:
                    st.empty()

    # แสดงตัวอย่างรูปพร้อมกรอบและรหัสสินค้า
    st.markdown("##### 👁️ ตัวอย่างรหัสสินค้าบนรูป:")
    
    # สร้างรูปตัวอย่าง
    preview_img = Image.open(uploaded_images[-1]).convert("RGBA")  # ใช้รูปสุดท้ายที่อัปโหลดเป็นตัวอย่าง
    preview_frame = Image.open(selected_frame_path).convert("RGBA")
    
    # ครอปและปรับขนาดรูปตัวอย่าง
    preview_cropped = crop_to_ratio(preview_img, aspect_ratio)
    preview_combined = fit_image_to_frame(preview_cropped, preview_frame.size)
    preview_combined = Image.alpha_composite(preview_combined, preview_frame)
    preview_draw = ImageDraw.Draw(preview_combined)

    # แสดงกล่องสีขาวและรหัสสินค้าเฉพาะเมื่อมีการกรอกรหัสสินค้า
    if product_code.strip():  # ตรวจสอบว่ามีการกรอกรหัสสินค้าหรือไม่
        try:
            preview_font = ImageFont.truetype(DEFAULT_THAI_FONT, font_size, encoding='utf-8')
        except Exception as e:
            st.warning(f"⚠️ ไม่สามารถโหลดฟอนต์ได้: {e}")
            preview_font = ImageFont.load_default()

        # คำนวณขนาดและตำแหน่งข้อความสำหรับพรีวิว
        preview_bbox = preview_draw.textbbox((0, 0), product_code, font=preview_font)
        preview_text_width = preview_bbox[2] - preview_bbox[0]
        preview_text_height = preview_bbox[3] - preview_bbox[1]

        # เพิ่ม padding
        padding_x = 30
        padding_y = 20
        
        # คำนวณขนาดกล่องพื้นหลังขาว
        preview_box_width = preview_text_width + (padding_x * 2)
        preview_box_height = preview_text_height + (padding_y * 2)
        
        # คำนวณตำแหน่งกล่อง
        preview_box_x = preview_combined.width - preview_box_width - 40
        preview_box_y = preview_combined.height - preview_box_height - 115

        # วาดกล่องพื้นหลังขาว
        preview_draw.rounded_rectangle(
            [preview_box_x, preview_box_y, preview_box_x + preview_box_width, preview_box_y + preview_box_height],
            radius=12, fill=(255, 255, 255, 255)
        )

        # คำนวณตำแหน่งข้อความให้อยู่กึ่งกลางกล่อง
        preview_text_x = preview_box_x + ((preview_box_width - preview_text_width) / 2)
        preview_text_y = preview_box_y + ((preview_box_height - preview_text_height) / 2)
        preview_draw.text((preview_text_x, preview_text_y), product_code, font=preview_font, fill=(0, 0, 0, 255))

    # แสดงรูปพรีวิวขนาดใหญ่
    st.image(preview_combined, caption="ตัวอย่างรูปพร้อมรหัสสินค้า", width=600)

if st.button("✅ สร้างภาพพร้อมกรอบ"):
    if uploaded_images:
        with st.spinner('⚙️ กำลังประมวลผลภาพ...'):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
                frame = Image.open(selected_frame_path).convert("RGBA")

                try:
                    font = ImageFont.truetype(DEFAULT_THAI_FONT, font_size, encoding='utf-8')
                    st.info("💡 ใช้ฟอนต์ภาษาไทยพื้นฐาน (IBM Plex Sans Thai)")
                except Exception as e:
                    st.warning(f"⚠️ ไม่สามารถโหลดฟอนต์ได้: {e}")
                    font = ImageFont.load_default()

                # Track used filenames to handle duplicates
                used_filenames = defaultdict(int)

                progress_bar = st.progress(0)
                for idx, uploaded_file in enumerate(uploaded_images):
                    # อัพเดท progress bar
                    progress = (idx + 1) / len(uploaded_images)
                    progress_bar.progress(progress)
                    
                    # สร้างชื่อโฟลเดอร์ตามรหัสสินค้า
                    folder_name = f"frame_{product_code}" if product_code.strip() else "frame_no_code"
                    
                    # Handle duplicate filenames
                    base_filename = f"{product_code if product_code.strip() else 'no_code'}.png"
                    if used_filenames[base_filename] > 0:
                        filename = f"{product_code if product_code.strip() else 'no_code'}_{used_filenames[base_filename]}.png"
                    else:
                        filename = base_filename
                    used_filenames[base_filename] += 1

                    # เพิ่มชื่อโฟลเดอร์เข้าไปในพาธของไฟล์
                    zip_path = f"{folder_name}/{filename}"

                    img = Image.open(uploaded_file).convert("RGBA")
                    
                    # ครอปตามอัตราส่วนที่เลือก
                    cropped = crop_to_ratio(img, aspect_ratio)
                    
                    # ปรับขนาดให้พอดีกับกรอบโดยไม่ยืด
                    combined = fit_image_to_frame(cropped, frame.size)
                    combined = Image.alpha_composite(combined, frame)
                    draw = ImageDraw.Draw(combined)

                    # แสดงกล่องสีขาวและรหัสสินค้าเฉพาะเมื่อมีการกรอกรหัสสินค้า
                    if product_code.strip():
                        # คำนวณตำแหน่งล่างขวา (ไม่ทับกรอบ)
                        margin = 40
                        bottom_margin = 115  # ระยะห่างจากด้านล่าง 115px
                        right_margin = 40  # ระยะห่างจากด้านขวา

                        # คำนวณขนาดข้อความ
                        bbox = draw.textbbox((0, 0), product_code, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]

                        # เพิ่ม padding
                        padding_x = 30  # padding ด้านซ้าย-ขวา
                        padding_y = 20  # padding ด้านบน-ล่าง
                        
                        # คำนวณขนาดกล่องพื้นหลังขาว
                        box_width = text_width + (padding_x * 2)
                        box_height = text_height + (padding_y * 2)
                        
                        # คำนวณตำแหน่งกล่องให้อยู่ด้านขวาล่าง
                        box_x = combined.width - box_width - right_margin
                        box_y = combined.height - box_height - bottom_margin

                        # วาดกล่องพื้นหลังขาว
                        draw.rounded_rectangle([box_x, box_y, box_x + box_width, box_y + box_height], 
                                            radius=12, fill=(255, 255, 255, 255))

                        # คำนวณตำแหน่งข้อความให้อยู่กึ่งกลางกล่องอย่างแม่นยำ
                        text_x = box_x + ((box_width - text_width) / 2)  # จัดกึ่งกลางแนวนอน
                        text_y = box_y + ((box_height - text_height) / 2)  # จัดกึ่งกลางแนวตั้ง
                        draw.text((text_x, text_y), product_code, font=font, fill=(0, 0, 0, 255))

                    img_bytes = io.BytesIO()
                    combined.save(img_bytes, format='PNG')
                    zf.writestr(zip_path, img_bytes.getvalue())

                progress_bar.empty()  # ลบ progress bar เมื่อเสร็จ

        st.success("✅ เสร็จเรียบร้อย! ดาวน์โหลดไฟล์ด้านล่าง")
        st.download_button("📦 ดาวน์โหลดภาพทั้งหมด (ZIP)", data=zip_buffer.getvalue(), file_name="framed_images.zip", mime="application/zip")
    else:
        st.warning("กรุณาอัปโหลดภาพสินค้าให้ครบถ้วนก่อน")