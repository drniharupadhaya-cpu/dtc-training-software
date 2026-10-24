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

# Helper function to connect to Google Sheets using Streamlit Secrets
@st.cache_resource
def get_sheets_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = ["Dashboard", "Trainee Management", "HR Records", "Settings"]
choice = st.sidebar.radio("Go to", menu)

client = get_sheets_client()

# Main Views
if choice == "Dashboard":
    st.title("📊 Training Center Analytics Dashboard")
    st.markdown("Live Training & HR data powered by your Master Google Sheet.")
    
    if client is None:
        st.warning("⚠️ Please check your Streamlit Secrets configuration.")
    else:
        try:
            # Open your Google Sheet by its exact name in Google Drive
            # Make sure you have a sheet named "DTC_Database" with worksheets named "Trainees" and "HR"
            sh = client.open("DTC_Database")
            
            # Fetch Trainee metrics
            trainee_ws = sh.worksheet("Trainees")
            trainee_data = pd.DataFrame(trainee_ws.get_all_records())
            
            # Fetch HR metrics
            hr_ws = sh.worksheet("HR")
            hr_data = pd.DataFrame(hr_ws.get_all_records())
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Trainees Registered", len(trainee_data) if not trainee_data.empty else 0)
            col2.metric("Total Staff Members", len(hr_data) if not hr_data.empty else 0)
            col3.metric("System Status", "Online & Synced")
            
            st.subheader("Recent Trainee Records")
            if not trainee_data.empty:
                st.dataframe(trainee_data.tail(5), use_container_width=True)
            else:
                st.info("No trainee records found yet. Use the 'Trainee Management' tab to add some!")
                
        except Exception as e:
            st.error(f"Could not load worksheets. Make sure your Google Sheet is named 'DTC_Database' and has sheets named 'Trainees' and 'HR'. Details: {e}")

elif choice == "Trainee Management":
    st.title("🎓 Trainee Management & Registration")
    
    with st.form("trainee_form"):
        st.subheader("Add New Trainee")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Trainee Full Name")
            batch = st.text_input("Batch / Program Name")
        with col2:
            contact = st.text_input("Contact Number / Email")
            status = st.selectbox("Status", ["Active", "Completed", "Dropped"])
            
        submit_button = st.form_submit_button(label="Save Trainee to Google Sheet")
        
        if submit_button:
            if client and name:
                try:
                    sh = client.open("DTC_Database")
                    ws = sh.worksheet("Trainees")
                    ws.append_row([name, batch, contact, status])
                    st.success(f"Successfully added {name} to Google Sheets!")
                except Exception as e:
                    st.error(f"Failed to save data: {e}")
            else:
                st.warning("Please fill in the trainee's name and ensure the database is connected.")

elif choice == "HR Records":
    st.title("👥 HR & Staff Records")
    
    with st.form("hr_form"):
        st.subheader("Add Staff Attendance / Record")
        col1, col2 = st.columns(2)
        with col1:
            staff_name = st.text_input("Staff Member Name")
            role = st.text_input("Designation / Role")
        with col2:
            attendance_status = st.selectbox("Attendance", ["Present", "Absent", "On Leave"])
            date = st.date_input("Date")
            
        hr_submit = st.form_submit_button(label="Save HR Record to Google Sheet")
        
        if hr_submit:
            if client and staff_name:
                try:
                    sh = client.open("DTC_Database")
                    ws = sh.worksheet("HR")
                    ws.append_row([staff_name, role, attendance_status, str(date)])
                    st.success(f"Successfully recorded data for {staff_name}!")
                except Exception as e:
                    st.error(f"Failed to save HR record: {e}")
            else:
                st.warning("Please fill in the staff name.")

elif choice == "Settings":
    st.title("⚙️ Settings & Database Structure")
    st.markdown("""
    ### Google Sheet Setup Checklist:
    1. Create a Google Sheet named **`DTC_Database`**.
    2. Create two tabs inside it named exactly:
       - **`Trainees`** (Columns: `Name`, `Batch`, `Contact`, `Status`)
       - **`HR`** (Columns: `StaffName`, `Role`, `Attendance`, `Date`)
    3. Share your Google Sheet with your Google Cloud Service Account email as an **Editor**.
    """)
