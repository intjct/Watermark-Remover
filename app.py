import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Auto Watermark Remover", page_icon="🤖")

st.title("🤖 Auto AI Watermark Remover")
st.markdown("โหมดอัตโนมัติ: เลือกลบตามตำแหน่ง (เหมาะกับรูปจาก AI เช่น DALL-E)")

# 1. ส่วนอัปโหลดไฟล์
uploaded_file = st.file_uploader("เลือกรูปภาพ (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    
    # แสดงรูปต้นฉบับ
    st.image(image, caption="ภาพต้นฉบับ", use_column_width=True)

    st.write("---")
    st.write("### ⚙️ เลือกตำแหน่งที่จะลบอัตโนมัติ")

    # ตัวเลือกตำแหน่งลายน้ำ
    option = st.radio(
        "ลายน้ำอยู่ที่ไหน?",
        ("มุมขวาล่าง (DALL-E Style)", "มุมซ้ายล่าง", "มุมขวาบน", "มุมซ้ายบน", "แถบล่างทั้งหมด")
    )
    
    # ตัวปรับขนาดพื้นที่ที่จะลบ (เผื่อลายน้ำใหญ่/เล็ก)
    mask_size = st.slider("ปรับขนาดพื้นที่ที่จะลบ (px)", 30, 150, 70)

    if st.button("🚀 ลบอัตโนมัติทันที"):
        # สร้างหน้ากาก (Mask) สีดำทั้งแผ่น
        mask = np.zeros(img_array.shape[:2], dtype=np.uint8)
        h, w = img_array.shape[:2]
        
        # กำหนดพื้นที่สีขาว (ส่วนที่จะลบ) ตามที่เลือก
        offset = 10 # ระยะห่างจากขอบเล็กน้อย
        
        if option == "มุมขวาล่าง (DALL-E Style)":
            # สร้างสี่เหลี่ยมสีขาวที่มุมขวาล่าง
            cv2.rectangle(mask, (w - mask_size - offset, h - mask_size - offset), (w, h), 255, -1)
            
        elif option == "มุมซ้ายล่าง":
            cv2.rectangle(mask, (0, h - mask_size - offset), (mask_size + offset, h), 255, -1)
            
        elif option == "มุมขวาบน":
            cv2.rectangle(mask, (w - mask_size - offset, 0), (w, mask_size + offset), 255, -1)
            
        elif option == "มุมซ้ายบน":
            cv2.rectangle(mask, (0, 0), (mask_size + offset, mask_size + offset), 255, -1)
            
        elif option == "แถบล่างทั้งหมด":
            cv2.rectangle(mask, (0, h - mask_size), (w, h), 255, -1)

        # --- ประมวลผลลบ (Inpainting) ---
        # ใช้ Radius 5 เพื่อให้เกลี่ยสีได้เนียนขึ้น
        result = cv2.inpaint(img_array, mask, 5, cv2.INPAINT_TELEA)

        # แสดงผลลัพธ์
        st.success("ลบเรียบร้อย!")
        st.image(result, caption="ภาพผลลัพธ์", use_column_width=True)

        # เตรียมปุ่มดาวน์โหลด
        result_pil = Image.fromarray(result)
        buf = io.BytesIO()
        result_pil.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="📥 ดาวน์โหลดรูปภาพ",
            data=byte_im,
            file_name="auto_cleaned_image.png",
            mime="image/png"
        )