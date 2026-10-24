import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Page Config
st.set_page_config(
    page_title="District Training Center Software",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Connect to Google Sheets
@st.cache_resource
def get_sheets_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        return None

client = get_sheets_client()

# Sidebar Navigation matching your CSV modules
st.sidebar.title("🏛️ DTC Navigation")
main_module = st.sidebar.selectbox(
    "Select Module", 
    ["1. Training Summary", "2. Current Year Data (26-27)", "3. Training Database", "4. Knowledge Bank", "5. About Us"]
)

# --- MODULE 1: TRAINING SUMMARY ---
if main_module == "1. Training Summary":
    st.title("📊 Training Summary")
    st.markdown("### Yearwise Training Performance")
    st.info("Here you can analyze year-over-year training achievements pulled from your Google Sheet.")
    
    # Placeholder for pulling Yearwise data
    if client:
        try:
            sh = client.open("DTC_Database")
            ws = sh.worksheet("Yearwise_Performance")
            data = pd.DataFrame(ws.get_all_records())
            st.dataframe(data, use_container_width=True)
        except Exception:
            st.warning("Please create a worksheet named 'Yearwise_Performance' in your Google Sheet.")

# --- MODULE 2: CURRENT YEAR DATA ---
elif main_module == "2. Current Year Data (26-27)":
    st.title("📅 Current Year Data (2026-27)")
    
    sub_tab = st.selectbox(
        "Select Section", 
        ["Registration 26-27", "Pre-Test 26-27", "Post-Test 26-27", "Feedback 26-27", "Field Evaluation", "Monthly Report", "Group Photos"]
    )
    
    if sub_tab == "Registration 26-27":
        st.subheader("📝 Trainee Registration")
        # Add registration form / table view here
    elif sub_tab == "Pre-Test 26-27":
        st.subheader("📋 Pre-Test Records")
    elif sub_tab == "Post-Test 26-27":
        st.subheader("📈 Post-Test Records")
    elif sub_tab == "Feedback 26-27":
        st.subheader("⭐ Feedback Analysis")
    elif sub_tab == "Field Evaluation":
        st.subheader("🔍 Field Evaluation Reports")
    elif sub_tab == "Monthly Report":
        st.subheader("📅 Monthly Progress Reports")
    elif sub_tab == "Group Photos":
        st.subheader("🖼️ Training Batch Group Photos")

# --- MODULE 3: TRAINING DATABASE ---
elif main_module == "3. Training Database":
    st.title("🗄️ Training Database (Directory)")
    
    db_category = st.selectbox(
        "Select Personnel Database", 
        ["MO Database", "AYUSH MO Database", "RBSK MO Database", "CHO Database", "ANM Database", "MPHW Database", "ASHA Database"]
    )
    
    st.markdown(f"### Viewing: {db_category}")
    if client:
        try:
            sh = client.open("DTC_Database")
            ws = sh.worksheet(db_category)
            data = pd.DataFrame(ws.get_all_records())
            st.dataframe(data, use_container_width=True)
            
            # Simple search filter
            search_query = st.text_input(f"Search in {db_category}")
            if search_query:
                filtered = data[data.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                st.dataframe(filtered, use_container_width=True)
        except Exception:
            st.warning(f"Worksheet '{db_category}' not found in your Google Sheet. Please add it!")

# --- MODULE 4: KNOWLEDGE BANK ---
elif main_module == "4. Knowledge Bank":
    st.title("📚 Knowledge Bank & Resources")
    
    kb_section = st.selectbox(
        "Select Resource Category",
        ["Prayers", "Training Materials (PDF/PPT/Videos)", "Pre/Post Test Forms", "Feedback Forms", "Field Evaluation Forms", "Innovations", "Games", "Govt Schemes"]
    )
    
    st.subheader(f"📂 {kb_section}")
    st.write("Access your reference files, links, media, and interactive guides here.")

# --- MODULE 5: ABOUT US ---
elif main_module == "5. About Us":
    st.title("ℹ️ About District Training Center")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Vision & Mission")
        st.write("To empower healthcare professionals through world-class training, rigorous evaluation, and continuous capacity building.")
        st.subheader("🏆 Success Milestones")
        st.write("Tracking our achievements and impact across healthcare training programs.")
    with col2:
        st.subheader("🏢 DTT Profile")
        st.write("District Training Team Profile and administrative structure.")
        st.subheader("📞 Contact Info")
        st.write("Get in touch with the DTC administration and training coordinators.")
