import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_image_coordinates import streamlit_image_coordinates
import io, zipfile, os

APP_VERSION = "v1.0.3"
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

# กรอกข้อมูลรหัสสินค้า
product_codes = {}
crop_boxes = {}

if uploaded_images:
    st.markdown("### ✍️ กรอกรหัสสินค้าและเลือกตำแหน่งครอป (Crop Box):")
    for img in uploaded_images:
        default_code = os.path.splitext(img.name)[0]
        code = st.text_input(f"รหัสสำหรับ {img.name}", value=default_code)
        product_codes[img.name] = code

        st.markdown(f"#### 📍 Crop พื้นที่สำหรับ: {img.name}")
        pil_img = Image.open(img)
        coords = streamlit_image_coordinates(pil_img, key=img.name)
        if coords:
            x, y = coords["x"], coords["y"]
            w = st.number_input(f"ความกว้างของ Crop Box สำหรับ {img.name}", min_value=10, max_value=pil_img.width, value=pil_img.width // 2, key=img.name+"w")
            h = st.number_input(f"ความสูงของ Crop Box สำหรับ {img.name}", min_value=10, max_value=pil_img.height, value=pil_img.height // 2, key=img.name+"h")
            crop_boxes[img.name] = (x, y, x + w, y + h)

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
                    cropped = img.crop(box)
                else:
                    cropped = img
                cropped = cropped.resize(frame.size)
                combined = Image.alpha_composite(cropped, frame)
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
