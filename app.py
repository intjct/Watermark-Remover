import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
from streamlit_drawable_canvas import st_canvas

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Gemini Watermark Remover", page_icon="✨", layout="centered")

# --- CSS Theme (Dark Blue & Orange) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    .stApp > header + div, .stApp, header[data-testid="stHeader"] {
        background-color: #253240 !important;
    }
    div[data-testid="stAppViewContainer"] {
        background-color: #253240 !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stExpander {
        color: white !important;
        font-family: 'Kanit', sans-serif !important;
    }
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
    
    /* Slider Styling */
    .stSlider > div > div > div > div {
        background-color: #ffbb4e !important;
    }
    
    /* Button Styling */
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

# --- Helper Function: Resize for Display ---
def resize_image_for_display(image, max_width=700):
    w, h = image.size
    if w > max_width:
        ratio = max_width / w
        new_h = int(h * ratio)
        return image.resize((max_width, new_h)), ratio
    return image, 1.0

# --- Main Logic ---

col_head1, col_head2, col_head3 = st.columns([1,2,1])
with col_head2:
    st.title("✨ ลบลายน้ำ Gemini")
    st.write("ลากกรอบเพื่อย้าย + เลื่อนหลอดเพื่อปรับขนาด")

uploaded_file = st.file_uploader("วางรูปภาพที่นี่ (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 1. จัดการรูปภาพ
    original_image_pil = Image.open(uploaded_file).convert("RGB")
    display_image, scale_factor = resize_image_for_display(original_image_pil)
    d_w, d_h = display_image.size
    
    # ใช้ session state เพื่อจำค่าตำแหน่ง (เมื่อมีการปรับ Slider จะได้ไม่เด้งกลับที่เดิม)
    if 'box_x' not in st.session_state:
        st.session_state['box_x'] = d_w - 85 # ค่าเริ่มต้น (มุมขวา)
    if 'box_y' not in st.session_state:
        st.session_state['box_y'] = d_h - 85 # ค่าเริ่มต้น (มุมล่าง)
    
    # 2. หลอดปรับขนาด (Slider)
    st.write("")
    # คำนวณค่า Default scale
    default_scale = int(d_w * 0.1) 
    if default_scale < 50: default_scale = 50
    
    # Slider ปรับขนาด
    box_size = st.slider("ปรับขนาดพื้นที่ลบ", 30, 200, 75)
    
    # 3. สร้าง JSON สำหรับ Canvas
    # เทคนิค: lockScalingX/Y = True จะทำให้ user ย่อขยายเองไม่ได้ (ต้องใช้ Slider เท่านั้น)
    initial_drawing = {
        "version": "4.4.0",
        "objects": [
            {
                "type": "rect",
                "left": st.session_state['box_x'],
                "top": st.session_state['box_y'],
                "width": box_size,
                "height": box_size,
                "fill": "rgba(255, 0, 0, 0.3)",
                "stroke": "#ffbb4e",
                "strokeWidth": 2,
                "angle": 0,
                "hasControls": False,   # ซ่อนจุดจับย่อขยาย
                "lockScalingX": True,   # ห้ามย่อขยายแนวนอน
                "lockScalingY": True,   # ห้ามย่อขยายแนวตั้ง
                "lockRotation": True    # ห้ามหมุน
            }
        ]
    }

    st.write("👇 **ลากกรอบแดงไปวางทับลายน้ำ (ปรับขนาดที่หลอดด้านบน)**")
    
    # 4. Canvas (Interactive)
    # key ต้องเปลี่ยนตาม box_size เพื่อให้มัน Redraw ขนาดใหม่ทันทีที่เลื่อน Slider
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=2,
        stroke_color="#ffbb4e",
        background_image=display_image,
        update_streamlit=True,
        height=d_h,
        width=d_w,
        drawing_mode="transform",
        initial_drawing=initial_drawing,
        key=f"canvas_{box_size}_{uploaded_file.name}", # Trick: เปลี่ยน key เพื่อบังคับอัปเดตขนาด
    )

    # 5. Logic การลบและอัปเดตตำแหน่ง
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        
        if len(objects) > 0:
            obj = objects[0]
            
            # อัปเดตตำแหน่งล่าสุดลง Session State (เพื่อให้ลากแล้วจำตำแหน่งได้)
            st.session_state['box_x'] = obj["left"]
            st.session_state['box_y'] = obj["top"]
            
            # คำนวณพิกัดจริงบนภาพ Original (Unscaled)
            real_left = int(obj["left"] / scale_factor)
            real_top = int(obj["top"] / scale_factor)
            real_size_w = int(box_size / scale_factor)
            real_size_h = int(box_size / scale_factor)

            # แปลงภาพเพื่อประมวลผล
            img_array = np.array(original_image_pil)
            
            # สร้าง Mask
            mask = np.zeros(img_array.shape[:2], dtype=np.uint8)
            cv2.rectangle(mask, 
                          (real_left, real_top), 
                          (real_left + real_size_w, real_top + real_size_h), 
                          255, -1)
            
            # เบลอ Mask (เพิ่มความเนียน)
            mask_blurred = cv2.GaussianBlur(mask, (35, 35), 0)

            # ลบด้วย AI (Inpaint)
            with st.spinner('⚡ กำลังลบ...'):
                result = cv2.inpaint(img_array, mask_blurred, 10, cv2.INPAINT_NS)

            # แสดงผล
            st.write("---")
            st.subheader("✨ ผลลัพธ์")
            st.image(result, use_column_width=True)

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
                    file_name="gemini_cleaned_hybrid.png",
                    mime="image/png"
                )