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
# ✨ การตกแต่ง UI ตามคำสั่งพิเศษของเจ้านาย
# ==========================================
st.set_page_config(page_title="บันทึกรายรับ-รายจ่าย", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #e0f2fe 0%, #ffffff 100%);
        background-attachment: fixed;
    }
    
    /* 1 & 2. ปรับช่อง Input (จำนวนเงิน/หมายเหตุ) เป็นสีขาว */
    div[data-baseweb="input"] {
        background-color: white !important;
        border-radius: 12px !important;
        border: 1px solid #bae6fd !important;
    }
    input {
        color: #1e293b !important;
    }

    /* 3. ปุ่มบันทึกข้อมูลสีม่วงอ่อน */
    div.stButton > button {
        background-color: #E9D5FF !important; /* Light Purple */
        color: #581c87 !important; /* Dark Purple Text */
        border-radius: 15px !important;
        border: 2px solid #d8b4fe !important;
        width: 100% !important;
        height: 60px !important;
        font-weight: bold !important;
        font-size: 22px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
    }

    /* 4. Dashboard แยกสี 3 ช่อง (เขียวอ่อน / ส้มอ่อน / ฟ้าอ่อน) */
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stMetric"] { background-color: #dcfce7 !important; border: 1px solid #86efac !important; }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetric"] { background-color: #ffedd5 !important; border: 1px solid #fdba74 !important; }
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stMetric"] { background-color: #e0f2fe !important; border: 1px solid #7dd3fc !important; }
    
    div[data-testid="stMetric"] {
        padding: 15px !important;
        border-radius: 15px !important;
    }

    /* 5. คำว่าสัดส่วนค่าใช้จ่าย สีน้ำเงินออกฟ้า */
    .donut-title {
        color: #0284c7 !important;
        font-weight: bold !important;
        font-size: 22px !important;
        margin-top: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💸 บันทึกรายรับ-รายจ่าย")

df = load_data()

# ==========================================
# ส่วนที่ 1: บันทึกรายการใหม่
# ==========================================
st.markdown("### 📝 บันทึกรายการใหม่")
type_ = st.radio("เลือกประเภทรายการ", ["รายจ่าย 🔴", "รายรับ 🟢"], horizontal=True)

with st.form("entry_form", clear_on_submit=True):
    date = st.date_input("📅 วันที่")
    
    if "รายจ่าย" in type_:
        category_options = ["🍜 ค่าอาหาร/เครื่องดื่ม", "🛍️ ช้อปปิ้ง/ของใช้", "⚡ ค่าน้ำ/ค่าไฟ", "📱 ค่า Net/Streaming", "🧺 ค่าซักผ้า", "🐷 เงินเก็บส่วนกลาง", "🏫 ค่าเรียนลูก", "🎌 เงินเก็บค่าเที่ยวญี่ปุ่น", "🚗 เดินทาง/เติมน้ำมัน", "📝 อื่นๆ"]
    else:
        category_options = ["💼 เงินเดือน", "👫 ค่าส่วนกลางจากปุ๊", "🎁 โบนัส/เงินพิเศษ", "💸 คืนเงิน/Cashback", "📈 ดอกเบี้ย/ปันผล", "📝 อื่นๆ"]
        
    category = st.selectbox("🏷️ เลือกหมวดหมู่", category_options)
    
    # ช่องใส่เงิน (พื้นขาวตาม CSS ด้านบน)
    amount = st.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, format="%.2f", step=100.0, value=None, placeholder="แตะเพื่อระบุยอดเงิน...")
    
    channel_options = ["💵 เงินสด", "🦅 KTB", "🟢 K-BANK", "🟣 SCB", "💳 Credit Card", "📝 อื่นๆ"]
    channel = st.radio("🏦 ช่องทางรับ/จ่าย", channel_options, horizontal=True)
    
    # ช่องหมายเหตุ (พื้นขาวตาม CSS ด้านบน)
    note = st.text_input("📝 หมายเหตุ (ถ้ามี)")

    if st.form_submit_button("บันทึกข้อมูลลงตาราง"):
        if amount is None or amount <= 0:
            st.error("⚠️ เจ้านายอย่าลืมใส่จำนวนเงินนะคะ!")
        else:
            all_values = sheet.get_all_values()
            next_id = len(all_values)
            income_amt = amount if "รายรับ" in type_ else ""
            expense_amt = amount if "รายจ่าย" in type_ else ""
            sheet.append_row([next_id, date.strftime("%Y-%m-%d"), category, income_amt, expense_amt, channel, note])
            st.success(f"✅ บันทึกยอด {amount:,.2f} บาท สำเร็จแล้วค่ะ!")
            st.rerun()

st.markdown("---")

# ==========================================
# ส่วนที่ 2: Dashboard
# ==========================================
st.markdown("### 📊 Dashboard สรุปยอด")

if not df.empty:
    df['รายรับ'] = pd.to_numeric(df['รายรับ'].replace('', 0, regex=True))
    df['รายจ่าย'] = pd.to_numeric(df['รายจ่าย'].replace('', 0, regex=True))
    df['วันที่'] = pd.to_datetime(df['วันที่'])
    df['เดือน'] = df['วันที่'].dt.strftime('%Y-%m')
    
    selected_month = st.selectbox("📅 เลือกดูประวัติรายเดือน:", ["ทั้งหมด"] + sorted(df['เดือน'].unique().tolist(), reverse=True))
    f_df = df if selected_month == "ทั้งหมด" else df[df['เดือน'] == selected_month]

    # การ์ดสรุปยอดแยกสี 3 ช่อง
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับ", f"{f_df['รายรับ'].sum():,.0f}")
    c2.metric("รายจ่าย", f"{f_df['รายจ่าย'].sum():,.0f}")
    c3.metric("คงเหลือ", f"{(f_df['รายรับ'].sum() - f_df['รายจ่าย'].sum()):,.0f}")

    # 6. กราฟโดนัทพื้นหลังขาว
    exp_df = f_df[f_df['รายจ่าย'] > 0]
    if not exp_df.empty:
        st.markdown('<p class="donut-title">🍩 สัดส่วนค่าใช้จ่าย</p>', unsafe_allow_html=True)
        cat_data = exp_df.groupby('รายการ', as_index=False)['รายจ่าย'].sum()
        fig = px.pie(cat_data, values='รายจ่าย', names='รายการ', hole=0.5, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        
        fig.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='horizontal')
        
        # ปรับพื้นหลังกราฟเป็นสีขาวตามสั่ง
        fig.update_layout(
            showlegend=False, 
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("เดือนนี้ยังไม่มีรายจ่ายค่ะ")
else:
    st.info("เจ้านายลองบันทึกรายการแรกดูนะคะ!")
