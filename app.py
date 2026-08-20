import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests
import urllib.parse
from PIL import Image

# പേജ് സെറ്റിംഗ്സ്
st.set_page_config(page_title="തോട്ടം പ്രൊഫഷണൽ മാനേജർ ERP (Audit Edition)", page_icon="🌿", layout="wide")

# Google Sheets കണക്ഷൻ
@st.cache_resource
def get_db_connection():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Thottam_ERP_Database")
        return sheet
    except Exception as e:
        return None

db = get_db_connection()

# ആക്ടിവിറ്റി ലോഗ് ചെയ്യാനുള്ള ഫങ്ഷൻ (Audit Trail)
def log_activity(username, action_type, details):
    try:
        if db:
            ws = db.worksheet("activity_logs")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.append_row([username, action_type, details, timestamp])
    except:
        pass

# തത്സമയ കാലാവസ്ഥാ ഫങ്ഷൻ
def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=10.0889&longitude=77.0595&current=temperature_2m,relative_humidity_2m,precipitation"
        response = requests.get(url, timeout=3).json()
        temp = response['current']['temperature_2m']
        humidity = response['current']['relative_humidity_2m']
        rain = response['current']['precipitation']
        return temp, humidity, rain
    except:
        return 24.5, 82.0, 0.0

# വിപണി വില സിമുലേഷൻ
def get_market_prices():
    return {
        "ഏലം (Cardamom - 7mm/8mm)": "₹ 1,650 / kg",
        "കുരുമുളക് (Black Pepper)": "₹ 620 / kg",
        "ജാതിക്ക (Nutmeg)": "₹ 240 / kg",
        "ജാതിപത്രി (Mace)": "₹ 1,150 / kg"
    }

# സെഷൻ സ്റ്റേറ്റുകൾ പരിശോധിക്കുക
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

if not st.session_state["logged_in"]:
    st.title("🌿 തോട്ടം പ്രൊഫഷണൽ മാനേജർ ERP (Audit Edition)")
    st.subheader("🔐 സിസ്റ്റത്തിലേക്ക് ലോഗിൻ ചെയ്യുക")
    
    login_type = st.radio("ലോഗിൻ വിഭാഗം തിരഞ്ഞെടുക്കുക", ["മാനേജ്‌മെന്റ് / അഡ്മിൻ (Admin/Supervisor)", "തൊഴിലാളി പാസ്ബുക്ക് (Worker Portal)"])
    
    if login_type == "മാനേജ്‌മെന്റ് / അഡ്മിൻ (Admin/Supervisor)":
        with st.form("admin_login"):
            username = st.text_input("യൂസർ നെയിം")
            password = st.text_input("പാസ്‌വേഡ്", type="password")
            submit = st.form_submit_button("ലോഗിൻ ചെയ്യുക")
            
            if submit:
                if username == "admin" and password == "admin123":
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = "തോട്ടം ഉടമ (Admin)"
                    st.session_state["role"] = "Admin"
                    log_activity("Admin", "LOGIN", "Successfully logged into system")
                    st.rerun()
                elif username == "supervisor" and password == "sup123":
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = "സൂപ്പർവൈസർ (Supervisor)"
                    st.session_state["role"] = "Supervisor"
                    log_activity("Supervisor", "LOGIN", "Successfully logged into system")
                    st.rerun()
                else:
                    st.error("❌ തെറ്റായ യൂസർ നെയിം അല്ലെങ്കിൽ പാസ്‌വേഡ്!")
        st.info("💡 **ടെസ്റ്റ് ലോഗിൻ:** Admin (`admin` / `admin123`) | Supervisor (`supervisor` / `sup123`)")
        
    else:
        with st.form("worker_login"):
            worker_id = st.text_input("തൊഴിലാളിയുടെ പേര് / ID")
            w_pass = st.text_input("പാസ്‌വേഡ്", type="password")
            w_sub = st.form_submit_button("പാസ്ബുക്ക് തുറക്കുക")
            if w_sub and worker_id:
                st.session_state["logged_in"] = True
                st.session_state["username"] = worker_id
                st.session_state["role"] = "Worker"
                log_activity(worker_id, "WORKER_LOGIN", "Viewed digital passbook")
                st.rerun()

