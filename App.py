import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import json

# ==========================================
# ส่วนตั้งค่าการเชื่อมต่อ (Secrets & Sheets)
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
# ✨ ปรับแต่ง UI: สีฟ้าสดใส ฟอนต์เข้ม แดชบอร์ดชัดเจน
# ==========================================
st.set_page_config(page_title="บันทึกรายรับ-รายจ่าย", layout="centered")

st.markdown("""
    <style>
    /* 1. พื้นหลังสีฟ้าสดใส */
    .stApp {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        background-attachment: fixed;
    }
    
    /* 1. แก้ไขฟอนต์ขาว: บังคับให้เป็นสีน้ำเงินเข้มอ่านง่าย */
    html, body, [class*="css"], .stMarkdown, p, div {
        color: #0f172a !important; 
        font-size: 16px;
    }
    
    /* ปรับแต่งกล่อง Form */
    .stForm {
        background-color: rgba(255, 255, 255, 0.8) !important;
        border-radius: 15px !important;
        border: 2px solid #7dd3fc !important;
    }

    /* ปุ่มบันทึกข้อมูลสีฟ้าสด */
    div.stButton > button:first-child {
        background-color: #0284c7;
        color: white !important;
        border-radius: 10px;
        font-weight: bold;
        height: 50px;
    }
    
    /* หัวข้อ Title */
    h1 {
        color: #0369a1 !important;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 บันทึกรายรับ-รายจ่าย")

df = load_data()

# ==========================================
# ส่วนที่ 1: บันทึกรายการใหม่
# ==========================================
st.markdown("### 📝 บันทึกรายการใหม่")
# ย้ายประเภทออกมานอก Form เพื่อให้หมวดหมู่เปลี่ยนทันที
type_ = st.radio("เลือกประเภท", ["รายจ่าย 🔴", "รายรับ 🟢"], horizontal=True)

with st.form("entry_form", clear_on_submit=True):
    date = st.date_input("📅 วันที่")
    
    if "รายจ่าย" in type_:
        category_options = ["🍜 ค่าอาหาร/เครื่องดื่ม", "🛍️ ช้อปปิ้ง/ของใช้", "⚡ ค่าน้ำ/ค่าไฟ", "📱 ค่า Net/Streaming", "🧺 ค่าซักผ้า", "🐷 เงินเก็บส่วนกลาง", "🏫 ค่าเรียนลูก", "🎌 เงินเก็บค่าเที่ยวญี่ปุ่น", "🚗 เดินทาง/เติมน้ำมัน", "📝 อื่นๆ"]
    else:
        category_options = ["💼 เงินเดือน", "👫 ค่าส่วนกลางจากปุ๊", "🎁 โบนัส/เงินพิเศษ", "💸 คืนเงิน/Cashback", "📈 ดอกเบี้ย/ปันผล", "📝 อื่นๆ"]
        
    category = st.selectbox("🏷️ หมวดหมู่", category_options)
    
    # 2. ช่องตัวเลข (คงไว้เพื่อให้แป้นมือถือเด้งตัวเลข)
    amount = st.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, format="%.2f", step=100.0)
    
    # พรีวิวตัวเลขตัวใหญ่ๆ พร้อมลูกน้ำเพื่อความเช็กง่าย
    if amount > 0:
        st.markdown(f"<h2 style='color:#059669; text-align:center;'>฿ {amount:,.2f}</h2>", unsafe_allow_html=True)
    
    # 3. เรียงลำดับช่องทางตามความต้องการของเจ้านาย
    channel_options = ["💵 เงินสด", "🦅 KTB", "🟢 K-BANK", "🟣 SCB", "💳 Credit Card", "📝 อื่นๆ"]
    channel = st.radio("🏦 ช่องทาง", channel_options, horizontal=True)
    
    note = st.text_input("📝 หมายเหตุ (ถ้ามี)")

    if st.form_submit_button("บันทึกข้อมูลเลย!"):
        if amount <= 0:
            st.warning("กรุณาระบุจำนวนเงินด้วยนะคะเจ้านาย")
        else:
            all_values = sheet.get_all_values()
            next_id = len(all_values)
            income_amt = amount if "รายรับ" in type_ else ""
            expense_amt = amount if "รายจ่าย" in type_ else ""
            sheet.append_row([next_id, date.strftime("%Y-%m-%d"), category, income_amt, expense_amt, channel, note])
            st.success("บันทึกเรียบร้อยแล้วค่ะ!")
            st.rerun()

st.markdown("---")

# ==========================================
# 4. ส่วนที่ 2: Dashboard (นำกล่องสีกลับมา)
# ==========================================
st.markdown("### 📊 Dashboard สรุปยอดเงิน")

if not df.empty:
    df['รายรับ'] = pd.to_numeric(df['รายรับ'].replace('', 0, regex=True))
    df['รายจ่าย'] = pd.to_numeric(df['รายจ่าย'].replace('', 0, regex=True))
    df['วันที่'] = pd.to_datetime(df['วันที่'])
    df['เดือน'] = df['วันที่'].dt.strftime('%Y-%m')
    
    selected_month = st.selectbox("📅 เลือกเดือน:", ["ทั้งหมด"] + sorted(df['เดือน'].unique().tolist(), reverse=True))
    f_df = df if selected_month == "ทั้งหมด" else df[df['เดือน'] == selected_month]

    # แสดงผลเป็นกล่องสีสดใส 3 ช่อง
    t_income = f_df['รายรับ'].sum()
    t_expense = f_df['รายจ่าย'].sum()
    t_balance = t_income - t_expense

    st.success(f"**รายรับรวม:** ฿ {t_income:,.2f}")
    st.error(f"**รายจ่ายรวม:** ฿ {t_expense:,.2f}")
    st.info(f"**คงเหลือสุทธิ:** ฿ {t_balance:,.2f}")

    # 1. กราฟโดนัท (แก้ตัวหนังสือเอียง)
    exp_df = f_df[f_df['รายจ่าย'] > 0]
    if not exp_df.empty:
        st.markdown("#### 🍩 สัดส่วนรายจ่าย")
        cat_data = exp_df.groupby('รายการ', as_index=False)['รายจ่าย'].sum()
        fig = px.pie(cat_data, values='รายจ่าย', names='รายการ', hole=0.5,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        
        # ตั้งค่าให้ตัวหนังสือในกราฟเป็นแนวนอนอ่านง่าย
        fig.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='horizontal')
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
    with st.expander("ดูประวัติรายการทั้งหมด"):
        st.dataframe(f_df[['วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง']].sort_values(by='วันที่', ascending=False), use_container_width=True)
else:
    st.info("ยังไม่มีข้อมูลในระบบเลยค่ะ เจ้านาย")
