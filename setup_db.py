import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

# ഗൂഗിൾ ഷീറ്റുമായി കണക്ട് ചെയ്യാനുള്ള സെറ്റപ്പ്
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = dict(st.secrets["gcp_service_account"]) # നിങ്ങളുടെ secrets.toml ഫയലിൽ നിന്നുള്ള ഡാറ്റ
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# നിങ്ങൾ ഉണ്ടാക്കിയ ഷീറ്റ് ഓപ്പൺ ചെയ്യുന്നു
try:
    sheet = client.open("Thottam_ERP_Database")
    print("✅ ഗൂഗിൾ ഷീറ്റ് വിജയകരമായി കണക്ട് ചെയ്തു!")
except Exception as e:
    print("⚠️ ഷീറ്റ് കണ്ടെത്താനായില്ല! ഷീറ്റിന്റെ പേര് ശരിയാണെന്നും Share ചെയ്തിട്ടുണ്ടെന്നും ഉറപ്പാക്കുക.")
    exit()

# ഉണ്ടാക്കേണ്ട ടാബുകളും അവയുടെ ഹെഡറുകളും
tabs_data = {
    "activity_logs": ["username", "action_type", "details", "timestamp"],
    "workers": ["name", "block", "work_type", "wage", "status", "date"],
    "advances": ["name", "amount", "date"],
    "soil_tests": ["block", "soil_ph", "nutrients", "water_quality", "date"],
    "exports": ["buyer_country", "crop", "quantity", "shipping_cost", "date"],
    "yields": ["crop_name", "block_source", "grade", "quantity", "batch_id", "date"],
    "inventory": ["item_name", "category", "quantity", "date"],
    "sales": ["buyer_name", "phone_no", "crop_sold", "quantity_sold", "price_per_kg", "gst_percent", "total_amount", "date"],
    "machinery": ["mach_name", "fuel_cost", "service_note", "date"],
    "expenses": ["category", "amount", "description", "date"]
}

# ഓരോ ടാബും ഓട്ടോമാറ്റിക് ആയി ക്രിയേറ്റ് ചെയ്യുന്നു
for tab_name, headers in tabs_data.items():
    try:
        ws = sheet.add_worksheet(title=tab_name, rows="100", cols="20")
        ws.append_row(headers)
        print(f"✅ ടാബ് ഉണ്ടാക്കി: {tab_name}")
    except Exception as e:
        print(f"ℹ️ ടാബ് '{tab_name}' നിലവിലുണ്ട്.")

print("🎉 സെറ്റപ്പ് പൂർത്തിയായി! ഇനി നിങ്ങളുടെ ERP ആപ്പ് റൺ ചെയ്യാം.")