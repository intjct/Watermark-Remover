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
    st.write("ปรับตำแหน่ง ซ้าย-ขวา ได้ดั่งใจ")

uploaded_file = st.file_uploader("วางรูปภาพที่นี่ (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # เตรียมภาพ
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    h, w = img_array.shape[:2]

    # --- Smart Scale Logic ---
    default_mask_scale = int(w * 0.07) 
    if default_mask_scale < 50: default_mask_scale = 50
    if default_mask_scale > 200: default_mask_scale = 200
    
    # --- ส่วนควบคุม (Controllers) ---
    st.write("---")
    st.markdown("### 🎛️ ปรับแต่งพื้นที่ลบ")
    
    # 1. ปรับขนาด
    mask_size = st.slider("📐 ขนาดกล่องสี่เหลี่ยม", 30, 300, default_mask_scale)
    
    # 2. ปรับตำแหน่ง (Logic ใหม่: เริ่มที่ 0)
    col_ctrl1, col_ctrl2 = st.columns(2)
    
    # กำหนด "ระยะขอบมาตรฐาน" (Base Margin) ไว้ที่ 10px
    base_margin = 10 
    
    with col_ctrl1:
        # แนวนอน: ลบ = ซ้าย, บวก = ขวา
        move_x = st.slider("↔️ แนวนอน (ซ้าย - ขวา)", -100, 100, 0, help="(-) ไปทางซ้าย, (+) ไปทางขวา")
        
    with col_ctrl2:
        # แนวตั้ง: ลบ = ลง, บวก = ขึ้น
        move_y = st.slider("↕️ แนวตั้ง (ลง - ขึ้น)", -100, 100, 0, help="(-) เลื่อนลง, (+) เลื่อนขึ้น")

    # --- คำนวณตำแหน่ง (Calculations แบบ Relative) ---
    
    # ตำแหน่งมาตรฐาน (Base Position) คือมุมขวาล่าง
    base_x = w - mask_size - base_margin
    base_y = h - mask_size - base_margin
    
    # บวกค่าที่ User ปรับเข้าไปตรงๆ (Logic ตามความรู้สึก)
    # เลื่อนขวา (+) ก็บวก X เพิ่ม
    start_x = base_x + move_x
    
    # เลื่อนขึ้น (+) ก็ลบ Y ออก (เพราะในคอม Y=0 คือบนสุด)
    # แต่เดี๋ยวก่อน! User บอกว่า "บวก = ขวา" (ใน slider)
    # ถ้าแนวตั้ง: เลื่อนขวา (บวก) ควรจะ "ขึ้น" หรือ "ลง"?
    # ปกติ Slider แนวตั้งในใจคน: ขวา/บวก = เพิ่มระดับความสูง (ขึ้น)
    # ดังนั้น:
    start_y = base_y - move_y
    
    end_x = start_x + mask_size
    end_y = start_y + mask_size
    
    # --- สร้าง Mask และ ประมวลผล ---
    # ตรวจสอบขอบเขตภาพ (Boundary Check)
    if end_x > 0 and end_y > 0 and start_x < w and start_y < h:
        
        # 1. สร้าง Mask
        mask = np.zeros(img_array.shape[:2], dtype=np.uint8)
        
        # Clip coordinates ให้อยู่ในภาพเสมอ ป้องกัน Error
        sx = max(0, start_x)
        sy = max(0, start_y)
        ex = min(w, end_x)
        ey = min(h, end_y)
        
        cv2.rectangle(mask, (sx, sy), (ex, ey), 255, -1)
        
        # 2. เบลอ Mask
        mask_blurred = cv2.GaussianBlur(mask, (35, 35), 0)

        # 3. ลบด้วย AI
        # ใช้ Try-Except ป้องกัน Error กรณีลากออกนอกจอจน Mask ว่างเปล่า
        try:
            result = cv2.inpaint(img_array, mask_blurred, 10, cv2.INPAINT_NS)
        except:
            result = img_array # ถ้า Error ให้โชว์รูปเดิมไปก่อน

        # --- ส่วนแสดงผล ---
        st.write("---")
        st.subheader("👀 ตรวจสอบและดาวน์โหลด")
        
        # Preview
        preview_img = img_array.copy()
        cv2.rectangle(preview_img, (sx, sy), (ex, ey), (255, 50, 50), 3)

        col_before, col_after = st.columns(2)
        with col_before:
            st.image(preview_img, caption="พื้นที่ลบ (กรอบแดง)", use_column_width=True)
        with col_after:
            st.image(result, caption="ผลลัพธ์ (ลบแล้ว ✨)", use_column_width=True)

        # Download
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
        st.warning("⚠️ กรอบหลุดออกนอกภาพแล้วครับ ลองเลื่อนกลับมาหน่อยนะ")