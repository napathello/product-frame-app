import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_image_coordinates import streamlit_image_coordinates
import io, zipfile, os

APP_VERSION = "v1.0.4"
DEFAULT_THAI_FONT = "default_thai_font.ttf"

st.set_page_config(page_title="Product Frame Generator", layout="centered")
st.title(f"🖼 Product Frame Generator  \n:gray[เวอร์ชัน {APP_VERSION}]")
st.caption("สร้างภาพสินค้าใส่กรอบ พร้อมรหัส ด้วยเว็บแอปแบบง่ายๆ (รองรับ Manual Crop ด้วย Mouse)")

uploaded_images = st.file_uploader("📂 อัปโหลดภาพสินค้า (รองรับหลายภาพ)", type=["jpg", "png"], accept_multiple_files=True)
uploaded_frame = st.file_uploader("🖼 อัปโหลดกรอบ (frame.png)", type=["png"])
uploaded_font = st.file_uploader("🔤 อัปโหลดฟอนต์ (.ttf)", type=["ttf"])
font_size = st.number_input("ขนาดฟอนต์", value=40)
pos_x = st.number_input("ตำแหน่ง X ของรหัส", value=30)
pos_y = st.number_input("ตำแหน่ง Y ของรหัส", value=1050)
aspect_ratio = st.selectbox("เลือกอัตราส่วนที่ต้องการครอป (ก่อนลากเมาส์)", ["1:1", "4:5", "3:4", "9:16", "ต้นฉบับ"])

# กรอกข้อมูลรหัสสินค้า
product_codes = {}
crop_boxes = {}

def crop_to_aspect_manual(img, target_ratio):
    width, height = img.size
    current_ratio = width / height
    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        box = (left, 0, left + new_width, height)
    else:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        box = (0, top, width, top + new_height)
    return img.crop(box)

ratio_map = {
    "1:1": 1.0,
    "4:5": 4/5,
    "3:4": 3/4,
    "9:16": 9/16
}

if uploaded_images:
    st.markdown("### ✍️ กรอกรหัสสินค้าและเลือกตำแหน่งครอป (Crop Box):")
    for img in uploaded_images:
        default_code = os.path.splitext(img.name)[0]
        code = st.text_input(f"รหัสสำหรับ {img.name}", value=default_code)
        product_codes[img.name] = code

        st.markdown(f"#### 📍 Crop สำหรับ: {img.name}")
        pil_img = Image.open(img)

        # ครอปตามอัตราส่วนที่เลือกก่อน
        if aspect_ratio != "ต้นฉบับ":
            pil_img = crop_to_aspect_manual(pil_img, ratio_map[aspect_ratio])

        # UI crop ด้วย mouse
        st.markdown("🖱️ ลาก Mouse เพื่อเลือกตำแหน่งเริ่มต้นของ Crop Box หรือกดข้าม")
        coords = streamlit_image_coordinates(pil_img, key=img.name)

        skip_crop = st.checkbox(f"ข้ามการครอปภาพนี้ ({img.name})", key="skip_"+img.name)

        if coords and not skip_crop:
            x, y = coords["x"], coords["y"]
            w = st.number_input(f"ความกว้าง Crop สำหรับ {img.name}", min_value=10, max_value=pil_img.width, value=pil_img.width // 2, key=img.name+"w")
            h = st.number_input(f"ความสูง Crop สำหรับ {img.name}", min_value=10, max_value=pil_img.height, value=pil_img.height // 2, key=img.name+"h")
            crop_boxes[img.name] = (x, y, x + w, y + h)
        elif skip_crop:
            crop_boxes[img.name] = None  # ใช้ภาพเต็มไม่ครอป

if st.button("✅ สร้างภาพพร้อมกรอบ"):
    if uploaded_images and uploaded_frame:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
            frame = Image.open(uploaded_frame).convert("RGBA")
            try:
                if uploaded_font:
                    font = ImageFont.truetype(uploaded_font, font_size)
                else:
                    font = ImageFont.truetype(DEFAULT_THAI_FONT, font_size)
                    st.info("💡 ไม่มีฟอนต์ที่อัปโหลด → ใช้ฟอนต์ภาษาไทยพื้นฐาน (IBM Plex Sans Thai)")
            except Exception as e:
                st.warning(f"⚠️ ฟอนต์ไม่สามารถโหลดได้: {e}")
                font = ImageFont.load_default()

            for uploaded_file in uploaded_images:
                img = Image.open(uploaded_file).convert("RGBA")
                box = crop_boxes.get(uploaded_file.name)
                if box:
                    img = img.crop(box)
                img = img.resize(frame.size)
                combined = Image.alpha_composite(img, frame)
                draw = ImageDraw.Draw(combined)
                code = product_codes.get(uploaded_file.name, "UNKNOWN")
                draw.text((pos_x, pos_y), f"รหัส: {code}", font=font, fill=(0, 0, 0, 255))
                img_bytes = io.BytesIO()
                combined.save(img_bytes, format='PNG')
                zf.writestr(f"{code}.png", img_bytes.getvalue())

        st.success("✅ เสร็จเรียบร้อย! ดาวน์โหลดไฟล์ด้านล่าง")
        st.download_button("📦 ดาวน์โหลดภาพทั้งหมด (ZIP)", data=zip_buffer.getvalue(), file_name="framed_images.zip", mime="application/zip")
    else:
        st.warning("กรุณาอัปโหลดภาพสินค้าและไฟล์กรอบให้ครบถ้วนก่อน")
