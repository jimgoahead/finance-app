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
SHEET_NAME = "Finance App" 
sheet = client.open(SHEET_NAME).sheet1

def load_data():
    data = sheet.get_all_records()
    if data:
        return pd.DataFrame(data)
    else:
        return pd.DataFrame(columns=['ลำดับ', 'วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง', 'หมายเหตุ'])

# ==========================================
# การตั้งค่าหน้าเว็บและสีสัน (CSS Magic)
# ==========================================
st.set_page_config(page_title="ระบบจัดการรายรับ-รายจ่าย", layout="centered")

st.markdown("""
    <style>
    /* ซ่อนหัวข้อช่องกรอกเสียง */
    div[data-testid="stTextInput"] label {
        display: none;
    }
    
    /* 1. แต่งช่อง Text Box เสียงให้เป็นสีฟ้าโดดเด่น และฟอนต์ดำ */
    div[data-testid="stTextInput"]:has(input[placeholder*="แตะที่นี่แล้วพูด"]) div[data-baseweb="base-input"] {
        background-color: #e0f7fa !important;
        border: 2px solid #00acc1 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stTextInput"]:has(input[placeholder*="แตะที่นี่แล้วพูด"]) input {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important; 
        font-weight: bold !important;
    }

    /* 2. ล็อกสีปุ่มแยกคำ (สีเขียว) และปุ่มล้างคำ (สีแดง) ด้วยตำแหน่ง Column */
    /* ปุ่มในคอลัมน์แรก (แยกคำ) */
    div[data-testid="column"]:nth-of-type(1) button[kind="secondary"] {
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
        height: 50px !important;
        width: 100% !important;
        font-weight: bold !important;
    }
    /* ปุ่มในคอลัมน์สอง (ล้างคำ) */
    div[data-testid="column"]:nth-of-type(2) button[kind="secondary"] {
        background-color: #f44336 !important;
        color: white !important;
        border: none !important;
        height: 50px !important;
        width: 100% !important;
        font-weight: bold !important;
    }

    /* 3. ปรับแต่งปุ่มบันทึกด้านล่างสุดให้เป็นสีน้ำเงิน */
    div[data-testid="stFormSubmitButton"] button {
        background-color: #1976D2 !important; 
        color: white !important;
        border-radius: 8px !important;
        height: 50px !important;
        font-weight: bold !important;
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💸 แอปรายรับ-รายจ่าย ประจำวัน")

df = load_data()

# ==========================================
# ส่วนที่ 1: ระบบสั่งงานด้วยเสียง (Voice Magic Input)
# ==========================================
if 'pre_type' not in st.session_state: st.session_state.pre_type = "รายจ่าย 🔴"
if 'pre_amount' not in st.session_state: st.session_state.pre_amount = None
if 'pre_cat' not in st.session_state: st.session_state.pre_cat = "🍜 ค่าอาหาร/เครื่องดื่ม"
if 'pre_chan' not in st.session_state: st.session_state.pre_chan = " 💵 เงินสด "
if 'pre_note' not in st.session_state: st.session_state.pre_note = ""

def clear_voice_text():
    if "voice_input_key" in st.session_state:
        st.session_state.voice_input_key = ""

st.markdown("### 🎙️ สั่งงานด้วยเสียง (Magic Input)")
st.info("💡 **วิธีใช้:** แตะช่องสีฟ้า กดไมค์ที่คีย์บอร์ดเพื่อพูด แล้วกดปุ่ม ✨ แยกคำ")

voice_input = st.text_input("ข้อความเสียง:", key="voice_input_key", placeholder="แตะที่นี่แล้วพูด... เช่น: รายจ่ายค่าอาหาร 150 บาท จ่ายด้วย Kbank")

col1, col2 = st.columns(2)
with col1:
    process_btn = st.button("✨ แยกคำ", use_container_width=True)
with col2:
    clear_btn = st.button("❌ ล้างคำ", use_container_width=True, on_click=clear_voice_text)

if process_btn and st.session_state.voice_input_key:
    text = st.session_state.voice_input_key.lower()
    
    if "รายรับ" in text:
        st.session_state.pre_type = "รายรับ 🟢"
    else:
        st.session_state.pre_type = "รายจ่าย 🔴"
        
    if "หมายเหตุ" in text:
        parts = text.split("หมายเหตุ", 1)
        st.session_state.pre_note = parts[1].strip()
        text_to_search = parts[0] 
    else:
        st.session_state.pre_note = "" 
        text_to_search = text
        
    amounts = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', text_to_search)
    if amounts:
        st.session_state.pre_amount = float(amounts[0].replace(',', ''))
        
    if any(word in text_to_search for word in ["อาหาร", "กิน", "ข้าว", "กาแฟ"]):
        st.session_state.pre_cat = "🍜 ค่าอาหาร/เครื่องดื่ม"
    elif any(word in text_to_search for word in ["เดินทาง", "รถ", "น้ำมัน", "bts"]):
        st.session_state.pre_cat = "🚗 เดินทาง/เติมน้ำมัน"
    elif any(word in text_to_search for word in ["ช้อปปิ้ง", "ของใช้", "ซื้อ", "เซเว่น"]):
        st.session_state.pre_cat = "🛍️ ช้อปปิ้ง/ของใช้"
    elif any(word in text_to_search for word in ["น้ำ", "ไฟ"]):
        st.session_state.pre_cat = "⚡ ค่าน้ำ/ค่าไฟ"
    elif any(word in text_to_search for word in ["เน็ต", "net", "สตรีมมิ่ง"]):
        st.session_state.pre_cat = "📱 ค่า Net/Streaming"
    elif "ซักผ้า" in text_to_search:
        st.session_state.pre_cat = "🧺 ค่าซักผ้า"
    elif any(word in text_to_search for word in ["ลูก", "เรียน"]):
        st.session_state.pre_cat = "🏫 ค่าเรียนลูก"
    elif "เงินเดือน" in text_to_search:
        st.session_state.pre_cat = "💼 เงินเดือน"
    else:
        st.session_state.pre_cat = "📝 อื่นๆ"

    if any(word in text_to_search for word in ["kbank", "กสิกร", "เคแบงก์"]):
        st.session_state.pre_chan = "🟢 K-BANK"
    elif any(word in text_to_search for word in ["scb", "ไทยพาณิชย์"]):
        st.session_state.pre_chan = "🟣 SCB"
    elif any(word in text_to_search for word in ["ktb", "กรุงไทย"]):
        st.session_state.pre_chan = "🦅 KTB"
    elif any(word in text_to_search for word in ["บัตร", "เครดิต", "credit"]):
        st.session_state.pre_chan = "💳 Credit Card"
    else:
        st.session_state.pre_chan = " 💵 เงินสด "
        
    st.rerun() 

st.markdown("---")

# ==========================================
# ส่วนที่ 2: ฟอร์มตรวจสอบและบันทึก
# ==========================================
st.markdown("### 📝 ตรวจสอบและบันทึกรายการ")

tourist_mode = st.toggle("✈️ โหมดนักท่องเที่ยว (แยกกระเป๋าทริป)")

type_index = 0 if st.session_state.pre_type == "รายจ่าย 🔴" else 1
type_ = st.radio("🔄 ประเภทรายการ", ["รายจ่าย 🔴", "รายรับ 🟢"], index=type_index, horizontal=True)

with st.form("entry_form", clear_on_submit=False):
    date = st.date_input("📅 วันที่")
    
    if tourist_mode:
        trip_name = st.text_input("🏷️ ชื่อทริป", value="Japan 2026")
    
    if "รายจ่าย" in type_:
        category_options = ["🍜 ค่าอาหาร/เครื่องดื่ม", "🛍️ ช้อปปิ้ง/ของใช้", "⚡ ค่าน้ำ/ค่าไฟ", "📱 ค่า Net/Streaming", "🧺 ค่าซักผ้า", "🐷 เงินเก็บส่วนกลาง", "🏫 ค่าเรียนลูก", "🎌 เงินเก็บค่าเที่ยวญี่ปุ่น", "🚗 เดินทาง/เติมน้ำมัน", "📝 อื่นๆ"]
    else:
        category_options = ["💼 เงินเดือน", "👫 ค่าส่วนกลางจากปุ๊", "🎁 โบนัส/เงินพิเศษ", "💸 คืนเงิน/Cashback", "📈 ดอกเบี้ย/ปันผล", "📝 อื่นๆ"]
        
    try: cat_idx = category_options.index(st.session_state.pre_cat)
    except: cat_idx = 0
        
    category = st.selectbox("🏷️ หมวดหมู่", category_options, index=cat_idx)
    
    if tourist_mode:
        st.markdown("🎌 **สกุลเงินต่างประเทศ**")
        col_curr, col_rate = st.columns(2)
        with col_curr: curr = st.selectbox("สกุลเงิน", ["JPY (เยน)", "USD (ดอลลาร์)"])
        with col_rate: rate = st.number_input("เรทแลกเปลี่ยน", value=None, format="%.4f", step=0.0100)
        amount_input = st.number_input(f"💰 จำนวนเงิน ({curr.split(' ')[0]})", min_value=0.0, format="%.2f", value=st.session_state.pre_amount)
    else:
        amount_input = st.number_input("💰 จำนวนเงิน (บาท)", min_value=0.0, format="%.2f", value=st.session_state.pre_amount)
    
    channel_options = ["💳 Credit Card", "🦅 KTB", "🟢 K-BANK", "🟣 SCB", " 💵 เงินสด ", "📝อื่นๆ"]
    try: chan_idx = channel_options.index(st.session_state.pre_chan)
    except: chan_idx = 4 
    channel = st.radio("🏦 ช่องทาง", channel_options, index=chan_idx, horizontal=True)
    
    note = st.text_input("📝 หมายเหตุ", value=st.session_state.pre_note)

    if st.form_submit_button("บันทึกข้อมูลลงตาราง"):
        if amount_input and amount_input > 0:
            if tourist_mode:
                final_amt = amount_input * rate
                final_note = f"#{trip_name} [{curr.split(' ')[0]} {amount_input:,.2f} @{rate}] {note}".strip()
            else:
                final_amt = amount_input
                final_note = note

            all_vals = sheet.get_all_values()
            sheet.append_row([len(all_vals), date.strftime("%Y-%m-%d"), category, final_amt if "รายรับ" in type_ else "", final_amt if "รายจ่าย" in type_ else "", channel, final_note])
            st.success(f"✅ บันทึกยอด {final_amt:,.2f} บาท สำเร็จ!")
            
            st.session_state.pre_amount = None
            st.session_state.pre_note = ""
            if "voice_input_key" in st.session_state: del st.session_state["voice_input_key"]
            st.rerun()
        else:
            st.error("⚠️ กรุณาใส่จำนวนเงิน!")

st.markdown("---")

# ==========================================
# ส่วนที่ 3: Dashboard
# ==========================================
st.markdown("### 📊 Dashboard")
if not df.empty:
    df['รายรับ'] = pd.to_numeric(df['รายรับ'].replace('', 0, regex=True))
    df['รายจ่าย'] = pd.to_numeric(df['รายจ่าย'].replace('', 0, regex=True))
    df['วันที่'] = pd.to_datetime(df['วันที่'])
    df['เดือน-ปี'] = df['วันที่'].dt.strftime('%Y-%m')
    
    if tourist_mode:
        df['หมายเหตุ'] = df['หมายเหตุ'].fillna('')
        trip_search = st.text_input("ชื่อทริป:", value="Japan 2026")
        f_df = df[df['หมายเหตุ'].str.contains(f"#{trip_search}", na=False)]
        if not f_df.empty:
            st.error(f"**จ่ายรวมทริป:** ฿ {f_df['รายจ่าย'].sum():,.2f}")
            fig_p = px.pie(f_df[f_df['รายจ่าย']>0].groupby('รายการ', as_index=False)['รายจ่าย'].sum(), values='รายจ่าย', names='รายการ', hole=0.4)
            st.plotly_chart(fig_p, use_container_width=True)
    else:
        sel_m = st.selectbox("เลือกเดือน:", ["ดูทั้งหมด"] + sorted(df['เดือน-ปี'].unique().tolist(), reverse=True))
        f_df = df if sel_m == "ดูทั้งหมด" else df[df['เดือน-year'] == sel_m] # Fix column name
        f_df = df if sel_m == "ดูทั้งหมด" else df[df['เดือน-ปี'] == sel_m]
        
        c1, c2 = st.columns(2)
        c1.success(f"รับ: ฿ {f_df['รายรับ'].sum():,.2f}")
        c2.error(f"จ่าย: ฿ {f_df['รายจ่าย'].sum():,.2f}")
        
        cc = f_df[f_df['ช่องทาง'] == '💳 Credit Card']['รายจ่าย'].sum()
        st.info(f"💳 ยอดบัตรเครดิตเดือนนี้: ฿ {cc:,.2f}")
        
        with st.expander("ดูประวัติ"):
            st.dataframe(f_df[['วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง', 'หมายเหตุ']].sort_values(by='วันที่', ascending=False), use_container_width=True)
else:
    st.info("ยังไม่มีข้อมูลค่ะ")
