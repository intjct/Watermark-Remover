import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Gemini Watermark Remover", page_icon="✨")

st.title("✨ Gemini Watermark Remover (Auto)")
st.markdown("อัปโหลดปุ๊บ ลบให้ปั๊บ! (เฉพาะลายน้ำมุมขวาล่าง)")

# ส่วนอัปโหลดไฟล์
uploaded_file = st.file_uploader("เลือกรูปภาพ (JPG/PNG)", type=["jpg", "jpeg", "png"])

# --- พออัปโหลดเสร็จ ทำงานทันที ---
if uploaded_file is not None:
    # 1. เตรียมภาพ
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    h, w = img_array.shape[:2]

    # แสดงข้อความระหว่างรอ
    with st.spinner('⚡ กำลังลบลายน้ำอัตโนมัติ...'):
        
        # 2. สร้าง Mask ตรงมุมขวาล่าง (กำหนดค่าตายตัว)
        # ขนาด 65px น่าจะพอดีกับดาวของ Gemini
        mask_size = 65  
        offset = 5      # เว้นระยะจากขอบนิดหน่อย

        mask = np.zeros(img_array.shape[:2], dtype=np.uint8)
        # วาดสี่เหลี่ยมสีขาวทับมุมขวาล่าง
        cv2.rectangle(mask, (w - mask_size - offset, h - mask_size - offset), (w, h), 255, -1)

        # 3. ประมวลผลลบ (Inpainting) ทันที
        result = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)

    # 4. แสดงผลลัพธ์
    st.success("เสร็จเรียบร้อย!")
    
    # แสดงภาพเปรียบเทียบ (ถ้าอยากโชว์แค่ภาพผลลัพธ์ให้ลบ col1 ออก)
    col1, col2 = st.columns(2)
    with col1:
        st.image(image, caption="ภาพต้นฉบับ", use_column_width=True)
    with col2:
        st.image(result, caption="✨ ลบแล้ว", use_column_width=True)

    # 5. ปุ่มดาวน์โหลด
    result_pil = Image.fromarray(result)
    buf = io.BytesIO()
    result_pil.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="📥 ดาวน์โหลดรูปภาพที่ลบแล้ว",
        data=byte_im,
        file_name="cleaned_image.png",
        mime="image/png",
        type="primary" # ทำให้ปุ่มเด่นขึ้น
    )