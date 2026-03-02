import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import json 

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
SHEET_NAME = "Finance App" 
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

st.markdown("""
    <style>
    div.stButton > button:first-child {
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
# ส่วนที่ 1: ฟอร์มสำหรับกรอกข้อมูล
# ==========================================
st.markdown("### 📝 บันทึกรายการใหม่")

# 💡 สวิตช์เปิด-ปิด โหมดต่างประเทศ (ตัวนี้ตัวเดียวคุมทั้งแอปค่ะ!)
tourist_mode = st.toggle("✈️ โหมดนักท่องเที่ยว (แยกกระเป๋าทริป)")

type_ = st.radio("🔄 ประเภทรายการ", ["รายจ่าย 🔴", "รายรับ 🟢"], horizontal=True)

with st.form("entry_form", clear_on_submit=True):
    date = st.date_input("📅 วันที่")
    
    # ถ้าเปิดโหมดทริป ให้ระบุชื่อทริปด้วย
    if tourist_mode:
        trip_name = st.text_input("🏷️ ชื่อทริป (เช่น Japan 2026)", value="Japan 2026")
    
    if "รายจ่าย" in type_:
        category_options = [
            "🍜 ค่าอาหาร/เครื่องดื่ม",
            "🛍️ ช้อปปิ้ง/ของใช้",
            "⚡ ค่าน้ำ/ค่าไฟ",
            "📱 ค่า Net/Streaming",
            "🧺 ค่าซักผ้า",          
            "🐷 เงินเก็บส่วนกลาง",
            "🏫 ค่าเรียนลูก",
            "🎌 เงินเก็บค่าเที่ยวญี่ปุ่น",
            "🚗 เดินทาง/เติมน้ำมัน",
            "📝 อื่นๆ"
        ]
    else:
        category_options = [
            "💼 เงินเดือน",
            "👫 ค่าส่วนกลางจากปุ๊",
            "🎁 โบนัส/เงินพิเศษ",
            "💸 คืนเงิน/Cashback",
            "📈 ดอกเบี้ย/ปันผล",
            "📝 อื่นๆ"
        ]
        
    category = st.selectbox("🏷️ หมวดหมู่", category_options)
    
    # ช่องกรอกเงินตามโหมดที่เลือก
    if tourist_mode:
        st.markdown("🎌 **ข้อมูลสกุลเงินต่างประเทศ**")
        col_curr, col_rate = st.columns(2)
        with col_curr:
            currency = st.selectbox("สกุลเงิน", ["JPY (เยน)", "USD (ดอลลาร์)"])
        with col_rate:
            exchange_rate = st.number_input("เรทแลกเปลี่ยน", value=None, format="%.4f", step=0.0100, placeholder="ระบุเรท...")
        
        amount_input = st.number_input(f"💰 จำนวนเงิน ({currency.split(' ')[0]})", min_value=0.0, format="%.2f", step=100.0, value=None, placeholder=f"แตะระบุยอด {currency.split(' ')[0]}...")
    else:
        amount_input = st.number_input("💰 จำนวนเงิน (บาท)", min_