else:
    if db is None:
        st.error("⚠️ ഗൂഗിൾ ഷീറ്റ് കണക്ഷൻ പരാജയപ്പെട്ടു!")
        st.stop()

    st.sidebar.success(f"ലോഗിൻ ചെയ്തിരിക്കുന്നു:\n**{st.session_state['username']}**")
    
    lang = st.sidebar.selectbox("ভাষা / Language", ["മലയാളം", "English"])

    if st.sidebar.button("ലോഗ് ഔട്ട് (Logout)"):
        log_activity(st.session_state['username'], "LOGOUT", "Logged out from system")
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = ""
        st.rerun()

    def get_data(worksheet_name):
        try:
            ws = db.worksheet(worksheet_name)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except:
            return pd.DataFrame()

    if st.session_state["role"] == "Worker":
        st.subheader(f"📖 ഡിജിറ്റൽ പാസ്ബുക്ക് - {st.session_state['username']}")
        workers_df = get_data("workers")
        adv_df = get_data("advances")
        
        if not workers_df.empty and 'name' in workers_df.columns:
            my_work = workers_df[workers_df['name'].str.lower() == st.session_state['username'].lower()]
            st.write("### ഹാജർ വിവരങ്ങൾ")
            st.dataframe(my_work)
            
        if not adv_df.empty and 'name' in adv_df.columns:
            my_adv = adv_df[adv_df['name'].str.lower() == st.session_state['username'].lower()]
            st.write("### അഡ്വാൻസ് വിവരങ്ങൾ")
            st.dataframe(my_adv)
            
        st.stop()

    if st.session_state["role"] == "Admin":
        menu_items = [
            "ഡാഷ്‌ബോർഡ്", "ഓഡിറ്റ് ട്രെയ്ൽ (Activity Log)", "തൊഴിലാളി & UPI പേയ്‌മെന്റ്", 
            "ലേഖന വിശകലനം (Productivity)", "മണ്ണുപരിശോധന (Soil Test Log)", "എക്സ്പോർട്ട് & ഷിപ്പിംഗ്", 
            "🤖 AI തോട്ടം ചാറ്റ്‌ബോട്ട്", "🔮 AI വിളവെടുപ്പ് പ്രവചനം", "💡 AI ചെലവ് ഒപ്റ്റിമൈസർ", 
            "AI രോഗ നിർണ്ണയം (AI Diagnosis)", "വോയ്സ് എൻട്രി (Voice Command)", 
            "വിളവെടുപ്പ് & ഗ്രേഡിംഗ്", "സ്റ്റോക്ക് & ഇൻവെന്ററി", "വിൽപ്പനയും ബില്ലിംഗും", 
            "മെഷിനറി & ഫ്യുവൽ", "ചെലവ് കണക്കുകൾ", "ലാഭ-നഷ്ടക്കണക്ക് (P&L)", "റിപ്പോർട്ടുകൾ"
        ]
    else:
        menu_items = ["ഡാഷ്‌ബോർഡ്", "തൊഴിലാളി & UPI പേയ്‌മെന്റ്", "🤖 AI തോട്ടം ചാറ്റ്‌ബോട്ട്", "AI രോഗ നിർണ്ണയം (AI Diagnosis)", "വിളവെടുപ്പ് & ഗ്രേഡിംഗ്"]

    menu = st.sidebar.selectbox("Navigation", menu_items)

    # 1. ഡാഷ്‌ബോർഡ്
    if menu == "ഡാഷ്‌ബോർഡ്":
        st.subheader("📊 സ്മാർട്ട് ഡാഷ്‌ബോർഡും ലൈവ് വിപണി വിലയും")
        
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown("### 🌤️ തോട്ടം കാലാവസ്ഥ")
            temp, humidity, rain = get_weather()
            w1, w2, w3 = st.columns(3)
            w1.metric("🌡️ താപനില", f"{temp} °C")
            w2.metric("💧 ഈർപ്പം", f"{humidity} %")
            w3.metric("🌧️ മഴ", f"{rain} mm")
            if humidity > 85 and rain > 2:
                st.warning("⚠️ ജാഗ്രത: ഏലത്തിൽ കാപ്സ്യൂൾ റോട്ട് രോഗം വരാൻ സാധ്യതയുള്ള കാലാവസ്ഥ!")
            else:
                st.success("✅ കാലാവസ്ഥ അനുകൂലം.")

        with col_w2:
            st.markdown("### 📈 സ്പൈസസ് ബോർഡ് ലൈവ് വിപണി വില")
            prices = get_market_prices()
            for crop, price in prices.items():
                st.info(f"**{crop}**: {price}")

        st.markdown("---")
        
        workers_df = get_data("workers")
        yields_df = get_data("yields")
        expenses_df = get_data("expenses")
        sales_df = get_data("sales")
        
        total_workers = len(workers_df) if not workers_df.empty else 0
        total_yield = yields_df['quantity'].sum() if not yields_df.empty and 'quantity' in yields_df.columns else 0
        total_expense = expenses_df['amount'].sum() if not expenses_df.empty and 'amount' in expenses_df.columns else 0
        total_revenue = sales_df['total_amount'].sum() if not sales_df.empty and 'total_amount' in sales_df.columns else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("തൊഴിലാളികൾ", f"{total_workers} പേർ")
        col2.metric("വിളവെടുപ്പ്", f"{total_yield} കിലോ")
        if st.session_state["role"] == "Admin":
            col3.metric("ആകെ വരുമാനം", f"₹ {total_revenue}")
            col4.metric("ആകെ ചെലവ്", f"₹ {total_expense}")

    # 2. ഓഡിറ്റ് ട്രെയ്ൽ & ആക്ടിവിറ്റി ലോഗ് (Activity Log)
    elif menu == "ഓഡിറ്റ് ട്രെയ്ൽ (Activity Log)" and st.session_state["role"] == "Admin":
        st.subheader("🛡️ സിസ്റ്റം സുരക്ഷ & ആക്ടിവിറ്റി ലോഗ് (Audit Trail)")
        st.write("ആപ്പിൽ നടന്ന ലോഗിൻ വിവരങ്ങളും മറ്റ് പ്രവർത്തനങ്ങളും ഇവിടെ നിരീക്ഷിക്കാം:")
        
        logs_df = get_data("activity_logs")
        if not logs_df.empty:
            st.dataframe(logs_df)
        else:
            st.info("ആക്ടിവിറ്റി ലോഗുകൾ ഒന്നും ലഭ്യമല്ല.")

    # 3. തൊഴിലാളി & UPI പേയ്‌മെന്റ് സിസ്റ്റം
    elif menu == "തൊഴിലാളി & UPI പേയ്‌മെന്റ്":
        st.subheader("👥 തൊഴിലാളി ഹാജറും UPI ഡിജിറ്റൽ പേയ്‌മെന്റും")
        tab_a, tab_b, tab_c = st.tabs(["ഹാജർ രേഖപ്പെടുത്തൽ", "അഡ്വാൻസ് ലെഡ്ജർ", "UPI കൂലി നൽകൽ"])
        
        with tab_a:
            with st.form("attendance_form"):
                worker_name = st.text_input("തൊഴിലാളിയുടെ പേര്")
                block_name = st.selectbox("ബ്ലോക്ക്", ["ബ്ലോക്ക് A (ഏലം)", "ബ്ലോക്ക് B (കുരുമുളക്)", "ബ്ലോക്ക് C (ജാതിക്ക)", "ജനറൽ"])
                work_type = st.selectbox("ജോലിയുടെ തരം", ["ഏലം പറിപ്പ്", "വളപ്രയോഗം", "കള വെട്ടൽ", "മറ്റ്‌ പരിപാലനം"])
                wage = st.number_input("ദിവസക്കൂലി (₹)", min_value=0.0, value=500.0)
                date = st.date_input("തീയതി", datetime.now())
                
                submitted = st.form_submit_button("ഹാജർ സേവ് ചെയ്യുക")
                if submitted and worker_name:
                    ws = db.worksheet("workers")
                    ws.append_row([worker_name, block_name, work_type, wage, "GPS Verified", str(date)])
                    log_activity(st.session_state['username'], "ADD_ATTENDANCE", f"Added attendance for {worker_name}")
                    st.success("ഹാജർ വിജയകരമായി സേവ് ചെയ്തു!")
                    
        with tab_b:
            with st.form("advance_form"):
                adv_worker = st.text_input("തൊഴിലാളിയുടെ പേര്")
                adv_amount = st.number_input("മുൻകൂർ അഡ്വാൻസ് തുക (₹)", min_value=0.0, value=1000.0)
                adv_date = st.date_input("തീയതി", datetime.now())
                
                adv_sub = st.form_submit_button("അഡ്വാൻസ് സേവ് ചെയ്യുക")
                if adv_sub and adv_worker:
                    ws = db.worksheet("advances")
                    ws.append_row([adv_worker, adv_amount, str(adv_date)])
                    log_activity(st.session_state['username'], "ADD_ADVANCE", f"Given advance to {adv_worker}")
                    st.success("അഡ്വാൻസ് കണക്ക് സേവ് ചെയ്തു!")

        with tab_c:
            with st.form("upi_form"):
                upi_worker = st.text_input("തൊഴിലാളിയുടെ പേര്")
                upi_id = st.text_input("UPI ID / GPay Number")
                pay_amount = st.number_input("നൽകേണ്ട കൂലി തുക (₹)", min_value=0.0, value=500.0)
                
                upi_sub = st.form_submit_button("UPI വഴി പണമടയ്ക്കുക")
                if upi_sub and upi_id:
                    upi_link = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(upi_worker)}&am={pay_amount}&cu=INR"
                    log_activity(st.session_state['username'], "UPI_PAYMENT", f"Generated UPI pay link for {upi_worker}")
                    st.success(f"🎉 {upi_worker}-ന് ₹ {pay_amount} നൽകാനുള്ള UPI ലിങ്ക് തയ്യാറാണ്!")
                    st.markdown(f"📲 **[UPI ആപ്പ് വഴി പണമടയ്ക്കാൻ ഇവിടെ ക്ലിക്ക് ചെയ്യുക]({upi_link})**", unsafe_allow_html=True)

    # 4. ലേബർ പ്രൊഡക്റ്റിവിറ്റി അനലിറ്റിക്സ്
    elif menu == "ലേഖന വിശകലനം (Productivity)":
        st.subheader("📈 ലേബർ പ്രൊഡക്റ്റിവിറ്റി അനലിറ്റിക്സ്")
        yields_df = get_data("yields")
        if not yields_df.empty:
            st.dataframe(yields_df)
        else:
            st.info("വിളവെടുപ്പ് ഡാറ്റകൾ ലഭ്യമല്ല.")

    # 5. മണ്ണുപരിശോധനാ ഫലങ്ങൾ
    elif menu == "മണ്ണുപരിശോധന (Soil Test Log)":
        st.subheader("🧪 തോട്ടം മണ്ണ് & ജല പരിശോധനാ റിപ്പോർട്ട് മാനേജർ")
        with st.form("soil_form"):
            block_s = st.selectbox("ബ്ലോക്ക് തിരഞ്ഞെടുക്കുക", ["ബ്ലോക്ക് A (ഏലം)", "ബ്ലോക്ക് B (കുരുമുളക്)", "ബ്ലോക്ക് C (ജാതിക്ക)"])
            soil_ph = st.number_input("മണ്ണിലെ pH നില (Soil pH Level)", min_value=0.0, max_value=14.0, value=6.2)
            nutrients = st.text_input("പോഷക വിവരങ്ങൾ", value="Nitrogen: Medium, Phosphorus: High")
            water_quality = st.selectbox("ജലത്തിന്റെ ഗുണനിലവാരം", ["ഉത്തമം (Good)", "ശ്രദ്ധിക്കുക (Moderate)", "മോശം (Poor)"])
            date = st.date_input("തീയതി", datetime.now())
            
            if st.form_submit_button("പരിശോധനാ ഫലം സേവ് ചെയ്യുക"):
                ws = db.worksheet("soil_tests")
                ws.append_row([block_s, soil_ph, nutrients, water_quality, str(date)])
                log_activity(st.session_state['username'], "ADD_SOIL_TEST", f"Added soil test for {block_s}")
                st.success("മണ്ണുപരിശോധനാ ഫലം വിജയകരമായി സേവ് ചെയ്തു!")

    # 6. എക്സ്പോർട്ട് & ഷിപ്പിംഗ് മാനേജർ
    elif menu == "എക്സ്പോർട്ട് & ഷിപ്പിംഗ്":
        st.subheader("🚢 അന്താരാഷ്ട്ര എക്സ്പോർട്ട് & ഷിപ്പിംഗ് ട്രാക്കർ")
        with st.form("export_form"):
            buyer_country = st.text_input("വാങ്ങുന്ന രാജ്യം / കമ്പനി")
            export_crop = st.selectbox("കയറ്റി അയക്കുന്ന ഉത്പന്നം", ["ഏലം (Cardamom Grade A)", "കുരുമുളക്", "ജാതിക്ക"])
            export_qty = st.number_input("അളവ് (കിലോയിൽ)", min_value=0.0, value=100.0)
            shipping_cost = st.number_input("ഷിപ്പിംഗ് ചെലവ് (₹)", min_value=0.0, value=5000.0)
            date = st.date_input("തീയതി", datetime.now())
            
            if st.form_submit_button("എക്സ്പോർട്ട് റെക്കോർഡ് സേവ് ചെയ്യുക") and buyer_country:
                ws = db.worksheet("exports")
                ws.append_row([buyer_country, export_crop, export_qty, shipping_cost, str(date)])
                log_activity(st.session_state['username'], "ADD_EXPORT", f"Added export record for {buyer_country}")
                st.success("എക്സ്പോർട്ട് വിവരങ്ങൾ സേവ് ചെയ്തു!")

    # 7. AI തോട്ടം ചാറ്റ്‌ബോട്ട്
    elif menu == "🤖 AI തോട്ടം ചാറ്റ്‌ബോട്ട്":
        st.subheader("🤖 AI അഗ്രികൾച്ചർ അസിസ്റ്റന്റ് (Farming Chatbot)")
        user_query = st.text_input("കൃഷി സംബന്ധമായ സംശയങ്ങൾ ഇവിടെ ചോദിക്കുക:")
        if st.button("AI-യോട് ചോദിക്കുക"):
            if user_query:
                st.success("💡 **AI അസിസ്റ്റന്റിന്റെ മറുപടി:**")
                st.write(f"'{user_query}' എന്ന വിഷയത്തിൽ, തോട്ടത്തിലെ നിലവിലെ മണ്ണും കാലാവസ്ഥയും പരിശോധിച്ച ശേഷം ആവശ്യത്തിന് വളപ്രയോഗവും ജലസേചനവും നടത്താൻ ശ്രദ്ധിക്കുക.")
            else:
                st.warning("ദയവായി ഒരു ചോദ്യം ടൈപ്പ് ചെയ്യുക.")

    # 8. AI വിളവെടുപ്പ് പ്രവചനം
    elif menu == "🔮 AI വിളവെടുപ്പ് പ്രവചനം":
        st.subheader("🔮 AI വിളവെടുപ്പ് പ്രവചനം (Yield Predictive Analytics)")
        if st.button("പ്രവചനം നടത്തുക"):
            st.success("📊 **AI പ്രവചന റിസൾട്ട്:**")
            col_p1, col_p2 = st.columns(2)
            col_p1.metric("ഏലം", "approx. 420 kg", "+12%")
            col_p2.metric("കുരുമുളക്", "approx. 280 kg", "+8%")

    # 9. AI ചെലവ് ഒപ്റ്റിമൈസർ
    elif menu == "💡 AI ചെലവ് ഒപ്റ്റിമൈസർ":
        st.subheader("💡 AI ചെലവ് ഒപ്റ്റിമൈസേഷൻ & അഡ്വൈസറി")
        if st.button("ചെലവ് വിശകലനം ചെയ്യുക"):
            st.success("🔍 **AI നിർദ്ദേശങ്ങൾ:** രാസവളങ്ങൾക്ക് പകരം ജൈവവളങ്ങൾ ഉപയോഗിക്കുന്നത് വഴി 15% ചെലവ് കുറയ്ക്കാം.")

    # 10. AI രോഗ നിർണ്ണയം
    elif menu == "AI രോഗ നിർണ്ണയം (AI Diagnosis)":
        st.subheader("🤖 AI അധിഷ്ഠിത സസ്യ രോഗ നിർണ്ണയം (AI Crop Doctor)")
        uploaded_file = st.file_uploader("ഇലയുടെ ചിത്രം അപ്‌ലോഡ് ചെയ്യുക", type=["jpg", "png", "jpeg"])
        if uploaded_file is not None:
            st.image(uploaded_file, caption="അപ്‌ലോഡ് ചെയ്ത ചിത്രം", use_container_width=True)
            if st.button("AI വിശകലനം നടത്തുക"):
                st.success("🔬 **രോഗം കണ്ടെത്തൽ:** കാപ്സ്യൂൾ റോട്ട് (Capsule Rot). കോപ്പർ ഓക്‌സിക്ലോറൈഡ് മരുന്ന് തളിക്കുക.")

    # 11. വോയ്സ് എൻട്രി
    elif menu == "വോയ്സ് എൻട്രി (Voice Command)":
        st.subheader("🎙️ മലയാളം വോയ്സ് കമാൻഡ് എൻട്രി")
        voice_text = st.text_area("സംസാരിച്ചതിന്റെ ടെക്സ്റ്റ് രൂപം")
        if st.button("സേവ് ചെയ്യുക"):
            log_activity(st.session_state['username'], "VOICE_ENTRY", f"Saved voice entry: {voice_text}")
            st.success("വോയ്സ് ഡാറ്റ സേവ് ചെയ്തു!")

    # 12. വിളവെടുപ്പ് & ഗ്രേഡിംഗ്
    elif menu == "വിളവെടുപ്പ് & ഗ്രേഡിംഗ്":
        st.subheader("🌾 വിളവെടുപ്പും ബാച്ച് ട്രാക്കിംഗും")
        with st.form("yield_form"):
            crop_name = st.selectbox("വിള", ["ഏലം", "കുരുമുളക്", "ജാതിക്ക", "വഴന"])
            block_source = st.selectbox("പ്ലോട്ട്", ["ബ്ലോക്ക് A", "ബ്ലോക്ക് B", "ബ്ലോക്ക് C"])
            grade = st.selectbox("ഗ്രേഡ്", ["6mm", "7mm", "8mm", "Medium", "Bulk"])
            quantity = st.number_input("അളവ് (കിലോയിൽ)", min_value=0.0, value=0.0)
            batch_id = st.text_input("ബാച്ച് കോഡ്", value=f"BAT-{datetime.now().strftime('%d%m%Y')}")
            date = st.date_input("തീയതി", datetime.now())
            
            if st.form_submit_button("വിവരങ്ങൾ ചേർക്കുക") and quantity > 0:
                ws = db.worksheet("yields")
                ws.append_row([crop_name, block_source, grade, quantity, batch_id, str(date)])
                log_activity(st.session_state['username'], "ADD_YIELD", f"Added yield for {crop_name} ({quantity} kg)")
                st.success("വിളവെടുപ്പ് വിവരങ്ങൾ സേവ് ചെയ്തു!")

    # 13. ഇൻവെന്ററി
    elif menu == "സ്റ്റോക്ക് & ഇൻവെന്ററി" and st.session_state["role"] == "Admin":
        st.subheader("📦 വളങ്ങളും കീടനാശിനികളും (Inventory)")
        with st.form("inv_form"):
            item_name = st.text_input("പേര്")
            category = st.selectbox("വിഭാഗം", ["വളങ്ങൾ", "കീടനാശിനികൾ", "ഉപകരണങ്ങൾ"])
            quantity = st.number_input("അളവ്", min_value=0.0, value=10.0)
            date = st.date_input("തീയതി", datetime.now())
            if st.form_submit_button("സ്റ്റോക്ക് സേവ് ചെയ്യുക") and item_name:
                ws = db.worksheet("inventory")
                ws.append_row([item_name, category, quantity, str(date)])
                log_activity(st.session_state['username'], "ADD_INVENTORY", f"Added inventory item {item_name}")
                st.success("ഇൻവെന്ററി അപ്ഡേറ്റ് ചെയ്തു!")

    # 14. വിൽപ്പനയും ബില്ലിംഗും
    elif menu == "വിൽപ്പനയും ബില്ലിംഗും" and st.session_state["role"] == "Admin":
        st.subheader("🧾 ഡിജിറ്റൽ ഇൻവോയ്സും QR കോഡ് ബില്ലിംഗും")
        with st.form("sales_form"):
            buyer_name = st.text_input("വായക്കാരന്റെ പേര്")
            phone_no = st.text_input("ഫോൺ നമ്പർ (WhatsApp)")
            crop_sold = st.selectbox("വിറ്റ ഉത്പന്നം", ["ഏലം", "കുരുമുളക്", "ജാതിക്ക", "വഴന"])
            quantity_sold = st.number_input("അളവ് (കിലോയിൽ)", min_value=0.0, value=10.0)
            price_per_kg = st.number_input("കിലോ വില (₹)", min_value=0.0, value=1650.0)
            gst_percent = st.selectbox("GST (%)", [0, 5, 12, 18])
            date = st.date_input("തീയതി", datetime.now())
            
            subtotal = quantity_sold * price_per_kg
            total_amount = subtotal + (subtotal * (gst_percent / 100))
            
            if st.form_submit_button("ബിൽ സേവ് ചെയ്യുക") and buyer_name:
                ws = db.worksheet("sales")
                ws.append_row([buyer_name, phone_no, crop_sold, quantity_sold, price_per_kg, gst_percent, total_amount, str(date)])
                log_activity(st.session_state['username'], "ADD_SALE", f"Sold {crop_sold} to {buyer_name} for Rs. {total_amount}")
                st.success(f"🎉 ബിൽ സേവ് ചെയ്തു! ആകെ: ₹ {total_amount:.2f}")

    # 15. മെഷിനറി & ഫ്യുവൽ ലോഗ്
    elif menu == "മെഷിനറി & ഫ്യുവൽ" and st.session_state["role"] == "Admin":
        st.subheader("🚜 മെഷീൻ ഫ്യുവൽ & സർവീസ് ട്രാക്കർ")
        with st.form("machinery_form"):
            mach_name = st.text_input("മെഷീന്റെ പേര്")
            fuel_cost = st.number_input("ചെലവ് (₹)", min_value=0.0, value=500.0)
            service_note = st.text_area("വിശദാംശങ്ങൾ")
            date = st.date_input("തീയതി", datetime.now())
            if st.form_submit_button("സേവ് ചെയ്യുക") and mach_name:
                ws = db.worksheet("machinery")
                ws.append_row([mach_name, fuel_cost, service_note, str(date)])
                log_activity(st.session_state['username'], "ADD_MACHINERY", f"Added machinery log for {mach_name}")
                st.success("സേവ് ചെയ്തു!")

    # 16. ചെലവ് കണക്കുകൾ
    elif menu == "ചെലവ് കണക്കുകൾ" and st.session_state["role"] == "Admin":
        st.subheader("💰 തോട്ടം ചെലവുകൾ രേഖപ്പെടുത്തുക")
        with st.form("expense_form"):
            category = st.selectbox("ചെലവ് ഇനം", ["വളം", "കൂലി", "മെഷിനറി", "മറ്റുള്ളവ"])
            amount = st.number_input("തുക (₹)", min_value=0.0, value=1000.0)
            description = st.text_area("വിശദാംശങ്ങൾ")
            date = st.date_input("തീയതി", datetime.now())
            if st.form_submit_button("ചെലവ് സേവ് ചെയ്യുക") and amount > 0:
                ws = db.worksheet("expenses")
                ws.append_row([category, amount, description, str(date)])
                log_activity(st.session_state['username'], "ADD_EXPENSE", f"Added expense {category}: Rs. {amount}")
                st.success("ചെലവ് സേവ് ചെയ്തു!")

    # 17. ലാഭ-നഷ്ടക്കണക്ക് (P&L)
    elif menu == "ലാഭ-നഷ്ടക്കണക്ക് (P&L)" and st.session_state["role"] == "Admin":
        st.subheader("📈 തോട്ടത്തിന്റെ ലാഭ-നഷ്ട വിശകലനം (P&L)")
        sales_df = get_data("sales")
        expenses_df = get_data("expenses")
        total_rev = sales_df['total_amount'].sum() if not sales_df.empty and 'total_amount' in sales_df.columns else 0.0
        total_exp = expenses_df['amount'].sum() if not expenses_df.empty and 'amount' in expenses_df.columns else 0.0
        net_profit = total_rev - total_exp
        col1, col2, col3 = st.columns(3)
        col1.metric("ആകെ വരുമാനം", f"₹ {total_rev:.2f}")
        col2.metric("ആകെ ചെലവ്", f"₹ {total_exp:.2f}")
        col3.metric("ശുദ്ധ ലാഭം", f"₹ {net_profit:.2f}")

    # 18. റിപ്പോർട്ടുകൾ
    elif menu == "റിപ്പോർട്ടുകൾ" and st.session_state["role"] == "Admin":
        st.subheader("📈 സമഗ്രമായ ഡാറ്റാ റിപ്പോർട്ടുകൾ")
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["ആക്ടിവിറ്റി ലോഗ്", "തൊഴിലാളികൾ", "മണ്ണുപരിശോധന", "എക്സ്പോർട്ട്", "വിളവെടുപ്പ്", "ഇൻവെന്ററി", "വിൽപ്പന", "മെഷിനറി", "ചെലവുകൾ"])
        with tab1:
            st.dataframe(get_data("activity_logs"))
        with tab2:
            st.dataframe(get_data("workers"))
        with tab3:
            st.dataframe(get_data("soil_tests"))
        with tab4:
            st.dataframe(get_data("exports"))
        with tab5:
            st.dataframe(get_data("yields"))
        with tab6:
            st.dataframe(get_data("inventory"))
        with tab7:
            st.dataframe(get_data("sales"))
        with tab8:
            st.dataframe(get_data("machinery"))
        with tab9:
            st.dataframe(get_data("expenses"))
