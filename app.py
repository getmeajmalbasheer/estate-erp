import streamlit as st
import pandas as pd
import datetime
import io
import sqlite3
import bcrypt
import requests

st.set_page_config(page_title="തോട്ടം പ്രൊഫഷണൽ മാനേജർ", layout="wide", page_icon="🌱")

# --- 1. DATABASE SETUP (SQLite) ---
def get_db_connection():
    conn = sqlite3.connect('estate_data.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    # Rainfall Table
    c.execute('''CREATE TABLE IF NOT EXISTS rainfall 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date TEXT, plot TEXT, mm REAL, notes TEXT)''')
    # Labor Table
    c.execute('''CREATE TABLE IF NOT EXISTS labor 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date TEXT, plot TEXT, category TEXT, work TEXT, worker TEXT, amount REAL, status TEXT, mode TEXT, note TEXT)''')
    # Inputs Table
    c.execute('''CREATE TABLE IF NOT EXISTS inputs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date TEXT, plot TEXT, item TEXT, dosage TEXT, qty TEXT, cost REAL)''')
    # Travel Table
    c.execute('''CREATE TABLE IF NOT EXISTS travel 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date TEXT, plot TEXT, purpose TEXT, cost REAL)''')
    # Harvest Table
    c.execute('''CREATE TABLE IF NOT EXISTS harvest 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date TEXT, plot TEXT, crop TEXT, green_wt REAL, dry_wt REAL, outturn REAL, notes TEXT)''')
    # Sales Table
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date TEXT, crop TEXT, qty REAL, total REAL, buyer TEXT)''')
    # Workers Master
    c.execute('''CREATE TABLE IF NOT EXISTS workers_master 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, name TEXT, phone TEXT)''')
    # Works Master
    c.execute('''CREATE TABLE IF NOT EXISTS works_master 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, name TEXT)''')
    
    # Default Admin User Setup
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        admin_pass = bcrypt.hashpw("12345".encode(), bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users VALUES ('admin', ?, 'admin')", (admin_pass,))
    
    conn.commit()
    conn.close()

init_db()

# --- SECURE HASH FUNCTIONS ---
def make_hash(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# --- UI STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F4F6F4; color: #2B2D42; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #D4A373; }
    .saas-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 6px solid #1E4620; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.04); }
    .card-title { font-size: 0.85rem; font-weight: 600; color: #718096; margin-bottom: 6px; text-transform: uppercase; }
    .card-value { font-size: 1.8rem; font-weight: 700; color: #1E4620; }
    .card-delta-pos { font-size: 0.75rem; font-weight: 600; color: #52B788; }
    .card-delta-neg { font-size: 0.75rem; font-weight: 600; color: #BC4749; }
    .stButton>button { border-radius: 8px; background-color: #1E4620; color: white; font-weight: 600; border: none; }
    .stButton>button:hover { background-color: #D4A373; color: #1E4620; }
    h1, h2, h3 { font-weight: 700; color: #1E4620 !important; }
</style>
""", unsafe_allow_html=True)

# Helper function to convert DataFrames to Excel
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    return output.getvalue()

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = "user"

# --- LOGIN / REGISTRATION PAGE ---
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
                    conn = get_db_connection()
                    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
                    conn.close()
                    
                    if user and check_password(password, user['password']):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = user['role']
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
                            conn = get_db_connection()
                            existing = conn.execute("SELECT * FROM users WHERE username = ?", (new_user.strip(),)).fetchone()
                            if existing:
                                st.warning("ഈ യൂസർ നെയിം നിലവിലുണ്ട്.")
                            else:
                                hashed_pass = make_hash(new_pass.strip())
                                conn.execute("INSERT INTO users VALUES (?, ?, 'user')", (new_user.strip(), hashed_pass))
                                conn.commit()
                                st.success("അക്കൗണ്ട് വിജയകരമായി ക്രിയേറ്റ് ചെയ്തു! ലോഗിൻ ചെയ്യാം.")
                            conn.close()
                        else:
                            st.error("പാസ്‌വേഡുകൾ ഒരേപോലെ ആയിരിക്കണം!")
                    else:
                        st.warning("എല്ലാ കോളങ്ങളും പൂരിപ്പിക്കുക.")

else:
    curr_user = st.session_state.username
    st.sidebar.markdown(f"### 🌿 സ്വാഗതം, **{curr_user.upper()}**")
    st.sidebar.markdown(f"👤 റോൾ: `{st.session_state.role.upper()}`")
    st.sidebar.markdown("---")
    if st.sidebar.button("ലോഗൗട്ട് ചെയ്യുക", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = "user"
        st.rerun()
        
    st.title("🌱 തോട്ടം പ്രൊഫഷണൽ മാനേജർ (ERP)")
    st.markdown("---")

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

    conn = get_db_connection()

    # --- 1. DASHBOARD & ANALYTICS ---
    if menu == "📊 ഡാഷ്‌ബോർഡ് & അനലിറ്റിക്സ്":
        st.subheader(f"📊 {curr_user.upper()} - വരവു-ചെലവ് സംഗ്രഹവും അനലിറ്റിക്സും")
        
        df_l = pd.read_sql_query("SELECT * FROM labor WHERE user=?", conn, params=(curr_user,))
        df_i = pd.read_sql_query("SELECT * FROM inputs WHERE user=?", conn, params=(curr_user,))
        df_t = pd.read_sql_query("SELECT * FROM travel WHERE user=?", conn, params=(curr_user,))
        df_s = pd.read_sql_query("SELECT * FROM sales WHERE user=?", conn, params=(curr_user,))
        df_h = pd.read_sql_query("SELECT * FROM harvest WHERE user=?", conn, params=(curr_user,))
        df_r = pd.read_sql_query("SELECT * FROM rainfall WHERE user=?", conn, params=(curr_user,))

        total_labor = df_l['amount'].sum() if not df_l.empty else 0.0
        total_inputs = df_i['cost'].sum() if not df_i.empty else 0.0
        total_travel = df_t['cost'].sum() if not df_t.empty else 0.0
        total_sales = df_s['total'].sum() if not df_s.empty else 0.0
        
        total_expense = total_labor + total_inputs + total_travel
        net_profit = total_sales - total_expense

        st.markdown("##### 💵 സാമ്പത്തിക അവസ്ഥ (Financial Metrics)")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="saas-card"><p class="card-title">ആകെ ചെലവ്</p><p class="card-value">₹ {total_expense:,.2f}</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="saas-card"><p class="card-title">ആകെ വരുമാനം</p><p class="card-value">₹ {total_sales:,.2f}</p></div>', unsafe_allow_html=True)
        
        profit_class = "card-delta-pos" if net_profit >= 0 else "card-delta-neg"
        c3.markdown(f'<div class="saas-card"><p class="card-title">അന്തിമ ഫലം</p><p class="card-value">₹ {net_profit:,.2f}</p><p class="{profit_class}">{"ലാഭം" if net_profit >= 0 else "നഷ്ടം"}</p></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="saas-card"><p class="card-title">യാത്ര & പെട്രോൾ</p><p class="card-value">₹ {total_travel:,.2f}</p></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts Section
        if not df_r.empty:
            st.markdown("##### 🌧️ മഴയുടെ അളവ് (Rainfall Graph)")
            st.line_chart(df_r.set_index("date")["mm"])

        st.write("---")
        st.subheader("📦 മാസ്റ്റർ ഡാറ്റ ബാക്ക്അപ്പ്")
        output_master = io.BytesIO()
        with pd.ExcelWriter(output_master, engine='openpyxl') as writer:
            df_l.to_excel(writer, index=False, sheet_name='Labor')
            df_i.to_excel(writer, index=False, sheet_name='Inputs')
            df_s.to_excel(writer, index=False, sheet_name='Sales')
            df_h.to_excel(writer, index=False, sheet_name='Harvest')
            df_r.to_excel(writer, index=False, sheet_name='Rainfall')

        st.download_button(
            label="📥 മുഴുവൻ കണക്കുകളും ബാക്ക്അപ്പ് എടുക്കുക (Excel)",
            data=output_master.getvalue(),
            file_name=f"estate_backup_{curr_user}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- 2. WEATHER & MARKET PRICES ---
    elif menu == "🌤️ കാലാവസ്ഥ & വിപണി വില (Live)":
        st.subheader("🌤️ തത്സമയ ഹൈറേഞ്ച് കാലാവസ്ഥ & വിപണി വില")
        
        # OpenWeather API from Streamlit Secrets
        api_key = st.secrets.get("OPENWEATHER_API_KEY", "bd5e373850a4d262a32b304f11700b36")
        
        def fetch_weather(city_name):
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric&lang=ml"
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    return data['main']['temp'], data['main']['humidity'], data['weather'][0]['description']
            except:
                pass
            return None, None, None

        temp_h, hum_h, desc_h = fetch_weather("Kattappana")
        
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown("##### 📍 തറവാട് പറമ്പ്")
            if temp_h:
                st.info(f"🌡️ **താപനില:** {temp_h}°C\n💧 **ഈർപ്പം:** {hum_h}%\n☁️ **അവസ്ഥ:** {desc_h}")
            else:
                st.info("🌡️ **അവസ്ഥ:** 24°C | ഭാഗികമായി മേഘാവൃതം")

        with col_w2:
            st.markdown("##### 📍 പുഷ്പക്കണ്ടം പ്ലോട്ട്")
            if temp_h:
                st.info(f"🌡️ **താപനില:** {temp_h - 1}°C\n💧 **ഈർപ്പം:** {hum_h + 2}%\n☁️ **അവസ്ഥ:** {desc_h}")
            else:
                st.info("🌡️ **അവസ്ഥ:** 22°C | ഈർപ്പമുള്ള കാലാവസ്ഥ")

    # --- 3. RAINFALL LOG ---
    elif menu == "🌧️ മഴയുടെ അളവ് (Rainfall mm)":
        st.subheader("🌧️ ദിനചര്യ മഴ രേഖപ്പെടുത്താൻ")
        
        with st.form("rain_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            r_date = col1.date_input("തീയതി")
            r_plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            r_mm = col1.number_input("മഴയുടെ അളവ് (mm)", min_value=0.0, step=1.0)
            r_notes = col2.text_input("കുറിപ്പുകൾ")
            
            if st.form_submit_button("സേവ് ചെയ്യുക", use_container_width=True):
                conn.execute("INSERT INTO rainfall (user, date, plot, mm, notes) VALUES (?, ?, ?, ?, ?)",
                             (curr_user, str(r_date), r_plot, r_mm, r_notes))
                conn.commit()
                st.success("മഴയുടെ വിവരങ്ങൾ സേവ് ചെയ്തു!")
                st.rerun()

        df_rain = pd.read_sql_query("SELECT id, date AS തീയതി, plot AS പ്ലോട്ട്, mm AS 'അളവ് (mm)', notes AS കുറിപ്പ് FROM rainfall WHERE user=?", conn, params=(curr_user,))
        if not df_rain.empty:
            st.write("---")
            st.dataframe(df_rain, use_container_width=True)

    # --- 4. LABOR & WAGES ---
    elif menu == "👷 തൊഴിൽ, കൂലി & അഡ്വാൻസ്":
        st.subheader("👷 തൊഴിലാളി കൂലിയും അഡ്വാൻസും")
        
        workers_db = conn.execute("SELECT name FROM workers_master WHERE user=?", (curr_user,)).fetchall()
        worker_list = [w['name'] for w in workers_db] if workers_db else ["തൊഴിലാളികൾ ഇല്ല"]

        with st.form("labor_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            entry_type = col1.selectbox("ഇനം", ["കൂലി (Labor Wages)", "അഡ്വാൻസ് (Advance Payment)"])
            worker = col2.selectbox("തൊഴിലാളി", worker_list)
            work = col1.text_input("പണിയുടെ പേര് / വിവരണം")
            amount = col2.number_input("ആകെ തുക (₹)", min_value=0.0, step=50.0)
            status = col1.selectbox("സ്റ്റാറ്റസ്", ["Paid (നൽകി)", "Pending (നൽകാനുണ്ട്)"])
            mode = col2.selectbox("രീതി", ["Cash", "GPay", "Bank Transfer"])
            note = st.text_input("കുറിപ്പ്")

            if st.form_submit_button("സേവ് ചെയ്യുക", use_container_width=True):
                conn.execute("INSERT INTO labor (user, date, plot, category, work, worker, amount, status, mode, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (curr_user, str(date), plot, entry_type, work, worker, amount, status, mode, note))
                conn.commit()
                st.success("കൂലി വിവരം സേവ് ചെയ്തു!")
                st.rerun()

    # --- 5. INPUTS (FERTILIZERS & PESTICIDES) ---
    elif menu == "🧪 വളം/മരുന്ന് & ഡോസേജ്":
        st.subheader("🧪 വളം, മരുന്ന് വിവരങ്ങൾ")
        
        with st.form("inputs_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            item = col1.text_input("വളത്തിന്റെ/മരുന്നിന്റെ പേര്")
            dosage = col2.text_input("ഡോസേജ്")
            qty = col1.text_input("അളവ് (Qty)")
            cost = col2.number_input("ചെലവ് (₹)", min_value=0.0, step=50.0)
            
            if st.form_submit_button("സേവ് ചെയ്യുക", use_container_width=True):
                conn.execute("INSERT INTO inputs (user, date, plot, item, dosage, qty, cost) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (curr_user, str(date), plot, item, dosage, qty, cost))
                conn.commit()
                st.success("വിവരങ്ങൾ സേവ് ചെയ്തു!")
                st.rerun()

    # --- 6. TRAVEL & FUEL ---
    elif menu == "🚗 യാത്ര & പെട്രോൾ ചെലവ്":
        st.subheader("🚗 യാത്ര, പെട്രോൾ വിവരങ്ങൾ")
        
        with st.form("travel_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            purpose = col1.text_input("യാത്രയുടെ ഉദ്ദേശ്യം / വിവരണം")
            cost = col2.number_input("ചെലവ് (₹)", min_value=0.0, step=50.0)
            
            if st.form_submit_button("സേവ് ചെയ്യുക", use_container_width=True):
                conn.execute("INSERT INTO travel (user, date, plot, purpose, cost) VALUES (?, ?, ?, ?, ?)",
                             (curr_user, str(date), plot, purpose, cost))
                conn.commit()
                st.success("യാത്രാ വിവരങ്ങൾ സേവ് ചെയ്തു!")
                st.rerun()

    # --- 7. HARVEST ---
    elif menu == "🌿 വിളവെടുപ്പ്":
        st.subheader("🌿 വിളവെടുപ്പ് വിവരങ്ങൾ")
        
        with st.form("harvest_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            plot = col2.selectbox("പ്ലോട്ട്", plots_list)
            crop = col1.text_input("വിള (ഉദാ: ഏലം, കുരുമുളക്)")
            green_wt = col2.number_input("പച്ച തൂക്കം (kg)", min_value=0.0, step=1.0)
            dry_wt = col1.number_input("ഉണക്ക തൂക്കം (kg)", min_value=0.0, step=1.0)
            outturn = col2.number_input("ഔട്ട്‌ടേൺ (Outturn %)", min_value=0.0, step=1.0)
            notes = st.text_input("കുറിപ്പുകൾ")
            
            if st.form_submit_button("സേവ് ചെയ്യുക", use_container_width=True):
                conn.execute("INSERT INTO harvest (user, date, plot, crop, green_wt, dry_wt, outturn, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                             (curr_user, str(date), plot, crop, green_wt, dry_wt, outturn, notes))
                conn.commit()
                st.success("വിളവെടുപ്പ് വിവരങ്ങൾ സേവ് ചെയ്തു!")
                st.rerun()

    # --- 8. SALES & INCOME ---
    elif menu == "💰 വിൽപ്പന & വരുമാനം":
        st.subheader("💰 വിൽപ്പന വിവരങ്ങൾ")
        
        with st.form("sales_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            date = col1.date_input("തീയതി")
            crop = col2.text_input("വിള (ഉദാ: ഏലം)")
            qty = col1.number_input("അളവ് (kg)", min_value=0.0, step=1.0)
            total = col2.number_input("ആകെ തുക (₹)", min_value=0.0, step=100.0)
            buyer = st.text_input("വാങ്ങിയ ആൾ / സ്ഥാപനം")
            
            if st.form_submit_button("സേവ് ചെയ്യുക", use_container_width=True):
                conn.execute("INSERT INTO sales (user, date, crop, qty, total, buyer) VALUES (?, ?, ?, ?, ?, ?)",
                             (curr_user, str(date), crop, qty, total, buyer))
                conn.commit()
                st.success("വിൽപ്പന വിവരങ്ങൾ സേവ് ചെയ്തു!")
                st.rerun()

    # --- 9. MASTER SETTINGS (RESTRICTED TO ADMIN FOR USERS TABLE) ---
    elif menu == "⚙️ മാസ്റ്റർ ക്രമീകരണങ്ങൾ":
        st.subheader("⚙️ മാസ്റ്റർ ക്രമീകരണങ്ങൾ")
        
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown("### 👷 തൊഴിലാളിയെ ചേർക്കുക")
            with st.form("worker_add_form", clear_on_submit=True):
                w_name = st.text_input("പേര്")
                w_phone = st.text_input("ഫോൺ നമ്പർ")
                if st.form_submit_button("സേവ് ചെയ്യുക"):
                    if w_name.strip():
                        conn.execute("INSERT INTO workers_master (user, name, phone) VALUES (?, ?, ?)",
                                     (curr_user, w_name.strip(), w_phone))
                        conn.commit()
                        st.success("തൊഴിലാളിയെ ചേർത്തു!")
                        st.rerun()

        # Admin Only Section
        if st.session_state.role == "admin":
            st.write("---")
            st.markdown("### 👥 സിസ്റ്റം യൂസർ മാനേജ്‌മെന്റ് (Admin Only)")
            users_db = pd.read_sql_query("SELECT username AS 'യൂസർ നെയിം', role AS 'റോൾ' FROM users", conn)
            st.dataframe(users_db, use_container_width=True)
        else:
            st.write("---")
            st.info("ℹ️ യൂസർ അക്കൗണ്ടുകൾ മാനേജ് ചെയ്യുന്നതിന് അഡ്മിൻ അനുവാദം ആവശ്യമാണ്.")

    conn.close()
