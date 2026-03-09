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
    cols = ['ลำดับ', 'วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง', 'หมายเหตุ', 'ประเภทการจ่าย', 'จำนวนงวด', 'งวดปัจจุบัน', 'ID รายการผ่อน']
    if data:
        df = pd.DataFrame(data)
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=cols)

# ==========================================
# การตั้งค่าหน้าเว็บและสีสัน
# ==========================================
st.set_page_config(page_title="ระบบจัดการรายรับ-รายจ่าย", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stTextInput"] label { display: none; }
    div[data-testid="stTextInput"]:has(input[placeholder*="แตะที่นี่แล้วพูด"]) div[data-baseweb="base-input"] {
        background-color: #e0f7fa !important;
        border: 2px solid #00acc1 !important;
        border-radius: 8px !important;
        padding: 5px !important;
    }
    div[data-testid="stTextInput"]:has(input[placeholder*="แตะที่นี่แล้วพูด"]) input {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important; 
        font-weight: bold !important;
        font-size: 16px !important;
    }
    div[data-testid="stTextInput"]:has(input[placeholder*="แตะที่นี่แล้วพูด"]) input::placeholder {
        color: #555555 !important;
        -webkit-text-fill-color: #555555 !important;
    }
    div[data-testid="stColumn"]:nth-child(1) div[data-testid="stButton"] button {
        background-color: #4CAF50 !important;
        color: white !important;
        border-color: #4CAF50 !important;
        font-weight: bold !important;
    }
    div[data-testid="stColumn"]:nth-child(2) div[data-testid="stButton"] button {
        background-color: #f44336 !important;
        color: white !important;
        border-color: #f44336 !important;
        font-weight: bold !important;
    }
    /* 💡 ล็อกเป้าปุ่มบันทึกข้อมูล (อ้างอิงจากคีย์ btn_save) */
    div[data-testid="stButton"]:has(button[key="btn_save"]) button {
        background-color: #1976D2 !important; 
        color: white !important;
        border-radius: 8px !important;
        height: 50px !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border: none !important;
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
st.info("💡 **วิธีใช้:** แตะช่องสีฟ้าด้านล่าง กดไมค์ที่คีย์บอร์ดมือถือเพื่อพูด แล้วกดปุ่ม ✨ แยกคำ")

voice_input = st.text_input("ข้อความเสียง:", key="voice_input_key", placeholder="แตะที่นี่แล้วพูด... เช่น: รายจ่ายค่าอาหาร 150 บาท จ่ายด้วย Kbank")

col1, col2 = st.columns(2)
with col1:
    process_btn = st.button("✨ แยกคำ", use_container_width=True)
with col2:
    clear_btn = st.button("❌ ล้างคำ", use_container_width=True, on_click=clear_voice_text)

if process_btn and st.session_state.voice_input_key:
    text = st.session_state.voice_input_key.lower()
    
    if "รายรับ" in text: st.session_state.pre_type = "รายรับ 🟢"
    else: st.session_state.pre_type = "รายจ่าย 🔴"
        
    if "หมายเหตุ" in text:
        parts = text.split("หมายเหตุ", 1)
        st.session_state.pre_note = parts[1].strip()
        text_to_search = parts[0] 
    else:
        st.session_state.pre_note = "" 
        text_to_search = text
        
    amounts = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', text_to_search)
    if amounts: st.session_state.pre_amount = float(amounts[0].replace(',', ''))
        
    # แกะหมวดหมู่
    if any(word in text_to_search for word in ["ส่วนกลางจากปุ๊", "ส่วนกลางปุ๊"]): st.session_state.pre_cat = "👫 ค่าส่วนกลางจากปุ๊"  
    elif any(word in text_to_search for word in ["เงินคืน", "หารค่า"]): st.session_state.pre_cat = "💸 คืนเงิน/Cashback"  
    elif any(word in text_to_search for word in ["โบนัส", "เงินพิเศษ"]): st.session_state.pre_cat = "🎁 โบนัส/เงินพิเศษ"  
    elif any(word in text_to_search for word in ["ดอกเบี้ย", "หุ้น", "กำไร", "ปันผล"]): st.session_state.pre_cat = "📈 ดอกเบี้ย/ปันผล"      
    elif "เงินเดือน" in text_to_search: st.session_state.pre_cat = "💼 เงินเดือน"
    elif any(word in text_to_search for word in ["เดินทาง", "รถ", "น้ำมัน", "ชาร์จ", "เรือ", "bts"]): st.session_state.pre_cat = "🚗 เดินทาง/เติมน้ำมัน"
    elif any(word in text_to_search for word in ["อาหาร", "กิน", "ดื่ม", "ข้าว", "กาแฟ"]): st.session_state.pre_cat = "🍜 ค่าอาหาร/เครื่องดื่ม"
    elif any(word in text_to_search for word in ["ช้อป", "ของใช้", "ซื้อ", "เซเว่น"]): st.session_state.pre_cat = "🛍️ ช้อปปิ้ง/ของใช้"
    elif any(word in text_to_search for word in ["น้ำ", "ไฟ"]): st.session_state.pre_cat = "⚡ ค่าน้ำ/ค่าไฟ"
    elif any(word in text_to_search for word in ["เน็ต", "net", "ค่าโทร", "ais", "true", "สตรีมมิ่ง"]): st.session_state.pre_cat = "📱 ค่า Net/Streaming"
    elif "ซักผ้า" in text_to_search: st.session_state.pre_cat = "🧺 ค่าซักผ้า"
    elif any(word in text_to_search for word in ["เงินเก็บลูก", "ค่าเรียน"]): st.session_state.pre_cat = "🏫 ค่าเรียนลูก"
    elif "ค่าเที่ยว" in text_to_search: st.session_state.pre_cat = "🎌 เงินเก็บค่าเที่ยวญี่ปุ่น"
    elif any(word in text_to_search for word in ["เก็บส่วนกลาง", "ส่วนกลาง"]): st.session_state.pre_cat = "🐷 เงินเก็บส่วนกลาง"
    else: st.session_state.pre_cat = "📝 อื่นๆ"

    # แกะช่องทาง
    if any(word in text_to_search for word in ["kbank", "กสิกร", "เคแบงก์"]): st.session_state.pre_chan = "🟢 K-BANK"
    elif any(word in text_to_search for word in ["scb", "ไทยพาณิชย์"]): st.session_state.pre_chan = "🟣 SCB"
    elif any(word in text_to_search for word in ["ktb", "กรุงไทย"]): st.session_state.pre_chan = "🦅 KTB"
    elif any(word in text_to_search for word in ["บัตร", "เครดิต", "credit"]): st.session_state.pre_chan = "💳 Credit Card"
    else: st.session_state.pre_chan = " 💵 เงินสด "
        
    st.rerun()

st.markdown("---")

# ==========================================
# ส่วนที่ 2: ฟอร์มตรวจสอบและบันทึก
# ==========================================
st.markdown("### 📝 ตรวจสอบและบันทึกรายการ")

tourist_mode = st.toggle("✈️ โหมดนักท่องเที่ยว (แยกกระเป๋าทริป)")

type_index = 0 if st.session_state.pre_type == "รายจ่าย 🔴" else 1
type_ = st.radio("🔄 ประเภทรายการ", ["รายจ่าย 🔴", "รายรับ 🟢"], index=type_index, horizontal=True)

# 💡 ถอด st.form ออก เพื่อให้ UI สลับโชว์อัตโนมัติแบบ Real-time
date = st.date_input("📅 วันที่ (วันทำรายการ)")

if tourist_mode:
    trip_name = st.text_input("🏷️ ชื่อทริป (เช่น Japan 2026)", value="Japan 2026")

if "รายจ่าย" in type_:
    category_options = ["🍜 ค่าอาหาร/เครื่องดื่ม", "🛍️ ช้อปปิ้ง/ของใช้", "⚡ ค่าน้ำ/ค่าไฟ", "📱 ค่า Net/Streaming", "🧺 ค่าซักผ้า", "🐷 เงินเก็บส่วนกลาง", "🏫 ค่าเรียนลูก", "🎌 เงินเก็บค่าเที่ยวญี่ปุ่น", "🚗 เดินทาง/เติมน้ำมัน", "📝 อื่นๆ"]
else:
    category_options = ["💼 เงินเดือน", "👫 ค่าส่วนกลางจากปุ๊", "🎁 โบนัส/เงินพิเศษ", "💸 คืนเงิน/Cashback", "📈 ดอกเบี้ย/ปันผล", "📝 อื่นๆ"]
    
try: cat_idx = category_options.index(st.session_state.pre_cat)
except ValueError: cat_idx = 0
category = st.selectbox("🏷️ หมวดหมู่", category_options, index=cat_idx)

channel_options = ["💳 Credit Card", "🦅 KTB", "🟢 K-BANK", "🟣 SCB", " 💵 เงินสด ", "📝อื่นๆ"]
try: chan_idx = channel_options.index(st.session_state.pre_chan)
except ValueError: chan_idx = 4 
channel = st.radio("🏦 ช่องทาง", channel_options, index=chan_idx, horizontal=True)

# 💡 ลูกเล่น UX ล่าสุด: เด้งต่อท้ายทันทีเมื่อกดบัตรเครดิต
payment_type = "จ่ายเต็ม"
installments = 1
if "รายจ่าย" in type_ and channel == "💳 Credit Card":
    st.markdown("💳 **รูปแบบการชำระบัตรเครดิต**")
    col_pay1, col_pay2 = st.columns(2)
    with col_pay1:
        # Default เป็นจ่ายเต็ม
        payment_type = st.radio("เลือกรูปแบบ", ["จ่ายเต็ม", "ผ่อนชำระ"], horizontal=True, label_visibility="collapsed")
    
    with col_pay2:
        if payment_type == "ผ่อนชำระ":
            # 💡 ดรอปดาวน์จำกัดเฉพาะ 4, 6, 10 เดือนตามที่เจ้านายสั่ง
            installments = st.selectbox("จำนวนงวด (เดือน)", [4, 6, 10], label_visibility="collapsed")

if tourist_mode:
    st.markdown("🎌 **ข้อมูลสกุลเงินต่างประเทศ**")
    col_curr, col_rate = st.columns(2)
    with col_curr: curr = st.selectbox("สกุลเงิน", ["JPY (เยน)", "USD (ดอลลาร์)"])
    with col_rate: rate = st.number_input("เรทแลกเปลี่ยน", value=None, format="%.4f", step=0.0100)
    curr_symbol = curr.split(' ')[0]
    amount_input = st.number_input(f"💰 จำนวนเงิน ({curr_symbol})", min_value=0.0, format="%.2f", step=100.0, value=st.session_state.pre_amount)
else:
    amount_input = st.number_input("💰 จำนวนเงินทั้งหมด (บาท)", min_value=0.0, format="%.2f", step=100.0, value=st.session_state.pre_amount)

note = st.text_input("📝 หมายเหตุ (ถ้ามี)", value=st.session_state.pre_note)

# 💡 ปุ่มบันทึก (ระบุ Key เพื่อให้ CSS ล็อกเป้าหมายถูกตัว)
if st.button("บันทึกข้อมูลลงตาราง", key="btn_save", use_container_width=True):
    if amount_input is None or amount_input <= 0:
        st.error("⚠️ เจ้านายอย่าลืมใส่จำนวนเงินนะคะ!")
    else:
        if tourist_mode:
            final_thb_amount = amount_input * rate
            final_note = f"#{trip_name} [{curr.split(' ')[0]} {amount_input:,.2f} @{rate}] {note}".strip()
        else:
            final_thb_amount = amount_input
            final_note = note

        all_values = sheet.get_all_values()
        next_id = len(all_values)
        rows_to_append = []

        if payment_type == "ผ่อนชำระ" and channel == "💳 Credit Card" and "รายจ่าย" in type_:
            monthly_amt = final_thb_amount / installments
            inst_id = f"INST-{date.strftime('%Y%m%d')}-{next_id}" 
            
            for i in range(1, installments + 1):
                f_date = (pd.to_datetime(date) + pd.DateOffset(months=i-1)).strftime("%Y-%m-%d")
                rows_to_append.append([
                    next_id + (i-1), f_date, category, "", monthly_amt, channel, final_note, 
                    "ผ่อนชำระ", installments, i, inst_id
                ])
            st.success(f"✅ บันทึกยอดผ่อนเดือนละ {monthly_amt:,.2f} บาท จำนวน {installments} งวด สำเร็จแล้วค่ะ!")
        else:
            income_amt = final_thb_amount if "รายรับ" in type_ else ""
            expense_amt = final_thb_amount if "รายจ่าย" in type_ else ""
            rows_to_append.append([
                next_id, date.strftime("%Y-%m-%d"), category, income_amt, expense_amt, channel, final_note, 
                "จ่ายเต็ม", 1, 1, ""
            ])
            st.success(f"✅ บันทึกยอด {final_thb_amount:,.2f} บาท สำเร็จแล้วค่ะ!")

        sheet.append_rows(rows_to_append)
        
        st.session_state.pre_amount = None
        st.session_state.pre_note = ""
        st.session_state.pre_type = "รายจ่าย 🔴"
        st.session_state.pre_cat = "🍜 ค่าอาหาร/เครื่องดื่ม"
        st.session_state.pre_chan = " 💵 เงินสด "
        if "voice_input_key" in st.session_state: del st.session_state["voice_input_key"]
        
        st.rerun()

st.markdown("---")

# ==========================================
# ส่วนที่ 3: Dashboard & Cashflow Tabs
# ==========================================
st.markdown("### 📊 รายงานทางการเงิน & กระแสเงินสด")

if not df.empty:
    df['รายรับ'] = pd.to_numeric(df['รายรับ'].replace('', 0, regex=True))
    df['รายจ่าย'] = pd.to_numeric(df['รายจ่าย'].replace('', 0, regex=True))
    df['วันที่'] = pd.to_datetime(df['วันที่'])
    df['เดือน-ปี'] = df['วันที่'].dt.strftime('%Y-%m')
    df['งวดปัจจุบัน'] = pd.to_numeric(df['งวดปัจจุบัน'], errors='coerce').fillna(1)
    df['จำนวนงวด'] = pd.to_numeric(df['จำนวนงวด'], errors='coerce').fillna(1)
    
    tab1, tab2 = st.tabs(["💵 Cashflow (เงินสดจริง)", "💳 Credit Card (ภาระหนี้)"])
    
    with tab1:
        if tourist_mode:
            df['หมายเหตุ'] = df['หมายเหตุ'].fillna('')
            st.markdown("#### ✈️ สรุปค่าใช้จ่ายแยกตามทริป")
            trip_search = st.text_input("พิมพ์ชื่อทริปที่ต้องการดู:", value="Japan 2026")
            f_df = df[df['หมายเหตุ'].str.contains(f"#{trip_search}", na=False)]
            
            if not f_df.empty:
                st.error(f"**รายจ่ายรวมทริป:**\n## ฿ {f_df['รายจ่าย'].sum():,.2f}")
                fig_pie = px.pie(f_df[f_df['รายจ่าย'] > 0].groupby('รายการ', as_index=False)['รายจ่าย'].sum(), values='รายจ่าย', names='รายการ', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
                with st.expander("เปิดดูรายการทั้งหมดของทริปนี้"):
                    st.dataframe(f_df[['วันที่', 'รายการ', 'รายจ่าย', 'ช่องทาง', 'หมายเหตุ']].sort_values(by='วันที่', ascending=False), use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลบันทึกสำหรับทริปนี้ค่ะ")
        else:
            months_list = ["ดูทั้งหมด"] + sorted(df['เดือน-ปี'].unique().tolist(), reverse=True)
            sel_m = st.selectbox("📅 เลือกเดือน:", months_list)
            
            if sel_m != "ดูทั้งหมด":
                f_df = df[df['เดือน-ปี'] == sel_m]
                
                cash_in = f_df['รายรับ'].sum()
                cash_out_direct = f_df[(f_df['ช่องทาง'] != '💳 Credit Card')]['รายจ่าย'].sum()
                
                curr_date = pd.to_datetime(sel_m + '-01')
                prev_m = (curr_date - pd.DateOffset(months=1)).strftime('%Y-%m')
                prev_df = df[df['เดือน-ปี'] == prev_m]
                cc_full_prev = prev_df[(prev_df['ช่องทาง'] == '💳 Credit Card') & (prev_df['ประเภทการจ่าย'] == 'จ่ายเต็ม')]['รายจ่าย'].sum()
                
                cc_inst_this_m = f_df[(f_df['ช่องทาง'] == '💳 Credit Card') & (f_df['ประเภทการจ่าย'] == 'ผ่อนชำระ')]['รายจ่าย'].sum()
                
                actual_cc_bill = cc_full_prev + cc_inst_this_m
                total_cash_out = cash_out_direct + actual_cc_bill
                real_cash_balance = cash_in - total_cash_out
                
                st.markdown("###### *ยอดนี้สะท้อนกระแสเงินสดในกระเป๋า (นำบิลบัตรเครดิตรอบที่แล้วมาหักให้แล้ว)*")
                c1, c2, c3 = st.columns(3)
                c1.success(f"🟢 รับสุทธิ:\n\n**฿ {cash_in:,.2f}**")
                c2.error(f"🔴 จ่ายจริง:\n\n**฿ {total_cash_out:,.2f}**")
                c3.info(f"💰 เงินสดคงเหลือ:\n\n**฿ {real_cash_balance:,.2f}**")
                
                st.write(f"**💡 แตกยอดจ่ายจริง:** รายจ่ายเงินสด `฿ {cash_out_direct:,.2f}` + จ่ายบิลบัตรเครดิต `฿ {actual_cc_bill:,.2f}`")
                
                with st.expander("เปิดดูประวัติรายการทั้งหมด"):
                    cols_to_show = ['วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง', 'ประเภทการจ่าย']
                    st.dataframe(f_df[cols_to_show].sort_values(by='วันที่', ascending=False), use_container_width=True)
            else:
                st.write("กรุณาเลือกเดือนเพื่อดู Cashflow ค่ะ")

    with tab2:
        if sel_m != "ดูทั้งหมด":
            st.markdown(f"#### 💳 สรุปสถานะบัตรเครดิต (รอบเดือน {sel_m})")
            
            st.markdown(f"""
            <div style="background-color: #fff1f2; border: 1px solid #fda4af; border-left: 5px solid #e11d48; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                <p style="margin:0; color: #881337; font-size: 16px;">🚨 บิลบัตรเครดิตที่ต้องจ่ายในเดือนนี้</p>
                <h2 style="margin:0; color: #9f1239;">฿ {actual_cc_bill:,.2f}</h2>
                <p style="margin:0; color: #881337; font-size: 14px;">(ยอดรูดเต็มจากเดือนก่อน ฿ {cc_full_prev:,.2f} + ยอดผ่อนเดือนนี้ ฿ {cc_inst_this_m:,.2f})</p>
            </div>
            """, unsafe_allow_html=True)
            
            cc_full_this_m = f_df[(f_df['ช่องทาง'] == '💳 Credit Card') & (f_df['ประเภทการจ่าย'] == 'จ่ายเต็ม')]['รายจ่าย'].sum()
            cc_inst_start_this_m_df = f_df[(f_df['ช่องทาง'] == '💳 Credit Card') & (f_df['ประเภทการจ่าย'] == 'ผ่อนชำระ') & (f_df['งวดปัจจุบัน'] == 1)]
            cc_inst_swipe_total = (cc_inst_start_this_m_df['รายจ่าย'] * cc_inst_start_this_m_df['จำนวนงวด']).sum()
            cc_total_swiped_this_m = cc_full_this_m + cc_inst_swipe_total
            
            st.warning(f"🛒 **ยอดที่รูดบัตรซื้อของไปในเดือนนี้ (หนี้ใหม่):** ฿ {cc_total_swiped_this_m:,.2f}")
            
            st.markdown("##### 🧾 รายการที่กำลังผ่อนชำระ")
            inst_df = f_df[(f_df['ช่องทาง'] == '💳 Credit Card') & (f_df['ประเภทการจ่าย'] == 'ผ่อนชำระ')]
            if not inst_df.empty:
                show_inst = inst_df[['วันที่', 'รายการ', 'รายจ่าย', 'งวดปัจจุบัน', 'จำนวนงวด', 'หมายเหตุ']].sort_values(by='วันที่', ascending=False)
                st.dataframe(show_inst, use_container_width=True)
            else:
                st.write("ไม่มีรายการผ่อนชำระในเดือนนี้ค่ะ")
        else:
            st.write("กรุณาเลือกเดือนเพื่อดูสถานะบัตรเครดิตค่ะ")

else:
    st.info("ยังไม่มีข้อมูลเลยค่ะ เจ้านายลองบันทึกรายการแรกดูนะคะ!")
