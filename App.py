import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import json

# ==========================================
# 1. ส่วนตั้งค่าการเชื่อมต่อ (Secrets & Google Sheets)
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

def load_data():
    data = sheet.get_all_records()
    if data:
        return pd.DataFrame(data)
    else:
        return pd.DataFrame(columns=['ลำดับ', 'วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง', 'หมายเหตุ'])

# ==========================================
# 2. ปรับแต่งดีไซน์ (CSS & Font)
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
    /* ปรับแต่งปุ่มบันทึกให้ดูพรีเมียม */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00b894, #00cec9);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2.5rem;
        font-weight: bold;
        width: 100%;
        box-shadow: 0 4px 15px rgba(0, 206, 201, 0.3);
    }
    /* ปรับแต่งกล่อง Radio */
    .stRadio > div {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.title("💎 บันทึกรายรับ-รายจ่าย")

df = load_data()

# ==========================================
# 3. ส่วนที่ 1: ฟอร์มบันทึกข้อมูล (UX ใหม่)
# ==========================================
st.markdown("### 📝 บันทึกรายการใหม่")
type_ = st.radio("เลือกประเภท", ["รายจ่าย 🔴", "รายรับ 🟢"], horizontal=True)

with st.form("entry_form", clear_on_submit=True):
    date = st.date_input("📅 วันที่")
    
    if "รายจ่าย" in type_:
        category_options = ["🍜 ค่าอาหาร/เครื่องดื่ม", "🛍️ ช้อปปิ้ง/ของใช้", "⚡ ค่าน้ำ/ค่าไฟ", "📱 ค่า Net/Streaming", "🧺 ค่าซักผ้า", "🐷 เงินเก็บส่วนกลาง", "🏫 ค่าเรียนลูก", "🎌 เงินเก็บค่าเที่ยวญี่ปุ่น", "🚗 เดินทาง/เติมน้ำมัน", "📝 อื่นๆ"]
    else:
        category_options = ["💼 เงินเดือน", "👫 ค่าส่วนกลางจากปุ๊", "🎁 โบนัส/เงินพิเศษ", "💸 คืนเงิน/Cashback", "📈 ดอกเบี้ย/ปันผล", "📝 อื่นๆ"]
        
    category = st.selectbox("🏷️ หมวดหมู่", category_options)
    
    # แก้ไขปัญหา 0.00 ค้าง: ใช้ value=None และใส่ placeholder แทน
    amount = st.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, step=100.0, value=None, placeholder="แตะเพื่อพิมพ์จำนวนเงิน...")
    
    if amount:
        st.markdown(f"<p style='color:#00cec9; font-size:1.2rem; text-align:center;'>✨ ยอดเงิน: <b>{amount:,.2f}</b> บาท</p>", unsafe_allow_html=True)
    
    # เรียงลำดับช่องทางใหม่ตามคำขอ
    channel_options = ["💳 Credit Card", "🦅 KTB", "🟢 K-BANK", "🟣 SCB", "💵 เงินสด", "📝 อื่นๆ"]
    channel = st.radio("🏦 ช่องทาง", channel_options, horizontal=True)
    
    note = st.text_input("📝 หมายเหตุ (ถ้ามี)")

    if st.form_submit_button("บันทึกข้อมูลลงตาราง"):
        if amount is None or amount <= 0:
            st.error("⚠️ เจ้านายระบุจำนวนเงินด้วยนะคะ")
        else:
            all_values = sheet.get_all_values()
            next_id = len(all_values)
            income_amt = amount if "รายรับ" in type_ else ""
            expense_amt = amount if "รายจ่าย" in type_ else ""
            date_str = date.strftime("%Y-%m-%d")
            sheet.append_row([next_id, date_str, category, income_amt, expense_amt, channel, note])
            st.success("บันทึกเรียบร้อยแล้วค่ะเจ้านาย!")
            st.rerun()

st.markdown("---")

# ==========================================
# 4. ส่วนที่ 2: Dashboard (กราฟโดนัท)
# ==========================================
st.markdown("### 📊 Dashboard สรุปยอด")

if not df.empty:
    # เตรียมข้อมูล
    df['รายรับ'] = pd.to_numeric(df['รายรับ'].replace('', 0, regex=True))
    df['รายจ่าย'] = pd.to_numeric(df['รายจ่าย'].replace('', 0, regex=True))
    df['วันที่'] = pd.to_datetime(df['วันที่'])
    df['เดือน-ปี'] = df['วันที่'].dt.strftime('%Y-%m')
    
    # ระบบกรองเดือน
    months_list = ["ดูทั้งหมด"] + sorted(df['เดือน-ปี'].unique().tolist(), reverse=True)
    selected_month = st.selectbox("📅 เลือกเดือนที่ต้องการดู:", months_list)
    
    f_df = df if selected_month == "ดูทั้งหมด" else df[df['เดือน-ปี'] == selected_month]

    # การ์ดสรุปตัวเลข
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับ", f"{f_df['รายรับ'].sum():,.0f}")
    c2.metric("รายจ่าย", f"{f_df['รายจ่าย'].sum():,.0f}")
    c3.metric("คงเหลือ", f"{(f_df['รายรับ'].sum() - f_df['รายจ่าย'].sum()):,.0f}")

    # กราฟโดนัทวิเคราะห์รายจ่าย
    exp_df = f_df[f_df['รายจ่าย'] > 0]
    if not exp_df.empty:
        st.markdown("#### 🍩 สัดส่วนค่าใช้จ่าย")
        cat_data = exp_df.groupby('รายการ', as_index=False)['รายจ่าย'].sum()
        fig = px.pie(cat_data, values='รายจ่าย', names='รายการ', hole=0.5,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📝 ดูประวัติรายการทั้งหมด"):
        st.dataframe(f_df[['วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง']].sort_values('วันที่', ascending=False), use_container_width=True)
else:
    st.info("ยังไม่มีข้อมูลในระบบเลยค่ะ เจ้านายลองบันทึกรายการแรกดูนะคะ!")
