import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Gemini Watermark Remover", page_icon="✨", layout="centered")

# --- 2. ส่วนกำหนด CSS (ปรับปรุงใหม่ให้สีติดชัวร์) ---
st.markdown(
    """
    <style>
    # Import ฟอนต์ Kanit
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    # เปลี่ยนสีพื้นหลัง (ใช้ Selector ที่เจาะจงขึ้น)
    .stApp > header + div, .stApp {
        background-color: #2596be !important;
    }
    
    # บังคับให้ Container หลักเป็นสีเดียวกัน
    div[data-testid="stAppViewContainer"] {
        background-color: #2596be !important;
    }

    # กำหนดให้ Text ทุกอย่างเป็นสีขาว และใช้ฟอนต์ Kanit
    h1, h2, h3, h4, h5, h6, p, div, label, span, button, .stMarkdown {
        color: white !important;
        font-family: 'Kanit', sans-serif !important;
    }
    
    # แก้สี header ด้านบนสุด (ถ้ามี)
    header[data-testid="stHeader"] {
        background-color: #2596be !important;
    }

    # ปรับแต่ง File Uploader
    [data-testid='stFileUploader'] {
        background-color: rgba(255, 255, 255, 0.15);
        border: 2px dashed rgba(255, 255, 255, 0.5);
        border-radius: 15px;
        padding: 30px;
    }
    section[data-testid="stFileUploaderDropzone"] > div > span {
         color: white !important;
         font-weight: bold;
    }
    # ซ่อน icon เล็กๆ ตรง uploader ที่สีไม่เข้าพวก
    [data-testid="stFileUploader"] svg {
        display: none;
    }
    
    # ปรับปุ่ม Download ให้เด่นสวยงาม
    .stDownloadButton > button {
        background-color: white !important;
        color: #2596be !important;
        border: none;
        border-radius: 25px;
        padding: 15px 30px;
        font-size: 1.1rem;
        font-weight: bold;
        font-family: 'Kanit', sans-serif !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        background-color: #f0f0f0 !important;
    }
    
    # ซ่อน footer ของ streamlit
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- 3. ส่วนเนื้อหาหลักของ App ---

# จัดวางหัวข้อให้อยู่ตรงกลาง
col_head1, col_head2, col_head3 = st.columns([1,2,1])
with col_head2:
    st.title("✨ ลบลายน้ำ Gemini (Auto)")
    st.write("อัปโหลดปุ๊บ ลบให้ปั๊บ! (เฉพาะมุมขวาล่าง)")

st.write("---")

# ส่วนอัปโหลดไฟล์
uploaded_file = st.file_uploader("วางรูปภาพที่นี่ (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # เตรียมภาพ
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    h, w = img_array.shape[:2]

    # --- การตั้งค่า Auto (Fix ค่าตายตัว ไม่ต้องมี Slider) ---
    # ค่าเหล่านี้ทดสอบแล้วว่าครอบคลุมลายน้ำ Gemini ส่วนใหญ่
    mask_size_w = 90  # ความกว้างพื้นที่ลบ
    mask_size_h = 70  # ความสูงพื้นที่ลบ
    offset_x = 5      # ระยะห่างจากขอบขวา
    offset_y = 5      # ระยะห่างจากขอบล่าง

    # สร้าง Mask สีดำ
    mask = np.zeros(img_array.shape[:2], dtype=np.uint8)
    
    # คำนวณตำแหน่งสี่เหลี่ยมมุมขวาล่าง
    start_x = w - mask_size_w - offset_x
    start_y = h - mask_size_h - offset_y
    end_x = w - offset_x
    end_y = h - offset_y
    
    # วาดสี่เหลี่ยมสีขาวลงใน Mask
    cv2.rectangle(mask, (start_x, start_y), (end_x, end_y), 255, -1)
    
    # --- 🔥 ทีเด็ด: ทำให้ขอบฟุ้ง (แก้ปัญหารอยลบเหลี่ยม) ---
    # ใช้ Gaussian Blur กับ Mask เพื่อให้ขอบขาวค่อยๆ ไล่เฟดเป็นดำ
    # (21, 21) คือขนาด kernel ยิ่งเยอะยิ่งฟุ้ง
    mask_blurred = cv2.GaussianBlur(mask, (21, 21), 11)

    # --- ประมวลผลลบ (Inpainting) ---
    with st.spinner('⚡ กำลังใช้พลัง AI ลบลายน้ำ...'):
        # ใช้ mask ที่เบลอแล้วในการลบ
        result = cv2.inpaint(img_array, mask_blurred, 3, cv2.INPAINT_TELEA)

    # --- แสดงผลลัพธ์ (แบบ Before / After สวยๆ) ---
    st.write("---")
    st.subheader("🎉 ผลลัพธ์")
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.image(image, caption="Before (ต้นฉบับ)", use_column_width=True)
    with col_res2:
        st.image(result, caption="After (ลบแล้ว ✨)", use_column_width=True)

    # ปุ่มดาวน์โหลด (จัดให้อยู่ตรงกลาง)
    st.write("")
    st.write("")
    col_d1, col_d2, col_d3 = st.columns([1,2,1])
    with col_d2:
        result_pil = Image.fromarray(result)
        buf = io.BytesIO()
        result_pil.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        st.download_button(
            label="📥 ดาวน์โหลดรูปภาพ HD",
            data=byte_im,
            file_name="gemini_cleaned.png",
            mime="image/png"
        )