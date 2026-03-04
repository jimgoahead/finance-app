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
    elif "scb" in text_to_search or "ไทยพาณิชย์" in text_to_search:
        st.session_state.pre_chan = "🟣 SCB"
    elif "ktb" in text_to_search or "กรุงไทย" in text_to_search:
        st.session_state.pre_chan = "🦅 KTB"
    elif "บัตร" in text_to_search or "เครดิต" in text_to_search or "credit" in text_to_search:
        st.session_state.pre_chan = "💳 Credit Card"
    elif "เงินสด" in text_to_search or "สด" in text_to_search:
        st.session_state.pre_chan = " 💵 เงินสด "
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
        
    try:
        cat_idx = category_options.index(st.session_state.pre_cat)
    except ValueError:
        cat_idx = 0
        
    category = st.selectbox("🏷️ หมวดหมู่", category_options, index=cat_idx)
    
    if tourist_mode:
        st.markdown("🎌 **ข้อมูลสกุลเงินต่างประเทศ**")
        col_curr, col_rate = st.columns(2)
        with col_curr:
            currency = st.selectbox("สกุลเงิน", ["JPY (เยน)", "USD (ดอลลาร์)"])
        with col_rate:
            exchange_rate = st.number_input("เรทแลกเปลี่ยน", value=None, format="%.4f", step=0.0100, placeholder="ระบุเรท...")
        
        curr_symbol = currency.split(' ')[0]
        amount_input = st.number_input(
            f"💰 จำนวนเงิน ({curr_symbol})", 
            min_value=0.0, 
            format="%.2f", 
            step=100.0, 
            value=st.session_state.pre_amount, 
            placeholder=f"แตะระบุยอด {curr_symbol}..."
        )
    else:
        amount_input = st.number_input(
            "💰 จำนวนเงิน (บาท)", 
            min_value=0.0, 
            format="%.2f", 
            step=100.0, 
            value=st.session_state.pre_amount, 
            placeholder="แตะเพื่อระบุยอดเงิน..."
        )
    
    channel_options = ["💳 Credit Card", "🦅 KTB", "🟢 K-BANK", "🟣 SCB", " 💵 เงินสด ", "📝อื่นๆ"]
    try:
        chan_idx = channel_options.index(st.session_state.pre_chan)
    except ValueError:
        chan_idx = 4 
    channel = st.radio("🏦 ช่องทาง", channel_options, index=chan_idx, horizontal=True)
    
    note = st.text_input("📝 หมายเหตุ (ถ้ามี)", value=st.session_state.pre_note)

    if st.form_submit_button("บันทึกข้อมูลลงตาราง"):
        if amount_input is None or amount_input <= 0:
            st.error("⚠️ เจ้านายอย่าลืมใส่จำนวนเงินนะคะ!")
        elif tourist_mode and (exchange_rate is None or exchange_rate <= 0):
            st.error("⚠️ เจ้านายอย่าลืมระบุเรทแลกเปลี่ยนนะคะ!")
        else:
            if tourist_mode:
                final_thb_amount = amount_input * exchange_rate
                curr_symbol = currency.split(' ')[0]
                final_note = f"#{trip_name} [{curr_symbol} {amount_input:,.2f} @{exchange_rate}] {note}".strip()
            else:
                final_thb_amount = amount_input
                final_note = note

            all_values = sheet.get_all_values()
            next_id = len(all_values)
            income_amt = final_thb_amount if "รายรับ" in type_ else ""
            expense_amt = final_thb_amount if "รายจ่าย" in type_ else ""
            
            sheet.append_row([next_id, date.strftime("%Y-%m-%d"), category, income_amt, expense_amt, channel, final_note])
            st.success(f"✅ บันทึกยอด {final_thb_amount:,.2f} บาท สำเร็จแล้วค่ะ!")
            
            # 💡 แก้ไขบั๊กตรงนี้: ใช้ del ลบออกจากหน่วยความจำแทนการกำหนดค่าเป็น ""
            st.session_state.pre_amount = None
            st.session_state.pre_note = ""
            st.session_state.pre_type = "รายจ่าย 🔴"
            st.session_state.pre_cat = "🍜 ค่าอาหาร/เครื่องดื่ม"
            st.session_state.pre_chan = " 💵 เงินสด "
            if "voice_input_key" in st.session_state:
                del st.session_state["voice_input_key"]
            
            st.rerun()

st.markdown("---")

# ==========================================
# ส่วนที่ 3: Dashboard วิเคราะห์ข้อมูล
# ==========================================
st.markdown("### 📊 Dashboard วิเคราะห์ข้อมูล")

