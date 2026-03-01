import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import json

# ==========================================
# ส่วนตั้งค่าการเชื่อมต่อ (เหมือนเดิม)
# ==========================================
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def init_connection():
    if "google_credentials" in st.secrets:
        creds_dict = json.loads(st.secrets["google_credentials"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    return gspread.authorize(creds)

client = init_connection()
SHEET_NAME = "Finance App" 
sheet = client.open(SHEET_NAME).sheet1

# ==========================================
# ปรับแต่ง UI ให้สวยงามพรีเมียม (CSS)
# ==========================================
st.set_page_config(page_title="My Finance App", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
    }
    .stApp {
        background: linear-gradient(180deg, #1a1c23 0%, #2d3436 100%);
    }
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00b894, #00cec9);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: 0.3s;
    }
    .stRadio > div {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💎 บันทึกรายรับ-รายจ่าย")

# ==========================================
# ฟอร์มบันทึกข้อมูล (ปรับปรุง UX)
# ==========================================
type_ = st.radio("ประเภทรายการ", ["รายจ่าย 🔴", "รายรับ 🟢"], horizontal=True)

with st.form("entry_form", clear_on_submit=True):
    date = st.date_input("📅 วันที่")
    
    if "รายจ่าย" in type_:
        category_options = ["🍜 ค่าอาหาร/เครื่องดื่ม", "🛍️ ช้อปปิ้ง/ของใช้", "⚡ ค่าน้ำ/ค่าไฟ", "📱 ค่า Net/Streaming", "🧺 ค่าซักผ้า", "🐷 เงินเก็บส่วนกลาง", "🏫 ค่าเรียนลูก", "🎌 เงินเก็บค่าเที่ยวญี่ปุ่น", "🚗 เดินทาง/เติมน้ำมัน", "📝 อื่นๆ"]
    else:
        category_options = ["💼 เงินเดือน", "👫 ค่าส่วนกลางจากปุ๊", "🎁 โบนัส/เงินพิเศษ", "💸 คืนเงิน/Cashback", "📈 ดอกเบี้ย/ปันผล", "📝 อื่นๆ"]
        
    category = st.selectbox("🏷️ หมวดหมู่", category_options)
    
    # 💡 แก้ไขข้อ 2: ใช้ value=None เพื่อให้ช่องว่างเปล่าตอนเริ่มต้น แตะแล้วพิมพ์ได้เลย!
    amount = st.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, step=100.0, value=None, placeholder="ระบุจำนวนเงิน...")
    
    if amount:
        st.markdown(f"<span style='color:#00cec9; font-size:18px;'>✨ ยอดเงิน: <b>{amount:,.2f}</b> บาท</span>", unsafe_allow_html=True)
    
    # 💡 แก้ไขข้อ 4: เรียงลำดับช่องทางใหม่
    channel_options = ["💳 Credit Card", "🦅 KTB", "🟢 K-BANK", "🟣 SCB", "💵 เงินสด", "📝 อื่นๆ"]
    channel = st.radio("🏦 ช่องทาง", channel_options, horizontal=True)
    
    note = st.text_input("📝 หมายเหตุ (ถ้ามี)")

    if st.form_submit_button("บันทึกข้อมูล"):
        if amount is None or amount <= 0:
            st.error("⚠️ เจ้านายระบุจำนวนเงินด้วยนะคะ")
        else:
            all_values = sheet.get_all_values()
            next_id = len(all_values)
            income_amt = amount if "รายรับ" in type_ else ""
            expense_amt = amount if "รายจ่าย" in type_ else ""
            date_str = date.strftime("%Y-%m-%d")
            sheet.append_row([next_id, date_str, category, income_amt, expense_amt, channel, note])
            st.success("บันทึกเรียบร้อยค่ะ!")
            st.rerun()

# ==========================================
# Dashboard (เหมือนเดิม)
# ==========================================
# ... (ส่วน Dashboard กราฟโดนัทคงเดิม)
