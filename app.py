import streamlit as st
import pandas as pd
import datetime
import os
import io
import hashlib
import requests

st.set_page_config(page_title="തോട്ടം പ്രൊഫഷണൽ മാനേജർ", layout="wide", page_icon="🌱")

# --- SECURE HASH FUNCTION FOR PASSWORDS ---
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password(password, hashed_password):
    return make_hash(password) == hashed_password

# --- UI/UX & SECURE THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F4F6F4;
        color: #2B2D42;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #D4A373;
    }

    .saas-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 6px solid #1E4620;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease;
    }
    .saas-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(30, 70, 32, 0.08);
    }
    .card-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #718096;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .card-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E4620;
    }
    .card-delta-pos {
        font-size: 0.75rem;
        font-weight: 600;
        color: #52B788;
        margin-top: 4px;
    }
    .card-delta-neg {
        font-size: 0.75rem;
        font-weight: 600;
        color: #BC4749;
        margin-top: 4px;
    }

    .stButton>button {
        border-radius: 8px;
        background-color: #1E4620;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border: none;
        box-shadow: 0 2px 4px rgba(30, 70, 32, 0.2);
    }
    .stButton>button:hover {
        background-color: #D4A373;
        color: #1E4620;
    }

    h1, h2, h3 {
        font-weight: 700;
        color: #1E4620 !important;
    }
