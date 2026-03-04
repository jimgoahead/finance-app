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
    if "voice_input_key" in st.session_state:
        st.session_state.voice_input_key = ""

st.markdown("### 🎙️ สั่งงานด้วยเสียง (Magic Input)")
st.info("💡 **วิธีใช้:** แตะช่องสีฟ้าด้านล่าง กดไมค์ที่คีย์บอร์ดมือถือเพื่อพูด แล้วกดปุ่ม ✨ แยกคำ")

# 🎨 รวมโค้ดสีมาไว้ตรงนี้เลย! (ล็อกพิกัดแบบตายตัวเฉพาะส่วนนี้)
st.markdown("""
    <style>
    /* 1. แต่งช่อง Text Box เสียงให้เป็นสีฟ้า ฟอนต์ดำ และซ่อนหัวข้อ */
    div[data-testid="stTextInput"]:has(input[placeholder*="แตะที่นี่แล้วพูด"]) label { display: none !important; }
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

    /* 2. ล็อกสีปุ่มแยกคำ (เขียว) ในคอลัมน์ซ้าย */
    div[data-testid="stColumn"]:nth-child(1) div[data-testid="stButton"] button {
        background-color: #4CAF50 !important;
        color: white !important;
        border-color: #4CAF50 !important;
        font-weight: bold !important;
    }

    /* 3. ล็อกสีปุ่มล้างคำ (แดง) ในคอลัมน์ขวา */
    div[data-testid="stColumn"]:nth-child(2) div[data-testid="stButton"] button {
        background-color: #f44336 !important;
        color: white !important;
        border-color: #f44336 !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# ช่องรับข้อความเสียง
voice_input = st.text_input("ข้อความเสียง:", key="voice_input_key", placeholder="แตะที่นี่แล้วพูด... เช่น: รายจ่ายค่าอาหาร 150 บาท จ่ายด้วย Kbank")

# จัดเรียงปุ่ม 2 ปุ่มให้อยู่แถวเดียวกัน
col1, col2 = st.columns(2)
with col1:
    process_btn = st.button("✨ แยกคำ", use_container_width=True)
with col2:
    clear_btn = st.button("❌ ล้างคำ", use_container_width=True, on_click=clear_voice_text)

# ระบบประมวลผลคำพูด
if process_btn and st.session_state.voice_input_key:
    text = st.session_state.voice_input_key.lower()
    
    # แกะประเภท (Type)
    if "รายรับ" in text:
        st.session_state.pre_type = "รายรับ 🟢"
    else:
        st.session_state.pre_type = "รายจ่าย 🔴"
        
    # แกะหมายเหตุ (Note)
    if "หมายเหตุ" in text:
        parts = text.split("หมายเหตุ", 1)
        st.session_state.pre_note = parts[1].strip()
        text_to_search = parts[0] 
    else:
        st.session_state.pre_note = "" 
        text_to_search = text
        
    # แกะจำนวนเงิน (Amount)
    amounts = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', text_to_search)
    if amounts:
        st.session_state.pre_amount = float(amounts[0].replace(',', ''))
        
    # แกะหมวดหมู่ (Category)
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

    # แกะช่องทาง (Channel)
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
