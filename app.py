import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Gemini Watermark Remover", page_icon="✨", layout="centered")

# --- 2. CSS ชุดแก้ไขล่าสุด (แก้สี Expander, ชื่อไฟล์, และธีม) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    /* --- Background Colors --- */
    .stApp > header + div, .stApp, header[data-testid="stHeader"] {
        background-color: #253240 !important;
    }
    div[data-testid="stAppViewContainer"] {
        background-color: #253240 !important;
    }

    /* --- Typography (White & Kanit) --- */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: white !important;
        font-family: 'Kanit', sans-serif !important;
    }

    /* --- File Uploader Styling --- */
    [data-testid='stFileUploader'] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 2px dashed #ffbb4e;
        border-radius: 15px;
        padding: 25px;
    }
    /* แก้สีตัวอักษร "Drag and drop..." */
    section[data-testid="stFileUploaderDropzone"] > div > span {
         color: #ffbb4e !important;
         font-weight: bold;
    }
    /* แก้สีไอคอน */
    [data-testid="stFileUploader"] svg {
        fill: #ffbb4e !important;
    }
    /* 🔥 แก้สีชื่อไฟล์ที่อัปโหลดเสร็จแล้วให้เป็นสีขาว (สำคัญ!) */
    div[data-testid="stFileUploader"] div, 
    div[data-testid="stFileUploader"] small,
    div[data-testid="stUploadedFileFileName"] {
        color: white !important;
    }

    /* --- Expander Styling (สีส้ม) --- */
    /* แก้สีตัวหนังสือหัวข้อ Expander */
    .streamlit-expanderHeader p, .streamlit-expanderHeader {
        color: #ffbb4e !important;
        font-weight: 600;
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 187, 78, 0.3);
        border-radius: 10px !important;
    }
    /* แก้สีลูกศร Expander */
    .streamlit-expanderHeader svg {
        fill: #ffbb4e !important;
        color: #ffbb4e !important;
    }
    
    /* --- Slider & Button --- */
    .stSlider > div > div > div > div {
        background-color: #ffbb4e !important;
    }
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

    # --- Smart Scale Logic ---
    default_mask_scale = int(w * 0.065) 
    if default_mask_scale < 50: default_mask_scale = 50
    if default_mask_scale > 200: default_mask_scale = 200

    # --- Expander ตั้งค่า (แก้ไขสีหัวข้อแล้ว) ---
    with st.expander("⚙️ ตั้งค่าเพิ่มเติม (กดเมื่อลบไม่หมด)"):
        st.write("ปรับขนาดหากลบไม่หมด หรือกินเนื้อที่มากเกินไป")
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
    
    if start_x > 0 and start_y > 0:
        # สร้าง Mask สำหรับลบ
        cv2.rectangle(mask, (start_x, start_y), (end_x, end_y), 255, -1)
        # เบลอ Mask (เพื่อความเนียน)
        mask_blurred = cv2.GaussianBlur(mask, (35, 35), 0)

        with st.spinner('⚡ กำลังใช้พลัง AI ลบลายน้ำ...'):
            # ใช้ INPAINT_NS เพื่อความเนียนของ Texture
            result = cv2.inpaint(img_array, mask_blurred, 10, cv2.INPAINT_NS)

        # --- ส่วนแสดงผล ---
        st.write("---")
        st.subheader("📊 เปรียบเทียบผลลัพธ์")
        
        # 🔥 สร้างภาพ Preview ที่มีกรอบแดง (ตามคำขอ)
        preview_img = img_array.copy()
        # วาดกรอบสี่เหลี่ยมสีแดง (Red Bounding Box)
        # (0, 0, 255) คือสีแดงใน OpenCV (BGR), 3 คือความหนา
        cv2.rectangle(preview_img, (start_x, start_y), (end_x, end_y), (255, 50, 50), 3)

        col_before, col_after = st.columns(2)
        with col_before:
            # แสดงภาพที่มีกรอบแดง เพื่อให้รู้ว่าลบตรงไหน
            st.image(preview_img, caption="Before (กรอบแดงคือส่วนที่ลบ)", use_column_width=True)
        with col_after:
            st.image(result, caption="After (ลบแล้ว ✨)", use_column_width=True)

        # ปุ่มดาว