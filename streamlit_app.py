import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, zipfile, os

APP_VERSION = "v1.0.0"

st.set_page_config(page_title="Product Frame Generator", layout="centered")
st.title(f"🖼 Product Frame Generator  \n:gray[เวอร์ชัน {APP_VERSION}]")
st.caption("สร้างภาพสินค้าใส่กรอบ พร้อมรหัส ด้วยเว็บแอปแบบง่ายๆ")

uploaded_images = st.file_uploader("📂 อัปโหลดภาพสินค้า (รองรับหลายภาพ)", type=["jpg", "png"], accept_multiple_files=True)
uploaded_frame = st.file_uploader("🖼 อัปโหลดกรอบ (frame.png)", type=["png"])
uploaded_font = st.file_uploader("🔤 อัปโหลดฟอนต์ (.ttf)", type=["ttf"])
font_size = st.number_input("ขนาดฟอนต์", value=40)
pos_x = st.number_input("ตำแหน่ง X ของรหัส", value=30)
pos_y = st.number_input("ตำแหน่ง Y ของรหัส", value=1050)

# กรอกข้อมูลรหัสสินค้า
product_codes = {}
if uploaded_images:
    st.markdown("### ✍️ กรอกรหัสสินค้าสำหรับแต่ละภาพ:")
    for img in uploaded_images:
        default_code = os.path.splitext(img.name)[0]
        code = st.text_input(f"รหัสสำหรับ {img.name}", value=default_code)
        product_codes[img.name] = code

if st.button("✅ สร้างภาพพร้อมกรอบ"):
    if uploaded_images and uploaded_frame:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
            frame = Image.open(uploaded_frame).convert("RGBA")

            try:
                if uploaded_font:
                    font = ImageFont.truetype(uploaded_font, font_size)
                else:
                    font = ImageFont.load_default()
                    st.info("💡 ไม่มีฟอนต์ที่อัปโหลด → ใช้ฟอนต์เริ่มต้นของระบบ")
            except Exception as e:
                st.warning(f"⚠️ ฟอนต์ไม่สามารถโหลดได้: {e}")
                font = ImageFont.load_default()

            for uploaded_file in uploaded_images:
                product = Image.open(uploaded_file).convert("RGBA").resize(frame.size)
                combined = Image.alpha_composite(product, frame)

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