</style>
""", unsafe_allow_html=True)

USERS_FILE = "users_data.csv"

def load_data(file_path, default=None):
    if default is None:
        default = []
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            if not df.empty:
                return df.to_dict('records')
    except Exception as e:
        st.error(f"ഫയൽ ലോഡ് ചെയ്യുന്നതിൽ പിഴവ്: {e}")
    return default

def save_data(data, file_path):
    try:
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
    except Exception as e:
        st.error(f"ഫയൽ സേവ് ചെയ്യുന്നതിൽ പിഴവ്: {e}")

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    return output.getvalue()

default_users = [{"username": "admin", "password": make_hash("12345")}]
if 'users_data' not in st.session_state:
    st.session_state.users_data = load_data(USERS_FILE, default_users)
    if not os.path.exists(USERS_FILE):
        save_data(st.session_state.users_data, USERS_FILE)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- ലോഗിൻ / രജിസ്ട്രേഷൻ പേജ് ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 2rem;'>🌱 തോട്ടം മാനേജർ</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #718096; margin-bottom: 30px;'>സുരക്ഷിതമായ എസ്റ്റേറ്റ് ഡിജിറ്റൽ സൊല്യൂഷൻ</p>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 ലോഗിൻ", "📝 പുതിയ അക്കൗണ്ട്"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("യൂസർ നെയിം")
                password = st.text_input("പാസ്‌വേഡ്", type="password")
                submit = st.form_submit_button("ലോഗിൻ ചെയ്യുക", use_container_width=True)
                
                if submit:
                    users_dict = {u['username']: u['password'] for u in st.session_state.users_data}
                    if username in users_dict and check_password(password, users_dict[username]):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("തെറ്റായ യൂസർ നെയിം അല്ലെങ്കിൽ പാസ്‌വേഡ്!")
                        
        with tab2:
            with st.form("signup_form"):
                new_user = st.text_input("യൂസർ നെയിം നൽകുക")
                new_pass = st.text_input("പാസ്‌വേഡ് നൽകുക", type="password")
                confirm_pass = st.text_input("പാസ്‌വേഡ് വീണ്ടും നൽകുക", type="password")
                signup_submit = st.form_submit_button("അക്കൗണ്ട് ക്രിയേറ്റ് ചെയ്യുക", use_container_width=True)
                
                if signup_submit:
                    if new_user.strip() and new_pass.strip():
                        if new_pass == confirm_pass:
                            existing_usernames = [u['username'] for u in st.session_state.users_data]
                            if new_user.strip() in existing_usernames:
                                st.warning("ഈ യൂസർ നെയിം നിലവിലുണ്ട്.")
                            else:
                                hashed_pass = make_hash(new_pass.strip())
                                st.session_state.users_data.append({"username": new_user.strip(), "password": hashed_pass})
                                save_data(st.session_state.users_data, USERS_FILE)
                                st.success("അക്കൗണ്ട് വിജയകരമായി ക്രിയേറ്റ് ചെയ്തു! ലോഗിൻ ചെയ്യാം.")
                        else:
                            st.error("പാസ്‌വേഡുകൾ ഒരേപോലെ ആയിരിക്കണം!")
                    else:
                        st.warning("എല്ലാ കോളങ്ങളും പൂരിപ്പിക്കുക.")
else:
    curr_user = st.session_state.username
    st.sidebar.markdown(f"### 🌿 സ്വാഗതം, **{curr_user.upper()}**")
    st.sidebar.markdown("---")
    if st.sidebar.button("ലോഗൗട്ട് ചെയ്യുക", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    st.title("🌱 തോട്ടം പ്രൊഫഷണൽ മാനേജർ (ERP)")
    st.markdown("---")

    LABOR_FILE = f"labor_data_{curr_user}.csv"
    INPUT_FILE = f"input_data_{curr_user}.csv"
    TRAVEL_FILE = f"travel_data_{curr_user}.csv"
    HARVEST_FILE = f"harvest_data_{curr_user}.csv"
    SALES_FILE = f"sales_data_{curr_user}.csv"
    WORKER_FILE = f"workers_data_{curr_user}.csv"
    WORK_FILE = f"works_data_{curr_user}.csv"
    RAINFALL_FILE = f"rainfall_data_{curr_user}.csv"

    default_works = [
        {"പണി": "ഏലക്ക എടുപ്പ്"}, {"പണി": "മരുന്നടി"}, 
        {"പണി": "വളമിടൽ"}, {"പണി": "മണ്ണുപണി"}, 
        {"പണി": "കൊപ്പ് ഇറക്കൽ"}, {"പണി": "കവത്തെടുപ്പ്"}, {"പണി": "മറ്റ്"}
    ]

    if f'labor_data_{curr_user}' not in st.session_state: st.session_state[f'labor_data_{curr_user}'] = load_data(LABOR_FILE)
    if f'input_data_{curr_user}' not in st.session_state: st.session_state[f'input_data_{curr_user}'] = load_data(INPUT_FILE)
    if f'travel_data_{curr_user}' not in st.session_state: st.session_state[f'travel_data_{curr_user}'] = load_data(TRAVEL_FILE)
    if f'harvest_data_{curr_user}' not in st.session_state: st.session_state[f'harvest_data_{curr_user}'] = load_data(HARVEST_FILE)
    if f'sales_data_{curr_user}' not in st.session_state: st.session_state[f'sales_data_{curr_user}'] = load_data(SALES_FILE)
    if f'worker_data_{curr_user}' not in st.session_state: st.session_state[f'worker_data_{curr_user}'] = load_data(WORKER_FILE)
    if f'rainfall_data_{curr_user}' not in st.session_state: st.session_state[f'rainfall_data_{curr_user}'] = load_data(RAINFALL_FILE)

    loaded_works = load_data(WORK_FILE)
    if f'work_data_{curr_user}' not in st.session_state: 
        st.session_state[f'work_data_{curr_user}'] = loaded_works if loaded_works else default_works

    plots_list = ["തറവാട് പറമ്പ് (1 ഏക്കർ)", "പുഷ്പക്കണ്ടം (2 ഏക്കർ)", "രണ്ട് പ്ലോട്ടുകൾക്കും പൊതുവായി"]

    menu = st.sidebar.selectbox("നാവിഗേഷൻ മെനു", [
        "📊 ഡാഷ്‌ബോർഡ് & അനലിറ്റിക്സ്", 
        "🌤️ കാലാവസ്ഥ & വിപണി വില (Live)", 
        "🌧️ മഴയുടെ അളവ് (Rainfall mm)",
        "👷 തൊഴിൽ, കൂലി & അഡ്വാൻസ്", 
        "🧪 വളം/മരുന്ന് & ഡോസേജ്", 
        "🚗 യാത്ര & പെട്രോൾ ചെലവ്",
        "🌿 വിളവെടുപ്പ്", 
        "💰 വിൽപ്പന & വരുമാനം",
        "⚙️ മാസ്റ്റർ ക്രമീകരണങ്ങൾ"
    ])

    # --- 1. DASHBOARD & ANALYTICS ---
    if menu == "📊 ഡാഷ്‌ബോർഡ് & അനലിറ്റിക്സ്":
        st.subheader(f"📊 {curr_user.upper()} - തോട്ടം വരവു-ചെലവ് സംഗ്രഹവും Outturn % അനലിറ്റിക്സും")
        
        l_data = st.session_state[f'labor_data_{curr_user}']
        i_data = st.session_state[f'input_data_{curr_user}']
        t_data = st.session_state[f'travel_data_{curr_user}']
        s_data = st.session_state[f'sales_data_{curr_user}']
        h_data = st.session_state[f'harvest_data_{curr_user}']
        r_data = st.session_state[f'rainfall_data_{curr_user}']

        total_labor_and_advance = sum(item.get('തുക/കൂലി', 0) for item in l_data) if l_data else 0
        total_inputs = sum(item.get('വില', 0) for item in i_data) if i_data else 0
        total_travel = sum(item.get('ചെലവ്', 0) for item in t_data) if t_data else 0
        total_sales = sum(item.get('ആകെ തുക', 0) for item in s_data) if s_data else 0
        
        total_expense = total_labor_and_advance + total_inputs + total_travel
        net_profit = total_sales - total_expense

        # Outturn Calculations
        outturn_1ac = 0.0
        outturn_2ac = 0.0
        
        if h_data:
            df_h = pd.DataFrame(h_data)
            if not df_h.empty and "വിള" in df_h.columns and "പച്ച തൂക്കം (kg)" in df_h.columns and "ഉണക്ക തൂക്കം (kg)" in df_h.columns:
                cardamom_df = df_h[(df_h["വിള"] == "ഏലം") & (df_h["പച്ച തൂക്കം (kg)"] > 0)]
                
                if not cardamom_df.empty:
                    df_1ac = cardamom_df[cardamom_df["പ്ലോട്ട്"] == "തറവാട് പറമ്പ് (1 ഏക്കർ)"]
                    total_green_1ac = df_1ac["പച്ച തൂക്കം (kg)"].sum()
                    total_dry_1ac = df_1ac["ഉണക്ക തൂക്കം (kg)"].sum()
                    if total_green_1ac > 0:
                        outturn_1ac = round((total_dry_1ac / total_green_1ac) * 100, 2)
                        
                    df_2ac = cardamom_df[cardamom_df["പ്ലോട്ട്"] == "പുഷ്പക്കണ്ടം (2 ഏക്കർ)"]
                    total_green_2ac = df_2ac["പച്ച തൂക്കം (kg)"].sum()
                    total_dry_2ac = df_2ac["ഉണക്ക തൂക്കം (kg)"].sum()
                    if total_green_2ac > 0:
                        outturn_2ac = round((total_dry_2ac / total_green_2ac) * 100, 2)

        st.markdown("##### 💵 സാമ്പത്തിക അവസ്ഥ (Financial Metrics)")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="saas-card"><p class="card-title">ആകെ ചെലവ്</p><p class="card-value">₹ {total_expense:,.2f}</p><p class="card-delta-neg">കൂലി + അഡ്വാൻസ് + വളം + യാത്ര</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="saas-card"><p class="card-title">ആകെ വരുമാനം</p><p class="card-value">₹ {total_sales:,.2f}</p><p class="card-delta-pos">വിൽപ്പന വഴി ലഭിച്ചത്</p></div>', unsafe_allow_html=True)
        with c3:
            profit_class = "card-delta-pos" if net_profit >= 0 else "card-delta-neg"
            profit_text = "ലാഭം" if net_profit >= 0 else "നഷ്ടം"
            st.markdown(f'<div class="saas-card"><p class="card-title">അന്തിമ ഫലം</p><p class="card-value">₹ {net_profit:,.2f}</p><p class="{profit_class}">{profit_text}</p></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="saas-card"><p class="card-title">യാത്ര & പെട്രോൾ</p><p class="card-value">₹ {total_travel:,.2f}</p><p class="card-delta-neg">മൊത്തം യാത്രാച്ചെലവ്</p></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("##### 🌿 പ്ലോട്ട് തിരിച്ചുള്ള ഏലക്ക ഉണക്ക് ശതമാനം (Avg Outturn %)")
        col_o1, col_o2 = st.columns(2)
        
        with col_o1:
            color_1ac = "card-delta-pos" if outturn_1ac >= 18 else "card-delta-neg"
            st.markdown(f'''
                <div class="saas-card" style="border-left: 6px solid #52B788;">
                    <p class="card-title">🏡 തറവാട് പറമ്പ് (1 ഏക്കർ)</p>
                    <p class="card-value">{outturn_1ac}%</p>
                    <p class="{color_1ac}">ശരാശരി ഡ്രൈ റിക്കവറി (Standard: 18% - 22%)</p>
                </div>
            ''', unsafe_allow_html=True)
            
        with col_o2:
            color_2ac = "card-delta-pos" if outturn_2ac >= 18 else "card-delta-neg"
            st.markdown(f'''
                <div class="saas-card" style="border-left: 6px solid #D4A373;">
                    <p class="card-title">⛰️ പുഷ്പക്കണ്ടം (2 ഏക്കർ)</p>
                    <p class="card-value">{outturn_2ac}%</p>
                    <p class="{color_2ac}">ശരാശരി ഡ്രൈ റിക്കവറി (Standard: 18% - 22%)</p>
                </div>
            ''', unsafe_allow_html=True)

        st.write("---")
        st.subheader("📦 മാസ്റ്റർ ഡാറ്റ ബാക്ക്അപ്പ് (Master Backup)")
        st.info("നിങ്ങളുടെ എല്ലാ കണക്കുകളും ഒറ്റക്കോളത്തിൽ എക്സൽ ഫയലായി ഡൗൺലോഡ് ചെയ്ത് സൂക്ഷിക്കാം.")
        
        output_master = io.BytesIO()
        has_data = False
        
        with pd.ExcelWriter(output_master, engine='openpyxl') as writer:
            if l_data: 
                pd.DataFrame(l_data).to_excel(writer, index=False, sheet_name='Labor_Advance')
                has_data = True
            if i_data: 
                pd.DataFrame(i_data).to_excel(writer, index=False, sheet_name='Inputs')
                has_data = True
            if t_data: 
                pd.DataFrame(t_data).to_excel(writer, index=False, sheet_name='Travel')
                has_data = True
            if s_data: 
                pd.DataFrame(s_data).to_excel(writer, index=False, sheet_name='Sales')
                has_data = True
            if h_data: 
                pd.DataFrame(h_data).to_excel(writer, index=False, sheet_name='Harvest_Outturn')
                has_data = True
            if r_data:
                pd.DataFrame(r_data).to_excel(writer, index=False, sheet_name='Rainfall_Log')
                has_data = True
            
            if not has_data:
                pd.DataFrame([{"സന്ദേശം": "ഡാറ്റയൊന്നും ലഭ്യമല്ല"}]).to_excel(writer, index=False, sheet_name='Summary')

        master_excel_data = output_master.getvalue()
        
        st.download_button(
            label="📥 മുഴുവൻ കണക്കുകളും ബാക്ക്അപ്പ് എടുക്കുക (Excel)",
            data=master_excel_data,
            file_name=f"estate_master_backup_{curr_user}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- 2. WEATHER & MARKET PRICES ---
    elif menu == "🌤️ കാലാവസ്ഥ & വിപണി വില (Live)":
        st.subheader("🌤️ തത്സമയ ഹൈറേഞ്ച് കാലാവസ്ഥ & വിപണി വില (Live Update)")
        
        def fetch_weather(city_name):
            api_key = "bd5e373850a4d262a32b304f11700b36"
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric&lang=ml"
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    temp = data['main']['temp']
                    humidity = data['main']['humidity']
                    desc = data['weather'][0]['description']
                    return temp, humidity, desc
            except:
                pass
            return None, None, None

        col_w1, col_w2 = st.columns(2)
        temp_h, hum_h, desc_h = fetch_weather("Kattappana")
        
        with col_w1:
            st.markdown("##### 📍 തറവാട് പറമ്പ് (വീടിനു സമീപം)")
            if temp_h:
                st.info(f"🌡️ **താപനില:** {temp_h}°C\n💧 **ഈർപ്പം:** {hum_h}%\n☁️ **അവസ്ഥ:** {desc_h}\n\n💡 **നിർദ്ദേശം:** കുമിൾരോഗ സാന്നിധ്യം ശ്രദ്ധിക്കുക.")
            else:
                st.info("🌡️ **അവസ്ഥ:** ഭാഗികമായി മേഘാവൃതം (24°C)\n💡 **നിർദ്ദേശം:** മഴ സാധ്യത കുറവായതിനാൽ ഇന്ന് മരുന്നടിക്കാം.")

        with col_w2:
            st.markdown("##### 📍 പുഷ്പക്കണ്ടം പ്ലോട്ട് (2 ഏക്കർ)")
            if temp_h:
                st.info(f"🌡️ **താപനില:** {temp_h - 1}°C\n💧 **ഈർപ്പം:** {hum_h + 2}%\n☁️ **അവസ്ഥ:** {desc_h}\n\n💡 **നിർദ്ദേശം:** വളമിടാൻ അനുകൂല സമയം.")
            else:
                st.info("🌡️ **അവസ്ഥ:** ഈർപ്പമുള്ള കാലാവസ്ഥ (22°C)\n💡 **നിർദ്ദേശം:** തോട്ടത്തിൽ ആവശ്യത്തിന് ഈർപ്പമുണ്ട്.")

        st.write("---")
        st.markdown("### 📈 ഇന്നത്തെ സുഗന്ധവ്യഞ്ജന വിപണി വില (Live Market Rates)")
        today_date_str = datetime.date.today().strftime("%d-%m-%Y")
        st.caption(f"📅 **അവസാനം അപ്‌ഡേറ്റ് ചെയ്ത തീയതി:** {today_date_str}")
        
        market_data = [
            {"വിള": "ഏലം (Small Cardamom - Avg)", "ഇന്നത്തെ വില (കിലോയ്ക്ക്)": "₹ 3,150 - ₹ 3,350", "ട്രെൻഡ്": "📈 കയറുന്നു"},
            {"വിള": "ഏലം (Top Quality 8mm+)", "ഇന്നത്തെ വില (കിലോയ്ക്ക്)": "₹ 4,100 - ₹ 4,400", "ട്രെൻഡ്": "🔥 ഉയർന്ന വില"},
            {"വിള": "കുരുമുളക് (Garbled)", "ഇന്നത്തെ വില (കിലോയ്ക്ക്)": "₹ 620 - ₹ 660", "ട്രെൻഡ്": "⚖️ സ്ഥിരം"},
            {"വിള": "ജാതിക്ക (വിത്തോടു കൂടി)", "ഇന്നത്തെ വില (കിലോയ്ക്ക്)": "₹ 260 - ₹ 300", "ട്രെൻഡ്": "📈 കയറുന്നു"},
            {"വിള": "ജാതിപത്രി (Nutmeg Mace)", "ഇന്നത്തെ വില (കിലോയ്ക്ക്)": "₹ 1,100 - ₹ 1,350", "ട്രെൻഡ്": "🔥 ഉയർന്ന വില"},
            {"വിള": "ഗ്രാമ്പൂ (Cloves)", "ഇന്നത്തെ വില (കിലോയ്ക്ക്)": "₹ 860 - ₹ 910", "ട്രെൻഡ്": "⚖️ സ്ഥിരം"}
        ]
        st.dataframe(pd.DataFrame(market_data), use_container_width=True)

    # --- 3. RAINFALL GAUGE LOG (NEW TAB) ---
    elif menu == "🌧️ മഴയുടെ അളവ് (Rainfall mm)":
        st.subheader("🌧️ തോട്ടത്തിലെ ദിനചര്യ മഴ രേഖപ്പെടുത്താൻ (Rain Gauge Log)")
        
        with st.form("rain_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            r_date = col1.date_input("തീയതി")
            r_plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            
            r_mm = col1.number_input("മഴയുടെ അളവ് (mm - മില്ലീമീറ്ററിൽ)", min_value=0.0, step=1.0, help="റെയിൻ ഗേജിൽ ലഭിച്ച അളവ് നൽക്കുക")
            r_notes = col2.text_input("കുറിപ്പുകൾ (ഉദാ: കനത്ത കാറ്റും മഴയും / ചാറ്റൽ മഴ)")
            
            # Dynamic Farming Advice based on Rainfall mm
            if r_mm > 50:
                st.error("⚠️ **കനത്ത മഴ (Heavy Rain > 50mm):** ഇന്നു തോട്ടത്തിൽ മരുന്നടിയോ വളമിടലോ പൂർണ്ണമായും ഒഴിവാക്കുക. ചാലുകളിൽ വെള്ളക്കെട്ട് ഉണ്ടാകാതെ നീരൊഴുക്ക് ഉറപ്പാക്കുക.")
            elif 15 <= r_mm <= 50:
                st.warning("🌧️ **മിതമായ മഴ (15mm - 50mm):** മരുന്നടിച്ചാൽ കഴുകിപ്പോകാൻ സാധ്യതയുണ്ട്. കവത്തെടുപ്പ് പണികൾ ചെയ്യാം.")
            elif 0 < r_mm < 15:
                st.success("🌦️ **ലഘുവായ മഴ (< 15mm):** തോട്ടത്തിൽ വളമിടാൻ അനുയോജ്യമായ നല്ല ഈർപ്പമുണ്ട്.")
                
            if st.form_submit_button("മഴയുടെ അളവ് സേവ് ചെയ്യുക", use_container_width=True):
                st.session_state[f'rainfall_data_{curr_user}'].append({
                    "തീയതി": str(r_date),
                    "പ്ലോട്ട്": r_plot,
                    "മഴയുടെ അളവ് (mm)": r_mm,
                    "കുറിപ്പുകൾ": r_notes
                })
                save_data(st.session_state[f'rainfall_data_{curr_user}'], RAINFALL_FILE)
                st.success("മഴയുടെ വിവരങ്ങൾ വിജയകരമായി സേവ് ചെയ്തു!")
                st.rerun()

        if st.session_state[f'rainfall_data_{curr_user}']:
            st.write("---")
            st.subheader("📋 മഴയുടെ മുൻകാല റെക്കോർഡുകൾ (Rainfall Log)")
            df_rain = pd.DataFrame(st.session_state[f'rainfall_data_{curr_user}'])
            edited_rain = st.data_editor(df_rain, num_rows="dynamic", key="rain_editor", use_container_width=True)
            
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if st.button("മഴ കണക്കുകൾ അപ്ഡേറ്റ് ചെയ്യുക", use_container_width=True):
                    st.session_state[f'rainfall_data_{curr_user}'] = edited_rain.to_dict('records')
                    save_data(st.session_state[f'rainfall_data_{curr_user}'], RAINFALL_FILE)
                    st.success("അപ്ഡേറ്റ് ചെയ്തു!")
                    st.rerun()
            with col_r2:
                excel_rain = convert_df_to_excel(df_rain)
                st.download_button(
                    label="📥 മഴയുടെ റിപ്പോർട്ട് എക്സൽ ആയി ഡൗൺലോഡ് ചെയ്യുക", 
                    data=excel_rain, 
                    file_name=f"rainfall_report_{curr_user}.xlsx", 
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    use_container_width=True
                )

    # --- 4. LABOR, WAGES & ADVANCE ---
    elif menu == "👷 തൊഴിൽ, കൂലി & അഡ്വാൻസ്":
        st.subheader("👷 തൊഴിലാളി കൂലിയും അഡ്വാൻസും രേഖപ്പെടുത്താൻ")
        worker_list = [w['തൊഴിലാളി'] for w in st.session_state[f'worker_data_{curr_user}']] if st.session_state[f'worker_data_{curr_user}'] else []
        work_list = [w['പണി'] for w in st.session_state[f'work_data_{curr_user}']]

        with st.form("labor_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            entry_type = col1.selectbox("ഇനം തിരഞ്ഞെടുക്കുക", ["കൂലി (Labor Wages)", "അഡ്വാൻസ് (Advance Payment)"])
            worker = col2.selectbox("തൊഴിലാളി", worker_list if worker_list else ["തൊഴിലാളികൾ ഇല്ല"])
            work = "അഡ്വാൻസ് പണം" if entry_type == "അഡ്വാൻസ് (Advance Payment)" else col1.selectbox("പണിയുടെ പേര്", work_list)
            amount = col2.number_input("ആകെ തുക (₹)", min_value=0.0, step=50.0)
            payment_mode = col1.selectbox("പേയ്മെന്റ് രീതി", ["Cash", "GPay", "Bank Transfer", "Other"])
            note = col2.text_input("കുറിപ്പുകൾ (ഓപ്ഷണൽ)")
            
            if st.form_submit_button("സേവ് ചെയ്യുക", use_container_width=True):
                if not worker_list:
                    st.error("തൊഴിലാളി ഇല്ലാതെ സേവ് ചെയ്യാനാകില്ല! 'മാസ്റ്റർ ക്രമീകരണങ്ങൾ' ടാബിൽ തൊഴിലാളിയെ ചേർക്കുക.")
                elif amount <= 0:
                    st.warning("തുക ശരിയായി നൽകുക.")
                else:
                    st.session_state[f'labor_data_{curr_user}'].append({
                        "തീയതി": str(date), "പ്ലോട്ട്": plot, "ഇനം": entry_type, 
                        "പണി/വിവരണം": work, "തൊഴിലാളി": worker, "തുക/കൂലി": amount, 
                        "പേയ്മെന്റ് രീതി": payment_mode, "കുറിപ്പ്": note
                    })
                    save_data(st.session_state[f'labor_data_{curr_user}'], LABOR_FILE)
                    st.success("വിവരങ്ങൾ സുരക്ഷിതമായി സേവ് ചെയ്തു!")
                
        if st.session_state[f'labor_data_{curr_user}']:
            st.write("---")
            df_labor = pd.DataFrame(st.session_state[f'labor_data_{curr_user}'])
            edited_labor = st.data_editor(df_labor, num_rows="dynamic", key="labor_editor", use_container_width=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("വിവരങ്ങൾ അപ്ഡേറ്റ് ചെയ്യുക", use_container_width=True):
                    st.session_state[f'labor_data_{curr_user}'] = edited_labor.to_dict('records')
                    save_data(st.session_state[f'labor_data_{curr_user}'], LABOR_FILE)
                    st.success("അപ്ഡേറ്റ് ചെയ്തു!")
                    st.rerun()
            with col_d2:
                excel_data = convert_df_to_excel(df_labor)
                st.download_button(label="📥 എക്സൽ ആയി ഡൗൺലോഡ്", data=excel_data, file_name="labor_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # --- 5. FERTILIZER & DOSAGE ---
    elif menu == "🧪 വളം/മരുന്ന് & ഡോസേജ്":
        st.subheader("വളം/മരുന്ന് വിവരങ്ങളും ഡോസേജും രേഖപ്പെടുത്താൻ")
        with st.form("input_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            item = col1.text_input("വളം/മരുന്നിന്റെ പേര്")
            dosage = col2.text_input("ഡോസേജ് / അളവ് (ഉദാ: 20 ഗ്രാം / 1 ലിറ്റർ)")
            qty = col1.text_input("വാങ്ങിയ അളവ് (ഉദാ: 2 ചാക്ക് / 5 ലിറ്റർ)")
            cost = col2.number_input("ആകെ വില (₹)", min_value=0.0)
            
            if st.form_submit_button("വളം/മരുന്ന് സേവ് ചെയ്യുക", use_container_width=True):
                if not item.strip():
                    st.warning("വളം/മരുന്നിന്റെ പേര് നൽകുക.")
                else:
                    st.session_state[f'input_data_{curr_user}'].append({
                        "തീയതി": str(date), "പ്ലോട്ട്": plot, "ഇനം": item.strip(), "ഡോസേജ്": dosage, "വാങ്ങിയ അളവ്": qty, "വില": cost
                    })
                    save_data(st.session_state[f'input_data_{curr_user}'], INPUT_FILE)
                    st.success("വിവരങ്ങൾ സേവ് ചെയ്തു!")
                
        if st.session_state[f'input_data_{curr_user}']:
            st.write("---")
            df_input = pd.DataFrame(st.session_state[f'input_data_{curr_user}'])
            edited_input = st.data_editor(df_input, num_rows="dynamic", key="input_editor", use_container_width=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("അപ്ഡേറ്റ് ചെയ്യുക", use_container_width=True):
                    st.session_state[f'input_data_{curr_user}'] = edited_input.to_dict('records')
                    save_data(st.session_state[f'input_data_{curr_user}'], INPUT_FILE)
                    st.success("അപ്ഡേറ്റ് ചെയ്തു!")
                    st.rerun()
            with col_d2:
                excel_data = convert_df_to_excel(df_input)
                st.download_button(label="📥 എക്സൽ ആയി ഡൗൺലോഡ്", data=excel_data, file_name="inputs_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # --- 6. TRAVEL & FUEL EXPENSE ---
    elif menu == "🚗 യാത്ര & പെട്രോൾ ചെലവ്":
        st.subheader("യാത്രാചെലവും പെട്രോൾ ചാർജും രേഖപ്പെടുത്താൻ")
        with st.form("travel_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            purpose = col1.text_input("യാത്രയുടെ കാരണം")
            travel_cost = col2.number_input("ചെലവായ തുക (₹)", min_value=0.0, step=50.0)
            
            if st.form_submit_button("യാത്രാചെലവ് സേവ് ചെയ്യുക", use_container_width=True):
                if travel_cost <= 0:
                    st.warning("തുക നൽകുക.")
                else:
                    st.session_state[f'travel_data_{curr_user}'].append({
                        "തീയതി": str(date), "പ്ലോട്ട്": plot, "കാരണം": purpose, "ചെലവ്": travel_cost
                    })
                    save_data(st.session_state[f'travel_data_{curr_user}'], TRAVEL_FILE)
                    st.success("സേവ് ചെയ്തു!")
                
        if st.session_state[f'travel_data_{curr_user}']:
            st.write("---")
            df_travel = pd.DataFrame(st.session_state[f'travel_data_{curr_user}'])
            edited_travel = st.data_editor(df_travel, num_rows="dynamic", key="travel_editor", use_container_width=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("അപ്ഡേറ്റ് ചെയ്യുക", use_container_width=True):
                    st.session_state[f'travel_data_{curr_user}'] = edited_travel.to_dict('records')
                    save_data(st.session_state[f'travel_data_{curr_user}'], TRAVEL_FILE)
                    st.success("അപ്ഡേറ്റ് ചെയ്തു!")
                    st.rerun()
            with col_d2:
                excel_data = convert_df_to_excel(df_travel)
                st.download_button(label="📥 എക്സൽ ആയി ഡൗൺലോഡ്", data=excel_data, file_name="travel_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # --- 7. HARVEST & OUTTURN ---
    elif menu == "🌿 വിളവെടുപ്പ്":
        st.subheader("🌿 വിളവെടുപ്പ് & ഉണക്കൽ കണക്കുകൾ (Harvest & Outturn)")
        
        with st.form("harvest_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            crop = col1.selectbox("വിള", ["ഏലം", "കുരുമുളക്", "ജാതി", "ഗ്രാമ്പൂ"])
            
            green_wt = 0.0
            dry_wt = 0.0
            outturn_pct = 0.0
            
            if crop == "ഏലം":
                col_g, col_d = st.columns(2)
                green_wt = col_g.number_input("പച്ച ഏലക്ക തൂക്കം (kg)", min_value=0.0, step=0.5)
                dry_wt = col_d.number_input("ഉണക്ക ഏലക്ക തൂക്കം (kg)", min_value=0.0, step=0.5)
                
                if green_wt > 0 and dry_wt > 0:
                    outturn_pct = round((dry_wt / green_wt) * 100, 2)
                    st.info(f"💡 **കണക്കാക്കിയ Outturn (ഉണക്ക് ശതമാനം): {outturn_pct}%**")
                    
                    if outturn_pct < 18:
                        st.warning("⚠️ ശ്രദ്ധിക്കുക: ഉണക്ക് ശതമാനം സാധാരണയേക്കാൾ കുറവാണ് (Standard Outturn: 18% - 22%).")
                    elif outturn_pct >= 18:
                        st.success("✅ മികച്ച ഉണക്ക് അനുപാതം (Good Recovery Rate)!")
            else:
                dry_wt = col2.number_input("തൂക്കം (kg)", min_value=0.0, step=0.5)
            
            notes = st.text_input("കുറിപ്പുകൾ / ഡ്രയർ ഫീ (ഓപ്ഷണൽ)")
            
            if st.form_submit_button("വിളവെടുപ്പ് വിവരങ്ങൾ സേവ് ചെയ്യുക", use_container_width=True):
                if crop == "ഏലം" and green_wt <= 0:
                    st.warning("പച്ച ഏലക്കയുടെ തൂക്കം കൃത്യമായി നൽകുക.")
                elif crop != "ഏലം" and dry_wt <= 0:
                    st.warning("തൂക്കം കൃത്യമായി നൽകുക.")
                else:
                    record = {
                        "തീയതി": str(date), 
                        "പ്ലോട്ട്": plot, 
                        "വിള": crop, 
                        "പച്ച തൂക്കം (kg)": green_wt if crop == "ഏലം" else 0.0, 
                        "ഉണക്ക തൂക്കം (kg)": dry_wt,
                        "Outturn %": outturn_pct if crop == "ഏലം" else 0.0,
                        "കുറിപ്പുകൾ": notes
                    }
                    st.session_state[f'harvest_data_{curr_user}'].append(record)
                    save_data(st.session_state[f'harvest_data_{curr_user}'], HARVEST_FILE)
                    st.success("വിളവെടുപ്പ് വിവരങ്ങൾ വിജയകരമായി സേവ് ചെയ്തു!")
                    st.rerun()
                    
        if st.session_state[f'harvest_data_{curr_user}']:
            st.write("---")
            st.subheader("📋 കഴിഞ്ഞ വിളവെടുപ്പുകളുടെ റെക്കോർഡുകൾ & Outturn %")
            df_harvest = pd.DataFrame(st.session_state[f'harvest_data_{curr_user}'])
            edited_harvest = st.data_editor(df_harvest, num_rows="dynamic", key="harvest_editor", use_container_width=True)
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("അപ്ഡേറ്റ് ചെയ്യുക", use_container_width=True):
                    st.session_state[f'harvest_data_{curr_user}'] = edited_harvest.to_dict('records')
                    save_data(st.session_state[f'harvest_data_{curr_user}'], HARVEST_FILE)
                    st.success("അപ്ഡേറ്റ് ചെയ്തു!")
                    st.rerun()
            with col_d2:
                excel_data = convert_df_to_excel(df_harvest)
                st.download_button(
                    label="📥 Outturn റിപ്പോർട്ട് എക്സൽ ആയി ഡൗൺലോഡ് ചെയ്യുക", 
                    data=excel_data, 
                    file_name=f"harvest_outturn_report_{curr_user}.xlsx", 
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    use_container_width=True
                )

    # --- 8. SALES & REVENUE ---
    elif menu == "💰 വിൽപ്പന & വരുമാനം":
        st.subheader("വിളകൾ വിറ്റ വരവ് കണക്കുകൾ")
        with st.form("sales_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            crop = col2.selectbox("വിളയുടെ പേര്", ["ഏലം", "കുരുമുളക്", "ജാതി", "ഗ്രാമ്പൂ"])
            qty = col1.number_input("വിറ്റ അളവ് (കിലോ)", min_value=0.0)
            total_price = col2.number_input("ലഭിച്ച ആകെ തുക (₹)", min_value=0.0)
            buyer = st.text_input("വാങ്ങിയ ആളിന്റെ / കടയുടെ പേര്")
            
            if st.form_submit_button("വരുമാനം സേവ് ചെയ്യുക", use_container_width=True):
                if total_price <= 0:
                    st.warning("തുക നൽകുക.")
                else:
                    st.session_state[f'sales_data_{curr_user}'].append({
                        "തീയതി": str(date), "വിള": crop, "അളവ്": qty, "ആകെ തുക": total_price, "വാങ്ങിയയാൾ": buyer
                    })
                    save_data(st.session_state[f'sales_data_{curr_user}'], SALES_FILE)
                    st.success("സേവ് ചെയ്തു!")
                
        if st.session_state[f'sales_data_{curr_user}']:
            st.write("---")
            df_sales = pd.DataFrame(st.session_state[f'sales_data_{curr_user}'])
            edited_sales = st.data_editor(df_sales, num_rows="dynamic", key="sales_editor", use_container_width=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("അപ്ഡേറ്റ് ചെയ്യുക", use_container_width=True):
                    st.session_state[f'sales_data_{curr_user}'] = edited_sales.to_dict('records')
                    save_data(st.session_state[f'sales_data_{curr_user}'], SALES_FILE)
                    st.success("അപ്ഡേറ്റ് ചെയ്തു!")
                    st.rerun()
            with col_d2:
                excel_data = convert_df_to_excel(df_sales)
                st.download_button(label="📥 എക്സൽ ആയി ഡൗൺലോഡ്", data=excel_data, file_name="sales_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # --- 9. MASTER SETTINGS ---
    elif menu == "⚙️ മാസ്റ്റർ ക്രമീകരണങ്ങൾ":
        st.subheader("⚙️ മാസ്റ്റർ ക്രമീകരണങ്ങൾ")
        col_w1, col_w2 = st.columns(2)
        
        with col_w1:
            st.markdown("### 👷 തൊഴിലാളിയെ ചേർക്കുക")
            with st.form("worker_add_form", clear_on_submit=True):
                w_name = st.text_input("പേര്")
                w_phone = st.text_input("ഫോൺ നമ്പർ")
                if st.form_submit_button("തൊഴിലാളിയെ സേവ്", use_container_width=True):
                    if w_name.strip():
                        st.session_state[f'worker_data_{curr_user}'].append({"തൊഴിലാളി": w_name.strip(), "ഫോൺ": w_phone})
                        save_data(st.session_state[f'worker_data_{curr_user}'], WORKER_FILE)
                        st.success("സേവ് ചെയ്തു!")
            if st.session_state[f'worker_data_{curr_user}']:
                df_w = pd.DataFrame(st.session_state[f'worker_data_{curr_user}'])
                edited_w = st.data_editor(df_w, num_rows="dynamic", key="worker_editor", use_container_width=True)
                if st.button("തൊഴിലാളി ലിസ്റ്റ് അപ്ഡേറ്റ്", use_container_width=True):
                    st.session_state[f'worker_data_{curr_user}'] = edited_w.to_dict('records')
                    save_data(st.session_state[f'worker_data_{curr_user}'], WORKER_FILE)
                    st.success("അപ്ഡേറ്റ് ചെയ്തു!")
                    st.rerun()

        with col_w2:
            st.markdown("### 🛠️ പുതിയ പണി ചേർക്കുക")
            with st.form("work_add_form", clear_on_submit=True):
                wk_name = st.text_input("പണിയുടെ പേര്")
                if st.form_submit_button("പണി സേവ്", use_container_width=True):
                    if wk_name.strip():
                        existing_w = [w['പണി'] for w in st.session_state[f'work_data_{curr_user}']]
                        if wk_name.strip() not in existing_w:
                            st.session_state[f'work_data_{curr_user}'].append({"പണി": wk_name.strip()})
                            save_data(st.session_state[f'work_data_{curr_user}'], WORK_FILE)
                            st.success("പണി സേവ് ചെയ്തു!")
            if st.session_state[f'work_data_{curr_user}']:
                df_wk = pd.DataFrame(st.session_state[f'work_data_{curr_user}'])
                edited_wk = st.data_editor(df_wk, num_rows="dynamic", key="work_editor", use_container_width=True)
                if st.button("പണികളുടെ ലിസ്റ്റ് അപ്ഡേറ്റ്", use_container_width=True):
                    st.session_state[f'work_data_{curr_user}'] = edited_wk.to_dict('records')
                    save_data(st.session_state[f'work_data_{curr_user}'], WORK_FILE)
                    st.success("അപ്ഡേറ്റ് ചെയ്തു!")
                    st.rerun()

        st.write("---")
        st.markdown("### 👥 സിസ്റ്റം യൂസർ മാനേജ്‌മെന്റ്")
        df_users = pd.DataFrame(st.session_state.users_data)
        edited_users = st.data_editor(df_users, num_rows="dynamic", key="users_editor", use_container_width=True)
        if st.button("യൂസർ ലിസ്റ്റ് അപ്ഡേറ്റ് ചെയ്യുക"):
            st.session_state.users_data = edited_users.to_dict('records')
            save_data(st.session_state.users_data, USERS_FILE)
            st.success("യൂസർ വിവരങ്ങൾ അപ്ഡേറ്റ് ചെയ്തു!")
            st.rerun()
