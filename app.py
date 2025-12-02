import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Gemini Watermark Remover", page_icon="✨", layout="centered")

# --- 2. CSS (ชุดเดิมที่สวยแล้ว) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    .stApp > header + div, .stApp {
        background-color: #2596be !important;
    }
    div[data-testid="stAppViewContainer"] {
        background-color: #2596be !important;
    }
    h1, h2, h3, h4, h5, h6, p, div, label, span, button, .stMarkdown, .stExpander {
        color: white !important;
        font-family: 'Kanit', sans-serif !important;
    }
    header[data-testid="stHeader"] {
        background-color: #2596be !important;
    }
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
    [data-testid="stFileUploader"] svg {
        display: none;
    }
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
    
    /* ปรับแต่ง Expander ให้ดูกลมกลืน */
    .streamlit-expanderHeader {
        background-color: rgba(0,0,0,0.1) !important;
        border-radius: 10px !important;
        color: white !important;
    }
    
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- 3. เนื้อหาหลัก ---

col_head1, col_head2, col_head3 = st.columns([1,2,1])
with col_head2:
    st.title("✨ ลบลายน้ำ Gemini")
    st.write("ระบบคำนวณขนาดลายน้ำให้อัตโนมัติ")

st.write("---")

uploaded_file = st.file_uploader("วางรูปภาพที่นี่ (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    h, w = img_array.shape[:2]

    # --- 🧠 Logic ใหม่: คำนวณขนาดแบบ Adaptive ---
    # ปกติลายน้ำ Gemini จะกินพื้นที่ประมาณ 6-7% ของความกว้างรูป
    # เราตั้งค่าเริ่มต้นให้มันคำนวณเองเลย
    default_mask_scale = int(w * 0.065) 
    
    # ป้องกันไม่ให้เล็กเกินไป (ถ้ารูปเล็กมาก) หรือใหญ่เกินไป
    if default_mask_scale < 50: default_mask_scale = 50
    if default_mask_scale > 200: default_mask_scale = 200

    # --- ซ่อนการปรับแต่งไว้ใน Expander (ไม่รกตา แต่แก้ได้ถ้าพลาด) ---
    with st.expander("⚙️ ตั้งค่าเพิ่มเติม (กดเมื่อลบไม่หมด)"):
        st.write("ปกติไม่ต้องปรับครับ ระบบคำนวณให้แล้ว แต่ถ้ารูปไหนลบไม่หมด ให้เพิ่มขนาดตรงนี้")
        # Slider นี้จะเริ่มที่ค่าที่คำนวณได้อัตโนมัติ
        mask_size = st.slider("ขนาดพื้นที่ลบ", 40, 300, default_mask_scale)
        offset_adj = st.slider("ขยับตำแหน่ง (เข้า-ออก)", 0, 50, 10)

    # คำนวณตำแหน่ง
    offset_x = offset_adj
    offset_y = offset_adj
    
    mask = np.zeros(img_array.shape[:2], dtype=np.uint8)
    
    start_x = w - mask_size - offset_x
    start_y = h - mask_size - offset_y
    end_x = w - offset_x
    end_y = h - offset_y
    
    # วาดและเบลอ Mask
    if start_x > 0 and start_y > 0:
        cv2.rectangle(mask, (start_x, start_y), (end_x, end_y), 255, -1)
        # เพิ่มความฟุ้งให้มากขึ้นอีกนิด (31,31) เพื่อลดรอยเหลี่ยม
        mask_blurred = cv2.GaussianBlur(mask, (31, 31), 15)

        with st.spinner('⚡ กำลังคำนวณและลบ...'):
            # ใช้ Inpaint รัศมีกว้างขึ้นนิดนึง (5->7) เพื่อกินเนื้อที่รอบๆ มาถมให้เนียน
            result = cv2.inpaint(img_array, mask_blurred, 7, cv2.INPAINT_TELEA)

        # --- แสดงผล ---
        st.write("---")
        
        # ใช้ columns จัดกลางให้ดูดี
        c1, c2, c3 = st.columns([1, 10, 1])
        with c2:
            st.image(result, caption="✨ ผลลัพธ์ (Cleaned)", use_column_width=True)

        # ปุ่มโหลด
        st.write("")
        col_d1, col_d2, col_d3 = st.columns([1,2,1])
        with col_d2:
            result_pil = Image.fromarray(result)
            buf = io.BytesIO()
            result_pil.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 ดาวน์โหลดรูปภาพ",
                data=byte_im,
                file_name="gemini_cleaned_smart.png",
                mime="image/png"
            )
    else:
        st.error("รูปภาพขนาดผิดปกติ ไม่สามารถประมวลผลได้")