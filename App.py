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
    return pd.DataFrame(data) if data else pd.DataFrame(columns=['ลำดับ', 'วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง', 'หมายเหตุ'])

# ==========================================
# ✨ การตกแต่ง UI สไตล์ใหม่ สดใสเพื่อมือถือ
# ==========================================
st.set_page_config(page_title="บันทึกรายรับ-รายจ่าย", layout="centered")

# CSS สำหรับปรับฟอนต์และพื้นหลังไล่เฉดสีฟ้า
st.markdown("""
    <style>
    /* พื้นหลัง Gradient สีฟ้าสดใส */
    .stApp {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        background-attachment: fixed;
    }
    
    /* ปรับขนาดตัวหนังสือหลักให้เล็กลงกะทัดรัด */
    html, body, [class*="css"]  {
        font-size: 15px; 
        color: #0c4a6e;
    }
    
    /* ปรับแต่งกล่อง Form ให้ดูนุ่มนวล */
    .stForm {
        background-color: rgba(255, 255, 255, 0.7) !important;
        border-radius: 15px !important;
        border: 1px solid #7dd3fc !important;
        padding: 15px !important;
    }

    /* ปุ่มกดสีเขียวมินต์ */
    div.stButton > button:first-child {
        background-color: #0ea5e9;
        color: white;
        border-radius: 12px;
        border: none;
        width: 100%;
        height: 45px;
        font-weight: bold;
    }
    
    /* หัวข้อ Title */
    h1 {
        color: #0369a1 !important;
        font-size: 24px !important;
        text-align: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 บันทึกรายรับ-รายจ่าย")

df = load_data()

# ==========================================
# ส่วนที่ 1: บันทึกรายการใหม่
# ==========================================
st.markdown("##### 📝 บันทึกรายการใหม่")
type_ = st.radio("เลือกประเภท", ["รายจ่าย 🔴", "รายรับ 🟢"], horizontal=True)

with st.form("entry_form", clear_on_submit=True):
    date = st.date_input("📅 วันที่")
    
    if "รายจ่าย" in type_:
        category_options = ["🍜 ค่าอาหาร/เครื่องดื่ม", "🛍️ ช้อปปิ้ง/ของใช้", "⚡ ค่าน้ำ/ค่าไฟ", "📱 ค่า Net/Streaming", "🧺 ค่าซักผ้า", "🐷 เงินเก็บส่วนกลาง", "🏫 ค่าเรียนลูก", "🎌 เงินเก็บค่าเที่ยวญี่ปุ่น", "🚗 เดินทาง/เติมน้ำมัน", "📝 อื่นๆ"]
    else:
        category_options = ["💼 เงินเดือน", "👫 ค่าส่วนกลางจากปุ๊", "🎁 โบนัส/เงินพิเศษ", "💸 คืนเงิน/Cashback", "📈 ดอกเบี้ย/ปันผล", "📝 อื่นๆ"]
        
    category = st.selectbox("🏷️ หมวดหมู่", category_options)
    amount = st.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, format="%.2f", step=100.0)
    
    if amount > 0:
        st.markdown(f"✨ ยอดเงิน: **{amount:,.2f}** บาท")
    
    channel_options = ["💵 เงินสด", "🦅 KTB", "🟢 K-BANK", "🟣 SCB", "💳 Credit Card", "📝 อื่นๆ"]
    channel = st.radio("🏦 ช่องทาง", channel_options, horizontal=True)
    note = st.text_input("📝 หมายเหตุ (ถ้ามี)")

    if st.form_submit_button("บันทึกข้อมูล"):
        if amount <= 0:
            st.warning("กรุณาระบุจำนวนเงินค่ะ")
        else:
            all_values = sheet.get_all_values()
            next_id = len(all_values)
            income_amt = amount if "รายรับ" in type_ else ""
            expense_amt = amount if "รายจ่าย" in type_ else ""
            sheet.append_row([next_id, date.strftime("%Y-%m-%d"), category, income_amt, expense_amt, channel, note])
            st.success("บันทึกสำเร็จแล้วค่ะ!")
            st.rerun()

st.markdown("---")

# ==========================================
# ส่วนที่ 2: Dashboard (กราฟวงกลม)
# ==========================================
st.markdown("##### 📊 สรุปยอดเงิน")

if not df.empty:
    df['รายรับ'] = pd.to_numeric(df['รายรับ'].replace('', 0, regex=True))
    df['รายจ่าย'] = pd.to_numeric(df['รายจ่าย'].replace('', 0, regex=True))
    df['วันที่'] = pd.to_datetime(df['วันที่'])
    df['เดือน'] = df['วันที่'].dt.strftime('%Y-%m')
    
    selected_month = st.selectbox("เลือกเดือน:", ["ทั้งหมด"] + sorted(df['เดือน'].unique().tolist(), reverse=True))
    f_df = df if selected_month == "ทั้งหมด" else df[df['เดือน'] == selected_month]

    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับ", f"{f_df['รายรับ'].sum():,.0f}")
    c2.metric("รายจ่าย", f"{f_df['รายจ่าย'].sum():,.0f}")
    c3.metric("คงเหลือ", f"{(f_df['รายรับ'].sum() - f_df['รายจ่าย'].sum()):,.0f}")

    exp_df = f_df[f_df['รายจ่าย'] > 0]
    if not exp_df.empty:
        cat_data = exp_df.groupby('รายการ', as_index=False)['รายจ่าย'].sum()
        fig = px.pie(cat_data, values='รายจ่าย', names='รายการ', hole=0.5, 
                     color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("เริ่มบันทึกรายการแรกกันเลยค่ะ!")