if not df.empty:
    df['รายรับ'] = pd.to_numeric(df['รายรับ'].replace('', 0, regex=True))
    df['รายจ่าย'] = pd.to_numeric(df['รายจ่าย'].replace('', 0, regex=True))
    df['วันที่'] = pd.to_datetime(df['วันที่'])
    df['เดือน-ปี'] = df['วันที่'].dt.strftime('%Y-%m')
    
    if tourist_mode:
        df['หมายเหตุ'] = df['หมายเหตุ'].fillna('')
        st.markdown("#### ✈️ สรุปค่าใช้จ่ายแยกตามทริป")
        trip_search = st.text_input("พิมพ์ชื่อทริปที่ต้องการดู (เช่น Japan 2026):", value="Japan 2026")
        
        filtered_df = df[df['หมายเหตุ'].str.contains(f"#{trip_search}", na=False)]
        
        if not filtered_df.empty:
            total_trip_expense = filtered_df['รายจ่าย'].sum()
            st.error(f"**รายจ่ายรวมทริป '{trip_search}':**\n## ฿ {total_trip_expense:,.2f}")
            
            st.markdown("##### 🍩 สัดส่วนค่าใช้จ่ายในทริปนี้")
            cat_expense = filtered_df[filtered_df['รายจ่าย'] > 0].groupby('รายการ', as_index=False)['รายจ่าย'].sum()
            fig_pie = px.pie(cat_expense, values='รายจ่าย', names='รายการ', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='horizontal')
            fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("##### 📈 ยอดใช้จ่ายรายวัน")
            exp_only = filtered_df[filtered_df['รายจ่าย'] > 0].copy()
            if not exp_only.empty:
                exp_only['วันที่_format'] = exp_only['วันที่'].dt.strftime('%Y-%m-%d')
                daily_expense = exp_only.groupby('วันที่_format', as_index=False)['รายจ่าย'].sum()
                
                fig_line = px.line(daily_expense, x='วันที่_format', y='รายจ่าย', markers=True, text='รายจ่าย')
                fig_line.update_traces(textposition="top center", texttemplate='%{text:,.0f}')
                fig_line.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="วันที่", yaxis_title="ยอดเงิน (บาท)")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลรายจ่ายสำหรับสร้างกราฟค่ะ")

            with st.expander("เปิดดูรายการทั้งหมดของทริปนี้"):
                cols_to_show = ['วันที่', 'รายการ', 'รายจ่าย', 'ช่องทาง', 'หมายเหตุ']
                st.dataframe(filtered_df[cols_to_show].sort_values(by='วันที่', ascending=False), use_container_width=True)
        else:
            st.info(f"ยังไม่มีข้อมูลบันทึกสำหรับทริป '{trip_search}' ค่ะ")

    else:
        months_list = ["ดูทั้งหมด"] + sorted(df['เดือน-ปี'].unique().tolist(), reverse=True)
        selected_month = st.selectbox("📅 เลือกเดือนที่ต้องการดูข้อมูล:", months_list)
        
        if selected_month != "ดูทั้งหมด":
            filtered_df = df[df['เดือน-ปี'] == selected_month]
        else:
            filtered_df = df

        total_income = filtered_df['รายรับ'].sum()
        total_expense = filtered_df['รายจ่าย'].sum()
        balance = total_income - total_expense

        col1, col2 = st.columns(2)
        col1.success(f"**รายรับรวม:**\n### ฿ {total_income:,.2f}")
        col2.error(f"**รายจ่ายรวม:**\n### ฿ {total_expense:,.2f}")
        st.info(f"**ยอดคงเหลือ:**\n## ฿ {balance:,.2f}")

        cc_expense = filtered_df[filtered_df['ช่องทาง'] == '💳 Credit Card']['รายจ่าย'].sum()
        st.markdown(f"""
        <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #64748b; padding: 15px; border-radius: 10px; margin-top: 10px; margin-bottom: 20px;">
            <p style="margin:0; color: #475569; font-size: 16px;">💳 เตรียมจ่ายบิลบัตรเครดิต (รูดในเดือนนี้)</p>
            <h3 style="margin:0; color: #0f172a;">฿ {cc_expense:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🏆 วิเคราะห์หมวดหมู่การใช้จ่าย")
        expense_df = filtered_df[filtered_df['รายจ่าย'] > 0]
        
        if not expense_df.empty:
            cat_expense = expense_df.groupby('รายการ', as_index=False)['รายจ่าย'].sum().sort_values(by='รายจ่าย', ascending=False)
            top_cat = cat_expense.iloc[0]['รายการ']
            top_amt = cat_expense.iloc[0]['รายจ่าย']
            st.warning(f"🥇 **จ่ายหนักสุดในหมวด:** {top_cat} (฿ {top_amt:,.2f})")
            
            fig = px.pie(cat_expense, values='รายจ่าย', names='รายการ', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='horizontal')
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("ยังไม่มีรายจ่ายในเดือนนี้ค่ะ")

        with st.expander("เปิดดูประวัติรายการทั้งหมด"):
            cols_to_show = ['วันที่', 'รายการ', 'รายรับ', 'รายจ่าย', 'ช่องทาง', 'หมายเหตุ']
            st.dataframe(filtered_df[cols_to_show].sort_values(by='วันที่', ascending=False), use_container_width=True)
else:
    st.info("ยังไม่มีข้อมูลเลยค่ะ เจ้านายลองบันทึกรายการแรกดูนะคะ!")
