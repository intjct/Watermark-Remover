import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Gemini Watermark Remover", page_icon="✨", layout="centered")

# --- 2. CSS ชุดใหม่ (แก้สี, แก้ตัวอักษรทับ, ปรับปุ่มส้ม) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    /* --- Main Background Colors (#253240) --- */
    .stApp > header + div, .stApp, header[data-testid="stHeader"] {
        background-color: #253240 !important;
    }
    div[data-testid="stAppViewContainer"] {
        background-color: #253240 !important;
    }

    /* --- Typography (Kanit & White Text) --- */
    /* เลือกเฉพาะ Element ที่จำเป็น เพื่อป้องกัน Layout พังแล้วตัวหนังสือทับกัน */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stExpander {
        color: white !important;
        font-family: 'Kanit', sans-serif !important;
    }

    /* --- File Uploader Styling (Orange Accent) --- */
    [data-testid='stFileUploader'] {
        background-color: rgba(255, 255, 255, 0.05); /* พื้นหลังจางๆ */
        border: 2px dashed #ffbb4e; /* ขอบสีส้ม */
        border-radius: 15px;
        padding: 25px;
    }
    section[data-testid="stFileUploaderDropzone"] > div > span {
         color: #ffbb4e !important; /* ตัวหนังสือ "Drag and drop..." สีส้ม */
         font-weight: bold;
    }
    [data-testid="stFileUploader"] svg {
        fill: #ffbb4e !important; /* เปลี่ยนสีไอคอนเป็นส้ม */
    }
    
    /* --- Download Button Styling (Orange #ffbb4e) --- */
    .stDownloadButton > button {
        background-color: #ffbb4e !important;
        color: #253240 !important; /* ตัวหนังสือสีเข้มบนปุ่มส้ม */
        border: none;
        border-radius: 25px;
        padding: 15px 35px;
        font-size: 1.1rem;
        font-weight: bold;
        font-family: 'Kanit', sans-serif !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(255, 187, 78, 0.3); /* เงาสีส้ม */
        background-color: #ffc978 !important; /* ส้มอ่อนลงนิดนึงตอน Hover */
    }

    /* --- Expander Styling --- */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px !important;
        color: #ffbb4e !important; /* หัวข้อ Expander สีส้ม */
    }
    /* แก้ไข slider สีส้ม */
    .stSlider > div > div > div > div {
        background-color: #ffbb4e !important;
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

    # --- Expander ตั้งค่า (แก้ไข UI แล้ว) ---
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
        # สร้าง Mask
        cv2.rectangle(mask, (start_x, start_y), (end_x, end_y), 255, -1)
        # เบลอ Mask (เพิ่มความฟุ้งอีกนิด)
        mask_blurred = cv2.GaussianBlur(mask, (35, 35), 0)

        with st.spinner('⚡ กำลังใช้พลัง AI ลบลายน้ำ...'):
            # --- เปลี่ยนอัลกอริทึม! ---
            # ใช้ INPAINT_NS (Navier-Stokes) แทน TELEA 
            # และเพิ่ม Radius เป็น 10 เพื่อให้กินวงกว้างขึ้น เนียนขึ้นกับพื้นผิวหมอก
            result = cv2.inpaint(img_array, mask_blurred, 10, cv2.INPAINT_NS)

        # --- แสดงผลแบบ Before / After (แก้แล้ว) ---
        st.write("---")
        st.subheader("📊 เปรียบเทียบผลลัพธ์")
        
        col_before, col_after = st.columns(2)
        with col_before:
            st.image(image, caption="Before (ต้นฉบับ)", use_column_width=True)
        with col_after:
            st.image(result, caption="After (ลบแล้ว ✨)", use_column_width=True)

        # ปุ่มดาวน์โหลดสีส้ม
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
                file_name="gemini_cleaned_pro.png",
                mime="image/png"
            )
    else:
        st.error("รูปภาพขนาดผิดปกติ ไม่สามารถประมวลผลได้")