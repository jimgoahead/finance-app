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
# ✨ การตกแต่ง UI ใหม่หมดจด (เน้นความชัดเจนและสดใส)
# ==========================================
st.set_page_config(page_title="บันทึกรายรับ-รายจ่าย", layout="centered")

st.markdown("""
    <style>
    /* พื้นหลัง Gradient สีฟ้าสว่างสดใส */
    .stApp {
        background: linear-gradient(135deg, #f0f9ff 0%, #bae6fd 100%);
        background-attachment: fixed;
    }
    
    /* ปรับแต่งฟอนต์พื้นฐาน */
    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
        color: #0c4a6e;
    }

    /* แก้ปัญหา Dropdown (Selectbox) สีกลืนกัน */
    div[data-baseweb="select"] > div {
        background-color: white !important;
        color: #0c4a6e !important;
        border-radius: 10px !important;
        border: 1px solid #7dd3fc !important;
    }
    
    /* แก้สีตัวหนังสือในลิสต์ Dropdown */
    div[data-baseweb="popover"] li {
        color: #0c4a6e !important;
        background-color: white !important;
    }

    /* ปรับแต่งกล่อง Input และตัวเลข */
    div[data-baseweb="input"] input {
        background-color: white !important;
        color: #0c4a6e !important;
        border-radius: 10px !important;
    }

    /* ปุ่มบันทึกข้อมูลสีฟ้าสดใส (จิ้มง่ายขึ้น) */
    div.stButton > button {
        background-color: #0284c7 !important;
        color: white !important;
        border-radius: 15px !important;
        border: none !important;
        width: 100% !important;
        height: 55px !important;
        font-weight: bold !important;
        font-size: 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        transition: 0.3s !important;
    }
    div.stButton > button:active {
        transform: scale(0.98) !important;
    }

    /* กล่องสรุปยอดเงิน (Metrics) */
    div[data-testid="stMetric"] {
        background-color: white !important;
        padding: 15px !important;
        border-radius: 15px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        border: 1px solid #e0f2fe !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 บันทึกรายรับ-รายจ่าย")

df = load_data()

# ==========================================
# ส่วนที่ 1: บันทึกรายการใหม่
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
    
    # 💡 ปรับให้เป็น None เพื่อให้ช่องว่างเปล่าตอนเริ่มพิมพ์
    amount = st.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, format="%.2f", step=100.0, value=None, placeholder="แตะเพื่อใส่จำนวนเงิน...")
    
    channel_options = ["💵 เงินสด", "🦅 KTB", "🟢 K-BANK", "🟣 SCB", "💳 Credit Card", "📝 อื่นๆ"]
    channel = st.radio("🏦 ช่องทาง", channel_options, horizontal=True)
    note = st.text_input("📝 หมายเหตุ (ถ้ามี)")

    if st.form_submit_button("บันทึกข้อมูล"):
        if amount is None or amount <= 0:
            st.warning("เจ้านายลืมใส่จำนวนเงินหรือเปล่าคะ?")
        else:
            all_values = sheet.get_all_values()
            next_id = len(all_values)
            income_amt = amount if "รายรับ" in type_ else ""
            expense_amt = amount if "รายจ่าย" in type_ else ""
            sheet.append_row([next_id, date.strftime("%Y-%m-%d"), category, income_amt, expense_amt, channel, note])
            st.success(f"บันทึกยอด {amount:,.2f} บาท สำเร็จแล้วค่ะ!")
            st.rerun()

st.markdown("---")

# ==========================================
# ส่วนที่ 2: Dashboard (สรุปยอดและกราฟ)
# ==========================================
st.markdown("### 📊 Dashboard สรุปยอด")

if not df.empty:
    df['รายรับ'] = pd.to_numeric(df['รายรับ'].replace('', 0, regex=True))
    df['รายจ่าย'] = pd.to_numeric(df['รายจ่าย'].replace('', 0, regex=True))
    df['วันที่'] = pd.to_datetime(df['วันที่'])
    df['เดือน'] = df['วันที่'].dt.strftime('%Y-%m')
    
    selected_month = st.selectbox("เลือกดูรายเดือน:", ["ทั้งหมด"] + sorted(df['เดือน'].unique().tolist(), reverse=True))
    f_df = df if selected_month == "ทั้งหมด" else df[df['เดือน'] == selected_month]

    # การ์ดสรุปยอดแบบ 3 ช่อง
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับ", f"{f_df['รายรับ'].sum():,.0f}")
    c2.metric("รายจ่าย", f"{f_df['รายจ่าย'].sum():,.0f}")
    c3.metric("คงเหลือ", f"{(f_df['รายรับ'].sum() - f_df['รายจ่าย'].sum()):,.0f}")

    # กราฟโดนัท (Pie Chart)
    exp_df = f_df[f_df['รายจ่าย'] > 0]
    if not exp_df.empty:
        st.markdown("#### 🍩 สัดส่วนค่าใช้จ่าย")
        cat_data = exp_df.groupby('รายการ', as_index=False)['รายจ่าย'].sum()
        fig = px.pie(cat_data, values='รายจ่าย', names='รายการ', hole=0.5, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        
        # ปรับการวางข้อความให้อ่านง่าย แนวนอน ไม่เอียง
        fig.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='horizontal')
        fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("เดือนนี้ยังไม่มีรายจ่ายค่ะ")
else:
    st.info("เจ้านายลองบันทึกรายการแรกดูนะคะ!")
