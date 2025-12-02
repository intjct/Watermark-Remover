import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Gemini Watermark Remover", page_icon="✨", layout="centered")

# --- CSS Theme (Dark Blue & Orange) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    /* Background Colors */
    .stApp > header + div, .stApp, header[data-testid="stHeader"] {
        background-color: #253240 !important;
    }
    div[data-testid="stAppViewContainer"] {
        background-color: #253240 !important;
    }

    /* Typography (Kanit & White) */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stExpander, div[data-testid="stCaptionContainer"] {
        color: white !important;
        font-family: 'Kanit', sans-serif !important;
    }

    /* File Uploader */
    [data-testid='stFileUploader'] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 2px dashed #ffbb4e;
        border-radius: 15px;
        padding: 25px;
    }
    section[data-testid="stFileUploaderDropzone"] > div > span {
         color: #ffbb4e !important;
         font-weight: bold;
    }
    [data-testid="stFileUploader"] svg {
        fill: #ffbb4e !important;
    }
    div[data-testid="stFileUploader"] div, 
    div[data-testid="stFileUploader"] small,
    div[data-testid="stUploadedFileFileName"] {
        color: white !important;
    }
    
    /* Sliders styling */
    .stSlider > div > div > div > div {
        background-color: #ffbb4e !important;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background-color: #ffbb4e !important;
        color: #253240 !important;
        border: none;
        border-radius: 25px;
        padding: 15px 35px;
        font-size: 1.1rem;
        font-weight: bold;
        font-family: 'Kanit', sans-serif !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        background-color: #ffc978 !important;
    }

    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- เนื้อหาหลัก ---

col_head1, col_head2, col_head3 = st.columns([1,2,1])
with col_head2:
    st.title("✨ ลบลายน้ำ Gemini")
    st.write("ปรับตำแหน่งด้วยหลอดเลื่อน (ชัวร์สุด!)")

uploaded_file = st.file_uploader("วางรูปภาพที่นี่ (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # เตรียมภาพ
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    h, w = img_array.shape[:2]

    # --- Smart Scale Logic (คำนวณค่าเริ่มต้นให้) ---
    default_mask_scale = int(w * 0.07) # ประมาณ 7% ของความกว้างรูป
    if default_mask_scale < 50: default_mask_scale = 50
    if default_mask_scale > 200: default_mask_scale = 200
    
    # --- ส่วนควบคุม (Controllers) ---
    st.write("---")
    st.markdown("### 🎛️ ปรับแต่งพื้นที่ลบ")
    
    # 1. ปรับขนาด
    mask_size = st.slider("📐 ขนาดกล่องสี่เหลี่ยม", 30, 300, default_mask_scale)
    
    # 2. ปรับตำแหน่ง (แยก 2 หลอดตามคำขอ)
    col_ctrl1, col_ctrl2 = st.columns(2)
    
    with col_ctrl1:
        # แนวนอน (X Axis)
        # 0 = ชิดขวาสุด, ค่ามาก = เลื่อนไปทางซ้าย
        offset_x = st.slider("↔️ แนวนอน (ซ้าย - ขวา)", 0, 150, 10, help="เลื่อนกรอบไปทางซ้าย")
        
    with col_ctrl2:
        # แนวตั้ง (Y Axis)
        # 0 = ชิดล่างสุด, ค่ามาก = เลื่อนขึ้นบน
        offset_y = st.slider("↕️ แนวตั้ง (ขึ้น - ลง)", 0, 150, 10, help="เลื่อนกรอบขึ้นข้างบน")

    # --- คำนวณตำแหน่ง (Calculations) ---
    # สูตร: เริ่มจากมุมขวาล่าง แล้วลบด้วยค่า offset ที่เราปรับ
    start_x = w - mask_size - offset_x
    start_y = h - mask_size - offset_y
    end_x = w - offset_x
    end_y = h - offset_y
    
    # --- สร้าง Mask และ ประมวลผล ---
    if start_x > 0 and start_y > 0:
        # 1. สร้าง Mask
        mask = np.zeros(img_array.shape[:2], dtype=np.uint8)
        cv2.rectangle(mask, (start_x, start_y), (end_x, end_y), 255, -1)
        
        # 2. เบลอ Mask (เทคนิคขอบฟุ้ง)
        mask_blurred = cv2.GaussianBlur(mask, (35, 35), 0)

        # 3. ลบด้วย AI (Inpaint NS)
        result = cv2.inpaint(img_array, mask_blurred, 10, cv2.INPAINT_NS)

        # --- ส่วนแสดงผล (Preview & Result) ---
        st.write("---")
        st.subheader("👀 ตรวจสอบและดาวน์โหลด")
        
        # สร้างภาพ Preview ที่มีกรอบแดง
        preview_img = img_array.copy()
        # วาดกรอบแดง (Red Box)
        cv2.rectangle(preview_img, (start_x, start_y), (end_x, end_y), (255, 50, 50), 3)

        col_before, col_after = st.columns(2)
        with col_before:
            st.image(preview_img, caption="พื้นที่ลบ (กรอบแดง)", use_column_width=True)
        with col_after:
            st.image(result, caption="ผลลัพธ์ (ลบแล้ว ✨)", use_column_width=True)

        # ปุ่มดาวน์โหลด
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
                file_name="gemini_cleaned_final.png",
                mime="image/png"
            )
    else:
        st.error("⚠️ พื้นที่ลบหลุดออกนอกกรอบภาพ กรุณาปรับค่าลดลง")