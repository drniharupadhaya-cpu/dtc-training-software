import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configure the main page layout
st.set_page_config(
    page_title="DTC Training & HR Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = ["Dashboard", "Trainee Management", "HR Records", "Settings"]
choice = st.sidebar.radio("Go to", menu)

# Helper function to connect to Google Sheets
@st.cache_resource
def init_google_sheet():
    try:
        # We will pull credentials from Streamlit Secrets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        return None

# Main Views
if choice == "Dashboard":
    st.title("📊 Training Center Analytics Dashboard")
    st.markdown("Live Training & HR data powered by Google Sheets & Streamlit.")
    
    client = init_google_sheet()
    if client is None:
        st.warning("⚠️ Google Sheets connection is waiting for your Service Account secrets to be added in Streamlit Cloud Settings.")
    else:
        st.success("✨ Connected successfully to Google Sheets backend!")

elif choice == "Trainee Management":
    st.title("🎓 Trainee Management")
    st.write("Register and track trainees here.")

elif choice == "HR Records":
    st.title("👥 HR Records")
    st.write("Manage staff data, attendance, and performance metrics here.")

elif choice == "Settings":
    st.title("⚙️ Settings & Configuration")
    st.markdown("""
    ### How to link your Google Sheet:
    1. Create a Google Sheet with your training/HR data.
    2. Share the Google Sheet editor email found in your Google Cloud Service Account JSON file.
    3. Paste your JSON credentials into your **Streamlit Community Cloud App Secrets** using the `[gcp_service_account]` format.
    """)
