import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import json 
import re  

# ==========================================
# ส่วนตั้งค่าการเชื่อมต่อ Google Sheets
# ==========================================
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def init_connection():
    if "google_credentials" in st.secrets:
        creds_dict = json.loads(st.secrets["google_credentials"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        
    client = gspread.authorize(creds)
    return client

client = init_connection()
SHEET_NAME = "Finance App" # ใช้ชีตหลักของเจ้านาย
sheet = client.open(SHEET_NAME).sheet1

def load_data():
    data = sheet.get_all_records()
    if data:
        return pd.DataFrame(data)
    else:
        return pd.DataFrame(columns=['ลำดับ', 'วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง', 'หมายเหตุ'])

# ==========================================
# การตั้งค่าหน้าเว็บและสีสัน
# ==========================================
st.set_page_config(page_title="ระบบจัดการรายรับ-รายจ่าย", layout="centered")

# 💡 อัปเดต CSS ให้ปุ่มสีสวยขึ้นและเต็มจอในมือถือ
st.markdown("""
    <style>
    /* ซ่อนหัวข้อช่องกรอกเสียงเพื่อให้ดูคลีนขึ้น */
    div[data-testid="stTextInput"] label {
        display: none;
    }
    /* ปรับแต่งปุ่มบันทึกด้านล่างสุด */
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        font-size: 18px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💸 แอปรายรับ-รายจ่าย ประจำวัน")

df = load_data()

# ==========================================
# ส่วนที่ 1: ระบบสั่งงานด้วยเสียง (Voice Magic Input)
# ==========================================
# เตรียมหน่วยความจำให้แอป
if 'pre_type' not in st.session_state: st.session_state.pre_type = "รายจ่าย 🔴"
if 'pre_amount' not in st.session_state: st.session_state.pre_amount = None
if 'pre_cat' not in st.session_state: st.session_state.pre_cat = "🍜 ค่าอาหาร/เครื่องดื่ม"
if 'pre_chan' not in st.session_state: st.session_state.pre_chan = " 💵 เงินสด "
if 'pre_note' not in st.session_state: st.session_state.pre_note = ""

# ฟังก์ชันสำหรับล้างข้อความ
def clear_voice_text():
    st.session_state.voice_input_key = ""

st.markdown("### 🎙️ สั่งงานด้วยเสียง (Magic Input)")
st.info("💡 **วิธีใช้:** แตะที่ช่องด้านล่าง กดไมค์ที่คีย์บอร์ดเพื่อพูด (หรือแก้คำผิด) แล้วกดปุ่ม ✨ แยกคำ")

# ช่องรับข้อความเสียง (เก็บค่าลง session_state ทันที)
voice_input = st.text_input("ข้อความเสียง:", key="voice_input_key", placeholder="แตะที่นี่แล้วพูด... เช่น: รายจ่ายค่าอาหาร 150 บาท...")

# จัดเรียงปุ่ม 3 ปุ่มให้อยู่แถวเดียวกัน
col1, col2, col3 = st.columns(3)
with col1:
    speak_btn = st.button("🎙️ กดเพื่อพูด", use_container_width=True)
with col2:
    process_btn = st.button("✨ แยกคำ", use_container_width=True)
with col3:
    # ปุ่มสีแดง (type="primary" จะดึงสีหลักของธีมมาใช้ ซึ่งมักจะเป็นสีแดง/ชมพู)
    clear_btn = st.button("❌ ล้างคำ", type="primary", use_container_width=True, on_click=clear_voice_text)

# ระบบประมวลผลคำพูด
if process_btn and st.session_state.voice_input_key:
    text = st.session_state.voice_input_key.lower()
    
    # 1. แกะประเภท (Type)
    if "รายรับ" in text:
        st.session_state.pre_type = "รายรับ 🟢"
    else:
        st.session_state.pre_type = "รายจ่าย 🔴"
        
    # 2. แกะหมายเหตุ (Note)
    if "หมายเหตุ" in text:
        parts = text.split("หมายเหตุ", 1)
        st.session_state.pre_note = parts[1].strip()
        text_to_search = parts[0] 
    else:
        st.session_state.pre_note = "" 
        text_to_search = text
        
    # 3. แกะจำนวนเงิน (Amount)
    amounts = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', text_to_search)
    if amounts:
        st.session_state.pre_amount = float(amounts[0].replace(',', ''))
        
    # 4. แกะหมวดหมู่ (Category)
    if "อาหาร" in text_to_search or "กิน" in text_to_search or "ข้าว" in text_to_search or "กาแฟ" in text_to_search:
        st.session_state.pre_cat = "🍜 ค่าอาหาร/เครื่องดื่ม"
    elif "เดินทาง" in text_to_search or "รถ" in text_to_search or "น้ำมัน" in text_to_search or "bts" in text_to_search:
        st.session_state.pre_cat = "🚗 เดินทาง/เติมน้ำมัน"
    elif "ช้อปปิ้ง" in text_to_search or "ของใช้" in text_to_search or "ซื้อ" in text_to_search or "เซเว่น" in text_to_search:
        st.session_state.pre_cat = "🛍️ ช้อปปิ้ง/ของใช้"
    elif "น้ำ" in text_to_search or "ไฟ" in text_to_search:
        st.session_state.pre_cat = "⚡ ค่าน้ำ/ค่าไฟ"
    elif "เน็ต" in text_to_search or "net" in text_to_search or "สตรีมมิ่ง" in text_to_search:
        st.session_state.pre_cat = "📱 ค่า Net/Streaming"
    elif "ซักผ้า" in text_to_search:
        st.session_state.pre_cat = "🧺 ค่าซักผ้า"
    elif "ลูก" in text_to_search or "เรียน" in text_to_search:
        st.session_state.pre_cat = "🏫 ค่าเรียนลูก"
    elif "เงินเดือน" in text_to_search:
        st.session_state.pre_cat = "💼 เงินเดือน"
    else:
        st.session_state.pre_cat = "📝 อื่นๆ"

    # 5. แกะช่องทาง (Channel)
    if "kbank" in text_to_search or "กสิกร" in text_to_search or "เคแบงก์" in text_to_search:
        st.session_state.pre_chan = "🟢 K-BANK"
    elif "scb" in text_to_search or "ไทยพาณิชย์" in
