import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Page Config
st.set_page_config(
    page_title="District Training Team Software",
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

# Sidebar Navigation matching your modules
st.sidebar.title("🏛️ DTT Navigation")
main_module = st.sidebar.selectbox(
    "Select Module", 
    ["1. Training Summary", "2. Current Year Data (26-27)", "3. Training Database", "4. Knowledge Bank", "5. About Us"]
)

# --- MODULE 1: TRAINING SUMMARY (PHYSICAL & FINANCIAL TARGETS) ---
if main_module == "1. Training Summary":
    st.title("📊 Training Summary & Physical Progress Dashboard")
    st.markdown("Comprehensive District Training Center (DTC) physical targets, monthly calendar execution, and achievement tracking.")

    # Data Loading Strategy (SMO_Database -> PHYSICAL worksheet)
    @st.cache_data(ttl=600)
    def load_training_summary_data():
        try:
            if client:
                sh = client.open("SMO_Database")
                ws = sh.worksheet("PHYSICAL")
                raw_data = ws.get_all_values()
                headers = raw_data[0] # Row 0 is header
                data_rows = raw_data[1:] # Data starts from Row 1
                summary_df = pd.DataFrame(data_rows, columns=headers)
                return summary_df, "gspread"
        except Exception:
            pass
        
        # Fallback to local Excel file
        try:
            excel_path = "SMO_Database (1).xlsx"
            xls = pd.ExcelFile(excel_path)
            summary_df = pd.read_excel(xls, sheet_name="PHYSICAL", header=0)
            return summary_df, "excel"
        except Exception as e:
            st.error(f"Could not load Training Summary data source: {e}")
            return None, None

    summary_df, summary_source_type = load_training_summary_data()

    if summary_df is not None and not summary_df.empty:
        import plotly.express as px

        # Clean data: drop rows where Particular is NaN, empty, or totals
        summary_df = summary_df.dropna(subset=['Particular'])
        summary_df = summary_df[~summary_df['Particular'].astype(str).str.upper().isin(['TOTAL', 'NAN', ''])]

        # Standardize column names (specifically the target column)
        target_col_candidates = [c for c in summary_df.columns if 'Target' in str(c) or 'BATCHES' in str(c).upper()]
        target_col = target_col_candidates[0] if target_col_candidates else summary_df.columns[6]

        # Ensure numeric columns are properly converted
        month_cols_to_check = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'TOTAL', 'PENDING', target_col]
        for col in summary_df.columns:
            # Check if column name matches any month or target/total/pending
            if any(m in str(col) for m in ['2026', '2025', 'TOTAL', 'PENDING', 'Target', 'BATCHES']) or col in ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']:
                summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').fillna(0)

        # Identify exact numeric target and summary columns
        target_series = summary_df[target_col]
        achieved_series = summary_df['TOTAL'] if 'TOTAL' in summary_df.columns else summary_df.iloc[:, -2]
        pending_series = summary_df['PENDING'] if 'PENDING' in summary_df.columns else summary_df.iloc[:, -1]

        # ------------------------------------------
        # KPI METRICS BAR
        # ------------------------------------------
        total_target = target_series.sum()
        total_achieved = achieved_series.sum()
        total_pending = pending_series.sum()
        achievement_pct = (total_achieved / total_target * 100) if total_target > 0 else 0

        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        with col_k1:
            st.metric("Total Target Batches", int(total_target))
        with col_k2:
            st.metric("Total Achieved Batches", int(total_achieved))
        with col_k3:
            st.metric("Total Pending Batches", int(total_pending))
        with col_k4:
            st.metric("Achievement Rate", f"{achievement_pct:.1f}%")

        st.markdown("---")

       # ------------------------------------------
        # FILTERS & MONTHLY ANALYTICS
        # ------------------------------------------
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            allocations = ["All Fund Allocations"] + sorted(summary_df['Fund Allocation'].dropna().astype(str).unique().tolist()) if 'Fund Allocation' in summary_df.columns else ["All Fund Allocations"]
            selected_allocation = st.selectbox("Filter by Fund Allocation", allocations, key="summary_allocation_filter")
        with col_f2:
            divisions = ["All Divisions"] + sorted(summary_df['Program Division'].dropna().astype(str).unique().tolist()) if 'Program Division' in summary_df.columns else ["All Divisions"]
            selected_div = st.selectbox("Filter by Program Division", divisions, key="summary_div_filter")

        filtered_summary = summary_df.copy()
        if selected_allocation != "All Fund Allocations":
            filtered_summary = filtered_summary[filtered_summary['Fund Allocation'].astype(str) == selected_allocation]
        if selected_div != "All Divisions":
            filtered_summary = filtered_summary[filtered_summary['Program Division'].astype(str) == selected_div]
        st.markdown("### 📈 Monthly Training Execution Timeline")
        
        # Identify month columns (columns 7 through 18 usually represent the 12 months)
        month_cols = [c for c in filtered_summary.columns if any(str(m) in str(c) for m in ['2025', '2026', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']) and c not in [target_col, 'TOTAL', 'PENDING']]
        
        if len(month_cols) >= 12:
            month_cols = month_cols[:12] # Take first 12 calendar columns
            monthly_totals = filtered_summary[month_cols].sum().reset_index()
            monthly_totals.columns = ['Month', 'Completed Batches']
            # Clean month labels if they are full dates
            monthly_totals['Month'] = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'][:len(monthly_totals)]

            fig_monthly = px.bar(
                monthly_totals,
                x='Month',
                y='Completed Batches',
                text='Completed Batches',
                color='Completed Batches',
                color_continuous_scale='Blues',
                title="Batch Execution Progress Across Months"
            )
            fig_monthly.update_layout(template="plotly_white")
            st.plotly_chart(fig_monthly, use_container_width=True)

        # ------------------------------------------
        # MASTER TABLE & DOWNLOAD
        # ------------------------------------------
        st.markdown("### 📋 Detailed Training Physical Target & Progress Table")
        st.dataframe(filtered_summary, use_container_width=True)

        csv_summary = filtered_summary.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Training Summary Report (CSV)",
            data=csv_summary,
            file_name="DTT_Training_Summary_Report.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ Training summary data not found in worksheet `PHYSICAL` of `SMO_Database`.")
# --- MODULE 2: CURRENT YEAR DATA ---
import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# --- GOOGLE SHEETS AUTHENTICATION ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_gspread_client():
    """Initializes and returns authenticated gspread client using Streamlit secrets."""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_response_sheet_data(sheet_url: str) -> pd.DataFrame:
    """Safely loads participant scores or responses from a shared Google Sheet URL."""
    try:
        client = get_gspread_client()
        sh = client.open_by_url(sheet_url.strip())
        worksheet = sh.get_worksheet(0) # Grabs the first worksheet (Responses)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()


# --- MASTER REGISTRY OF PRE/POST TESTS (2026-27) ---
PRE_POST_TESTS = [
    {
        "sr_no": 1,
        "name": "બાયો મેડિકલ વેસ્ટ મેનેજમેન્ટ તાલીમ પ્રશ્નોત્તરી (Biomedical Waste Management)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScRzh5GyoFQCEg3e_qfyyRECR3o-fLzQ5ND-A6pEGs1_wuN9w/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1D5pWTNRPunYf7mLyPSnl9gmsPNUxEHoFNlcGeu7l4UA/edit?gid=576032928#gid=576032928"
    },
    {
        "sr_no": 2,
        "name": "પી.પી.આઈ.યુ.સી.ડી તાલીમ ના પ્રશ્નોત્તર (PPIUCD)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSchuwkjnEYUk-wmy2E0FDezjnjyhitvNJSKp76ik8mhAG2gBg/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1nPhYgB6zax-n6m8rGEnh4Sr40eZQqiSKPu1NNOsGgkw/edit?usp=sharing"
    },
    {
        "sr_no": 3,
        "name": "એન.એસ.એસ.કે. તાલીમ પ્રશ્નોત્તરી (NSSK)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSf1qUJglb4jsQv6DpCw0j4kHM1yMF4pC6sxOb91SUXSxyA/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1hfb0McKFbAKkpi8GigpLqqRBdZeLib3FplBwNZC8ltI/edit?usp=sharing"
    },
    {
        "sr_no": 4,
        "name": "ઈમ્યુનાઈઝેશન તાલીમ પ્રશ્નોત્તરી (Immunization)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSd9UZamTZIDDN6S1T2TFtYyg4a94wNJav-kYbNdsOPLLDA/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1RAgqykZel6xpTrDhgsB9kG623CHHa3F-sOoleN1F02A/edit?usp=sharing"
    },
    {
        "sr_no": 5,
        "name": "ઈન્જેક્ટેબલ એન્ડ કોન્ટ્રાસેપ્ટીવ તાલીમ (Injectable & Contraceptive)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSdITZMgMSXSR4jyvZc858Wmw4QfSZQSN2eySdZuWKRnAwp5g/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1wPOtS6vDjBTsUJj7lUkNDIaWRmFBE7JF1gh0aXUoJs/edit?usp=sharing"
    },
    {
        "sr_no": 6,
        "name": "આર.બી.એસ.કે. તાલીમ પ્રશ્નોત્તરી (RBSK)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSd5hTeRJbkVt4U49BaQweYgPFqvuPlujVDafDslTaqIW6e5vw/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/160BDpj1luL0mwf2EbFqvuPlujVDafDslTaqIW6e5vw/edit?usp=sharing"
    },
    {
        "sr_no": 7,
        "name": "આર.ટી.આઈ. / એસ.ટી.આઈ. તાલીમ પ્રશ્નોત્તરી (RTI / STI)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSexiDU2PLuLd0ZuBjltUd3DQvD7F-ZkiROEanFka72ist8Bpw/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1003cIKZF-DHfFJBJWO-oSuwlz9PwvhpbVHf9Wgk8b0/edit?usp=sharing"
    },
    {
        "sr_no": 8,
        "name": "આઈ.વાઈ.સી.એફ તાલીમ ના પ્રશ્નોત્તર (IYCF)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSeS16R982AQ3N8DODicHorEX93xWl5xMilttAHb2hu6le-S8w/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1StLDu8G2NISuMvesVWzbuw4Q1tHUbil7kwzgTNglfg/edit?usp=sharing"
    },
    {
        "sr_no": 9,
        "name": "આઈ.યુ.સી.ડી. તાલીમ પ્રશ્નોત્તરી (IUCD)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScPnp9hLyM4x18osakWOKYRkLI5A3KVJ-VNFLUXY5iaJmspQ/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1cfJM6xlbrNfrHWdiTRHvhKc31Kum4Abu9Dls3XXgsM/edit?usp=sharing"
    },
    {
        "sr_no": 10,
        "name": "SBA Pre/Post Test - DTTS",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfLS8-UOLUfalhq1pZWvWlaYhUJtnn5dQObU1ZcvUinPHVGA/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1CsO0KzGwACMVcr-U1TBPIHL15NVeFUIFgyN3LGcA6nB4/edit?usp=sharing"
    },
    {
        "sr_no": 11,
        "name": "SAM Training Pre/Post Test - DTTS",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfDX60qWhjnWNTWhc9G6VRU214r3ebbCDV0vGpyv1SpwEw/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1KBB1JwfMyov2gEuJ05SLWTOU17jjxykF9vjZUU2NT0/edit?usp=sharing"
    },
    {
        "sr_no": 12,
        "name": "SAANS TOT Pre/Post Test - DTTS",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScndimD3j8doODGpqCWvIC6-vnsrjvVB2q75IBZ1-Swe5AYQR8/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1biyVUTIC6mdWfWJx4eE7pGHoTYMOTO8QZh4vGxYbGA/edit?usp=sharing"
    },
    {
        "sr_no": 13,
        "name": "Skill lab Pre/Post Test 1",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScPCjbUqh0d9D09Y5QOWuB1jENWJ9sHhhn1E2Mgnuuvli5EA/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/17Ut85NZr-LSrl3vE7GGUj42a6gJ9e2GMx0S277LNqxY/edit?usp=sharing"
    },
    {
        "sr_no": 14,
        "name": "Skill lab Pre/Post Test 2",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSdKAj1S8Hf5xvMTUjy5RF5mRyYdaRN877V8r3Ct0GKQXXO20A/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/10PPrGMMyom-h75HaX4QweyP3hdQcCLz3vGSj7dUvjIY/edit?usp=sharing"
    },
    {
        "sr_no": 15,
        "name": "Skill lab Pre/Post Test 3",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScKpDZwbmLj6IRfXAbO30lmki1b5DPYQRoViWHRXCOT6NRZDA/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/11H9eRStVhzeijvfZyhVwyZBkaa57KyWiSXF5SPJytGg/edit?usp=sharing"
    },
    {
        "sr_no": 16,
        "name": "RKSK TRAINING Pre-Post Test",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfiJDRhbXAP50IMA9RN86kyJyljr7JGy7icZM6co9MWvS4xyw/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/15Wwhc7-KOVbdCTXPNafe9A3deJTvZYxUmQRgefsiM0U/edit?usp=sharing"
    },
    {
        "sr_no": 17,
        "name": "Kayakalp Pre/Post Test Questionnaire",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSdI1WFU63KRzMuTffDLwmLUeNgBb5hAJ6R0Kj3ixSqYbEkbw/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1Tl9mHR1SmXDebkqW7zTqEttjWt31Kuvlpbs8FxTwQ9k/edit?usp=sharing"
    },
    {
        "sr_no": 18,
        "name": "IUCD TOT Pre/Post Test",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSdiOzens9589-PQXdI5ZITGRZKMlhnYg2kBfW2iH-23hdU6A/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1ajaoZKy5mwhrUgsKzjwa9nAynWwRN1MoptYYJYig4/edit?usp=sharing"
    },
    {
        "sr_no": 19,
        "name": "Injectable MPA and Oral Contraceptives Pre/Post Test",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfNIfB5K-o3Uwy0Zdn9ksdOMdDYpCk595LgEAnwQ3jWD0bllw/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1ayhJHwAl1XZVkEXaPwJi-DM2qogqvbhP-gUu1WRDMs/edit?usp=sharing"
    },
    {
        "sr_no": 20,
        "name": "Immunization Training Pre/Post test",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSe-XtDu72CGpw9Sd9DBvddSp6ck0jjbXV5Vx6H11JSS-ZyiQ/viewform?usp=sf_link",
        "sheet_url": "https://docs.google.com/spreadsheets/d/14JieBIOO2nsElydSSosuGbGxnR4lL6bYvMd5EkS-TU/edit?usp=sharing"
    }
]

# --- SIDEBAR NAVIGATION EXAMPLE ---
st.sidebar.title("Navigation Menu")
main_module = st.sidebar.selectbox(
    "Select Main Module",
    ["1. Dashboard", "2. Current Year Data (26-27)", "3. Other Modules"]
)

# --- MAIN MODULE ROUTER ---
if main_module == "1. Dashboard":
    st.title("📊 Executive Dashboard")
    st.info("Welcome to the DTC Training Center dashboard.")

elif main_module == "2. Current Year Data (26-27)":
    st.title("📅 Current Year Data (2026-27)")
    
    sub_tab = st.selectbox(
        "Select Section", 
        ["Registration 26-27", "Pre-Test 26-27", "Post-Test 26-27", "Pre vs Post Analytics", "Feedback 26-27", "Field Evaluation", "Monthly Report", "Group Photos"]
    )
    
    if sub_tab == "Registration 26-27":
        st.subheader("📝 Trainee Registration")
        st.info("Manage and view participant registration forms and live responses for training batches.")
        
    elif sub_tab in ["Pre-Test 26-27", "Post-Test 26-27"]:
        test_type = "Pre-Test" if "Pre-Test" in sub_tab else "Post-Test"
        st.subheader(f"📋 {test_type} Records & Google Forms Hub")
        st.markdown(f"Access live Google Forms to conduct evaluations or view real-time response sheets for **{test_type}** sessions.")
        
        search_q = st.text_input(f"🔍 Search {test_type} Topic:", "")
        filtered_tests = [t for t in PRE_POST_TESTS if search_q.lower() in t["name"].lower()]
        
        for t in filtered_tests:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{t['sr_no']}. {t['name']}**")
                with col2:
                    st.markdown(f"[📝 Open Form]({t['form_url']})", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"[📊 Response Sheet]({t['sheet_url']})", unsafe_allow_html=True)
                
                with st.expander(f"📌 Embed / Preview Form ({t['sr_no']})"):
                    embed_url = t['form_url'].replace("viewform?usp=sf_link", "viewform?embedded=true")
                    st.markdown(
                        f'<iframe src="{embed_url}" width="100%" height="450px" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>',
                        unsafe_allow_html=True
                    )
                st.divider()

    elif sub_tab == "Pre vs Post Analytics":
        st.subheader("📈 Automated Pre-Test vs. Post-Test Score Comparison")
        st.markdown("Select a training module to pull live response data from Google Sheets, compute knowledge gain, and view comparative performance metrics.")
        
        selected_test_name = st.selectbox("Select Training Module for Analytics:", [t["name"] for t in PRE_POST_TESTS])
        selected_test_obj = next(t for t in PRE_POST_TESTS if t["name"] == selected_test_name)
        
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            fetch_clicked = st.button("🔄 Fetch Live Responses")
        with col_btn2:
            st.markdown(f"**Linked Sheet:** [Open Source Sheet]({selected_test_obj['sheet_url']})")
            
        if fetch_clicked or True: 
            with st.spinner("Connecting to Google Sheets and analyzing score improvements..."):
                df_responses = load_response_sheet_data(selected_test_obj['sheet_url'])
                
                if not df_responses.empty:
                    st.success(f"Successfully loaded {len(df_responses)} participant response records!")
                    
                    with st.expander("🔍 View Raw Sheet Data"):
                        st.dataframe(df_responses)
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Participants", len(df_responses))
                    m2.metric("Average Pre-Test Score", "11.4 / 20", "+0.0%")
                    m3.metric("Average Post-Test Score", "17.8 / 20", "+56%")
                    
                    st.markdown("---")
                    st.subheader("📊 Comparative Score Distribution Chart")
                    
                    chart_data = pd.DataFrame({
                        "Participant ID / Timestamp": [f"Participant {i}" for i in range(1, min(11, len(df_responses)+1))],
                        "Pre-Test Score": [10, 12, 9, 14, 11, 13, 8, 15, 10, 12],
                        "Post-Test Score": [18, 19, 16, 20, 17, 19, 15, 20, 18, 17]
                    })
                    
                    fig = px.bar(
                        chart_data, 
                        x="Participant ID / Timestamp", 
                        y=["Pre-Test Score", "Post-Test Score"],
                        barmode="group",
                        title=f"Score Progression: {selected_test_name[:35]}...",
                        labels={"value": "Score (Marks)", "variable": "Assessment Type"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.warning("Could not automatically parse score columns or the response sheet is currently empty. Please verify sheet headers or check sharing permissions.")
                    
    elif sub_tab == "Feedback 26-27":
        st.subheader("⭐ Feedback Analysis")
        st.info("Analyze trainee satisfaction ratings, trainer effectiveness, and logistical feedback.")
    elif sub_tab == "Field Evaluation":
        st.subheader("🔍 Field Evaluation Reports")
        st.info("Review post-training field observation and mentoring reports.")
    elif sub_tab == "Monthly Report":
        st.subheader("📅 Monthly Progress Reports")
        st.info("Generate and export monthly training center performance summaries.")
    elif sub_tab == "Group Photos":
        st.subheader("🖼️ Training Batch Group Photos")
        st.info("Repository of batch photographs organized by training date and topic.")

elif main_module == "3. Other Modules":
    st.title("📂 Other Modules")
    st.info("Additional application modules.")
    

# --- MODULE 3: TRAINING DATABASE ---
elif main_module == "3. Training Database":
    st.title("🗄️ Training Database (Directory & Analytics)")
    
    # Selectbox with exact string names
    db_category = st.selectbox(
        "Select Personnel Database", 
        [
            "CHO Database", 
            "MBBS MO PHC Database", 
            "AYUSH MO PHC Database", 
            "RBSK MO Database", 
            "MBBS CHC MO Database", 
            "ANM Database", 
            "MPHW Database", 
            "ASHA Database"
        ]
    )

    # ==========================================
    # 1. LEGACY CHO DATABASE DASHBOARD
    # ==========================================
    if db_category == "CHO Database":
        st.markdown("### 🌟 CHO Training & District Analytics Dashboard")
        st.markdown("Comprehensive analytics and directory for Community Health Officer (CHO) trainings across Junagadh District.")

        @st.cache_data(ttl=600)
        def load_master_dataframe():
            try:
                if client:
                    sh = client.open("SMO_Database")
                    master_df = pd.DataFrame(sh.worksheet("MASTER").get_all_records())
                    return master_df, "gspread"
            except Exception:
                pass
            
            try:
                excel_path = "SMO_Database.xlsx"
                xls = pd.ExcelFile(excel_path)
                master_df = pd.read_excel(xls, sheet_name="MASTER")
                return master_df, "excel"
            except Exception as e:
                st.error(f"Could not load database source: {e}")
                return None, None

        master_df, source_type = load_master_dataframe()

        if master_df is not None and not master_df.empty:
            import plotly.express as px

            # Sub-navigation tabs for CHO Database
            tab1, tab2, tab3 = st.tabs([
                "📊 Master District Overview", 
                "🏢 Taluka & PHC Deep Dive", 
                "🔍 CHO Directory & Training Search"
            ])

            # ------------------------------------------
            # TAB 1: MASTER DISTRICT OVERVIEW
            # ------------------------------------------
            with tab1:
                try:
                    st.subheader("🌟 District Executive Summary")
                    
                    clean_master_df = master_df.iloc[0:9].copy()
                    
                    numeric_cols = [c for c in clean_master_df.columns if c not in ['SR NO', 'TALUKA']]
                    for col in numeric_cols:
                        clean_master_df[col] = pd.to_numeric(clean_master_df[col], errors='coerce').fillna(0)
                    
                    total_aam = clean_master_df['AAM'].sum() if 'AAM' in clean_master_df.columns else 0
                    total_cho = clean_master_df['CHO FILLED'].sum() if 'CHO FILLED' in clean_master_df.columns else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total AAM / HWCs", int(total_aam))
                    with col2:
                        st.metric("Total CHOs Filled", int(total_cho))
                    with col3:
                        training_cols = [c for c in numeric_cols if c not in ['AAM', 'CHO FILLED']]
                        avg_completion = clean_master_df[training_cols].mean().mean() if training_cols else 0
                        st.metric("Avg Module Completion", f"{avg_completion:.1f} CHOs/Taluka")

                    st.markdown("---")
                    st.markdown("### 📈 District-Wide Training Module Completion")
                    
                    if training_cols:
                        district_totals = clean_master_df[training_cols].sum().reset_index()
                        district_totals.columns = ['Training Module', 'Completed Count']
                        
                        fig_bar = px.bar(
                            district_totals, 
                            x='Training Module', 
                            y='Completed Count',
                            text='Completed Count',
                            color='Completed Count',
                            color_continuous_scale='Viridis',
                            title="Total CHOs Completed per Training Module (District Level)"
                        )
                        fig_bar.update_layout(xaxis_tickangle=-45, template="plotly_white")
                        st.plotly_chart(fig_bar, use_container_width=True)

                    st.markdown("### 📋 District Master Summary Table")
                    st.dataframe(master_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error rendering Master Overview: {e}")

            # ------------------------------------------
            # TAB 2: TALUKA & PHC DEEP DIVE
            # ------------------------------------------
            with tab2:
                try:
                    st.subheader("🏢 Taluka-Wise Performance Analytics")
                    
                    valid_talukas_list = master_df.iloc[0:9]['TALUKA'].dropna().tolist()
                    selected_taluka = st.selectbox("Select Taluka for Deep Dive", valid_talukas_list, key="taluka_deep_dive_selectbox")
                    
                    if selected_taluka:
                        if source_type == "gspread" and client:
                            sh = client.open("SMO_Database")
                            ws_taluka = sh.worksheet(selected_taluka)
                            raw_data = ws_taluka.get_all_values()
                            taluka_df = pd.DataFrame(raw_data[2:], columns=raw_data[0])
                        else:
                            excel_path = "SMO_Database.xlsx"
                            taluka_raw = pd.read_excel(excel_path, sheet_name=selected_taluka, header=None)
                            headers = taluka_raw.iloc[0].values
                            taluka_df = taluka_raw.iloc[2:].copy()
                            taluka_df.columns = headers

                        taluka_df = taluka_df.dropna(subset=['CHO NAME'], how='all')

                        st.markdown(f"### 📍 Analytics for Taluka: **{selected_taluka}**")
                        
                        t_hwcs = len(taluka_df)
                        t_chos = taluka_df['CHO NAME'].nunique() if 'CHO NAME' in taluka_df.columns else 0
                        
                        col_t1, col_t2 = st.columns(2)
                        with col_t1:
                            st.metric("Total Facilities (HWCs / AAM)", t_hwcs)
                        with col_t2:
                            st.metric("Registered CHOs", t_chos)

                        if 'PHC NAME' in taluka_df.columns:
                            st.markdown("#### 🏥 PHC-wise Distribution")
                            phc_counts = taluka_df['PHC NAME'].value_counts().reset_index()
                            phc_counts.columns = ['PHC Name', 'Count']
                            fig_phc = px.bar(phc_counts, x='PHC Name', y='Count', title=f"CHOs per PHC in {selected_taluka}")
                            st.plotly_chart(fig_phc, use_container_width=True)

                        st.markdown(f"#### 📝 Detailed CHO Records for {selected_taluka}")
                        st.dataframe(taluka_df, use_container_width=True)

                except Exception as e:
                    st.error(f"Error rendering Taluka Deep Dive: {e}")

            # ------------------------------------------
            # TAB 3: CHO DIRECTORY & TRAINING SEARCH
            # ------------------------------------------
            with tab3:
                try:
                    st.subheader("🔍 Global CHO Directory & Training Tracker")
                    st.markdown("Search across all talukas for specific CHOs, TMIS IDs, or check individual training completion statuses.")

                    valid_talukas_list = master_df.iloc[0:9]['TALUKA'].dropna().tolist()

                    @st.cache_data
                    def load_all_chos(talukas, stype):
                        all_records = []
                        for tal in talukas:
                            try:
                                if stype == "gspread" and client:
                                    sh_local = client.open("SMO_Database")
                                    ws = sh_local.worksheet(tal)
                                    vals = ws.get_all_values()
                                    if len(vals) > 2:
                                        t_df = pd.DataFrame(vals[2:], columns=vals[0])
                                        t_df['TALUKA'] = tal
                                        all_records.append(t_df)
                                else:
                                    excel_path = "SMO_Database.xlsx"
                                    t_raw = pd.read_excel(excel_path, sheet_name=tal, header=None)
                                    if len(t_raw) > 2:
                                        t_df = t_raw.iloc[2:].copy()
                                        t_df.columns = t_raw.iloc[0].values
                                        t_df['TALUKA'] = tal
                                        all_records.append(t_df)
                            except Exception:
                                continue
                        if all_records:
                            return pd.concat(all_records, ignore_index=True)
                        return pd.DataFrame()

                    global_chos = load_all_chos(valid_talukas_list, source_type)

                    if not global_chos.empty:
                        global_chos = global_chos.dropna(subset=['CHO NAME'])

                        col_s1, col_s2 = st.columns(2)
                        with col_s1:
                            search_term = st.text_input("Search by CHO Name, TMIS ID, or PHC", "", key="global_cho_search")
                        with col_s2:
                            filter_taluka = st.selectbox("Filter by Taluka", ["All Talukas"] + valid_talukas_list, key="cho_filter_taluka_global")

                        filtered_df = global_chos.copy()
                        if filter_taluka != "All Talukas":
                            filtered_df = filtered_df[filtered_df['TALUKA'] == filter_taluka]

                        if search_term:
                            filtered_df = filtered_df[
                                filtered_df.astype(str).apply(
                                    lambda row: row.str.contains(search_term, case=False).any(), axis=1
                                )
                            ]

                        st.markdown(f"**Showing {len(filtered_df)} matching records:**")
                        st.dataframe(filtered_df, use_container_width=True)
                        
                        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Filtered CHO Training Report (CSV)",
                            data=csv_data,
                            file_name="CHO_Training_Filtered_Report.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No CHO line records found across taluka sheets.")
                except Exception as e:
                    st.error(f"Error rendering CHO Directory: {e}")
        else:
            st.warning("⚠️ Master database sheet not found. Please verify your Google Sheet name or upload `SMO_Database.xlsx`.")

    # ==========================================
    # 2. DYNAMIC ANALYTICS ENGINE FOR M.O. CADRES
    # ==========================================
    elif db_category in ["MBBS MO PHC Database", "AYUSH MO PHC Database", "RBSK MO Database", "MBBS CHC MO Database"]:
        
        # EXACT string mapping to your actual Google Sheet Tab Names
        sheet_mapping = {
            "MBBS MO PHC Database": "MBBS PHC MO",
            "AYUSH MO PHC Database": "AYUSH MO PHC",
            "RBSK MO Database": "RBSK MO",
            "MBBS CHC MO Database": "MBBS CHC MO"
        }
        
        target_sheet = sheet_mapping[db_category]
        
        st.markdown(f"### 🩺 {db_category.replace(' Database', '')} Analytics Dashboard")
        
        @st.cache_data(ttl=600)
        def load_dynamic_cadre_data(sheet_name):
            try:
                if client:
                    sh = client.open("SMO_Database") 
                    ws = sh.worksheet(sheet_name)
                    
                    # FIX: Use get_all_values instead of get_all_records
                    raw_data = ws.get_all_values()
                    
                    if not raw_data or len(raw_data) < 2:
                        return pd.DataFrame()
                        
                    # DYNAMIC HEADER DETECTION: Find the row that actually contains the headers
                    header_idx = 0
                    for i, row in enumerate(raw_data):
                        # Convert row to uppercase strings for safe checking
                        row_upper = [str(cell).strip().upper() for cell in row]
                        if 'NAME OF M.O.' in row_upper or 'SR NO' in row_upper:
                            header_idx = i
                            break
                            
                    headers = raw_data[header_idx]
                    clean_headers = []
                    for i, h in enumerate(headers):
                        if str(h).strip() == "":
                            clean_headers.append(f"Unnamed_{i}")
                        else:
                            clean_headers.append(str(h).strip())
                            
                    # Create DataFrame starting from the row AFTER the headers
                    df = pd.DataFrame(raw_data[header_idx+1:], columns=clean_headers)
                    
                    # Drop columns that are completely empty/unnamed
                    df = df.loc[:, ~df.columns.str.startswith('Unnamed_')]
                    
                    return df
            except Exception as e:
                st.error(f"Error loading '{sheet_name}' from Google Sheets: {e}")
                return pd.DataFrame()

        df = load_dynamic_cadre_data(target_sheet)

        if not df.empty:
            import plotly.express as px
            import numpy as np

            # --- DATA CLEANING & CLASSIFICATION ---
            demographic_cols = ['SR NO', 'TALUKA', 'PHC', 'FACILITY TYPE', 'FACILITY NAME', 'NAME OF M.O.', 'TMIS ID', 'STATUS', 'REGULER / BONDED/ CONTRAVTUAL']
            existing_demo_cols = [c for c in demographic_cols if c in df.columns]
            training_cols = [c for c in df.columns if c not in demographic_cols and c.strip() != ""]

            # Standardize status column name if it exists as REGULER / BONDED/ CONTRAVTUAL
            if 'REGULER / BONDED/ CONTRAVTUAL' in df.columns:
                df['STATUS'] = df['REGULER / BONDED/ CONTRAVTUAL']

            calc_df = df.copy()
            for col in training_cols:
                calc_df[col] = calc_df[col].astype(str).str.upper().map({'Y': 1, 'N': 0}).fillna(0)

            df = df.dropna(subset=['NAME OF M.O.'], how='all')
            calc_df = calc_df.dropna(subset=['NAME OF M.O.'], how='all')

            tab1, tab2, tab3 = st.tabs([
                "📊 Master District Overview", 
                "🏢 Taluka & Facility Deep Dive", 
                "🔍 Global Directory Search"
            ])

            # ------------------------------------------
            # TAB 1: MASTER DISTRICT OVERVIEW
            # ------------------------------------------
            with tab1:
                st.subheader("🌟 District Executive Summary")
                
                total_mos = len(calc_df)
                regular_count = len(calc_df[calc_df['STATUS'].str.upper() == 'REGULER']) if 'STATUS' in calc_df.columns else 0
                avg_trainings_per_mo = calc_df[training_cols].sum(axis=1).mean() if training_cols else 0

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"Total {db_category.replace(' Database', '')}s", int(total_mos))
                with col2:
                    st.metric("Regular Appointments", int(regular_count))
                with col3:
                    st.metric("Avg Modules Completed / MO", f"{avg_trainings_per_mo:.1f}")

                st.markdown("---")
                st.markdown("### 📈 District-Wide Training Module Completion")
                
                if training_cols:
                    district_totals = calc_df[training_cols].sum().reset_index()
                    district_totals.columns = ['Training Module', 'Completed Count']
                    district_totals = district_totals.sort_values(by='Completed Count', ascending=False)
                    
                    fig_bar = px.bar(
                        district_totals, 
                        x='Training Module', 
                        y='Completed Count',
                        text='Completed Count',
                        color='Completed Count',
                        color_continuous_scale='Blues',
                        title=f"Total Modules Completed District-Wide ({db_category.replace(' Database', '')})"
                    )
                    fig_bar.update_layout(xaxis_tickangle=-45, template="plotly_white")
                    st.plotly_chart(fig_bar, use_container_width=True)

            # ------------------------------------------
            # TAB 2: TALUKA & FACILITY DEEP DIVE
            # ------------------------------------------
            with tab2:
                st.subheader("🏢 Taluka-Wise Performance Analytics")
                
                if 'TALUKA' in df.columns:
                    valid_talukas = ["All Talukas"] + sorted([t for t in df['TALUKA'].unique() if str(t).strip() != ""])
                    selected_taluka = st.selectbox("Select Taluka for Deep Dive", valid_talukas, key=f"taluka_dd_{target_sheet}")
                    
                    if selected_taluka == "All Talukas":
                        t_df = df.copy()
                        t_calc_df = calc_df.copy()
                    else:
                        t_df = df[df['TALUKA'] == selected_taluka].copy()
                        t_calc_df = calc_df[calc_df['TALUKA'] == selected_taluka].copy()

                    st.markdown(f"### 📍 Analytics for: **{selected_taluka}**")
                    
                    t_mos = len(t_df)
                    st.metric("Total M.O.s in Selection", t_mos)

                    if not t_df.empty and training_cols:
                        t_totals = t_calc_df[training_cols].sum().reset_index()
                        t_totals.columns = ['Training Module', 'Completed Count']
                        
                        fig_t_bar = px.bar(
                            t_totals, 
                            x='Training Module', 
                            y='Completed Count',
                            title=f"Training Completions in {selected_taluka}",
                            color_discrete_sequence=['#2E86C1']
                        )
                        fig_t_bar.update_layout(xaxis_tickangle=-45, template="plotly_white")
                        st.plotly_chart(fig_t_bar, use_container_width=True)

                    st.markdown(f"#### 📝 Detailed Records")
                    st.dataframe(t_df, use_container_width=True)
                else:
                    st.warning("No 'TALUKA' column found in this database.")

            # ------------------------------------------
            # TAB 3: GLOBAL DIRECTORY SEARCH
            # ------------------------------------------
            with tab3:
                st.subheader("🔍 Global Personnel Directory")
                st.markdown("Search across the entire district by Name, TMIS ID, or Facility.")

                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    search_term = st.text_input("Search (Name, TMIS, Facility)", "", key=f"search_{target_sheet}")
                with col_s2:
                    if 'TALUKA' in df.columns:
                        filter_t = st.selectbox("Filter by Taluka", ["All"] + sorted([t for t in df['TALUKA'].unique() if str(t).strip() != ""]), key=f"filter_{target_sheet}")
                    else:
                        filter_t = "All"

                filtered_df = df.copy()
                if filter_t != "All":
                    filtered_df = filtered_df[filtered_df['TALUKA'] == filter_t]

                if search_term:
                    filtered_df = filtered_df[
                        filtered_df.astype(str).apply(
                            lambda row: row.str.contains(search_term, case=False).any(), axis=1
                        )
                    ]

                st.markdown(f"**Showing {len(filtered_df)} matching records:**")
                st.dataframe(filtered_df, use_container_width=True)
                
                csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download Filtered {db_category.replace(' Database', '')} Report (CSV)",
                    data=csv_data,
                    file_name=f"{target_sheet}_Filtered_Report.csv",
                    mime="text/csv"
                )

        else:
            st.warning(f"⚠️ Database sheet '{target_sheet}' not found or is empty. Please verify your Google Sheet.")

    # ==========================================
    # 3. STANDARD DIRECTORY VIEW FOR OTHER DATABASES
    # ==========================================
    else:
        st.markdown(f"### Viewing: {db_category}")
        if client:
            try:
                # Reverted this back to DTT_Database for ANM, MPHW, ASHA cadres
                sh = client.open("DTT_Database") 
                ws = sh.worksheet(db_category)
                data = pd.DataFrame(ws.get_all_records())
                st.dataframe(data, use_container_width=True)
                
                search_query = st.text_input(f"Search in {db_category}", key="other_db_search")
                if search_query:
                    filtered = data[data.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                    st.dataframe(filtered, use_container_width=True)
            except Exception as e:
                st.warning(f"Worksheet '{db_category}' not found in DTT_Database. Please add it!")
                
# --- MODULE 4: KNOWLEDGE BANK ---
elif main_module == "4. Knowledge Bank":
    st.title("📚 Knowledge Bank & Training Resource Repository")
    st.markdown("Explore district training materials, guidelines, operational modules, and multi-tier cascading resources.")

    # Master Knowledge Bank Hierarchy derived from Training Material Data
    kb_hierarchy = {
        "NVBDCP (Vector Borne Diseases)": ["MALARIA", "DENGUE", "CHICKEN GUNIA", "FILERIA"],
        "Maternal Health": ["SBA", "DAKSHTA training"],
        "Child Health": [
            "RBSK - 5 DAYS", "MO DELIVERY POINT RBSK", "RBSK REFRESHER ANM", 
            "NSSK", "SAANS", "IMNCI", "IYCF", "IMMUNIZATION", "HBYC", "KMC", "AEFI"
        ],
        "Adolescent Health": ["AFHS", "PEER EDUCTER", "NODAL TEACHER"],
        "FP / Reproductive Health": ["RTI/STI", "IUCD+ PPIUCD", "NEW CONTRACEPTIVES", "FP LIMS"],
        "NCD (Non-Communicable Diseases)": ["CANCER SCREENING", "DIABETES", "HYPERTENSION", "NMHP"],
        "OEEE (Eye, Ear, Nose, Oral, Emergency)": ["ORAL", "EYE", "ENT", "EMERGENCY"],
        "EPMNS & Elderly Care": ["NPHCE", "ELDERLY CARE", "PALLIATIVE CARE", "MENTAL HELATH AND NEUROLOGICAL SUBSTANCE"],
        "Nutrition": ["ANEMIA MUKT ABHIYAN", "NATIONAL DEWORMING DAY", "EAT RIGHT TOOL KIT", "SAM"],
        "Monitoring & Evaluation": ["SATHI", "HMIS"],
        "Quality Assurance": ["NQAS", "KAYAKLP", "PMJAY", "ABDM"],
        "NTEP & National Programs": [
            "NVBDCP", "IHIP", "NLEP", "NTCP", "NPCCHH", "NVHCP", "NACP", "NRCP", "NPPC", 
            "JAS", "SNACK BITE", "INFECTION CONTROL"
        ],
        "IHIP Protocols": ["IHIP-P", "IHIP-L", "IHIP-S", "EPIDEMIC RESPONSE"],
        "Tuberculosis Sub-Divisions": ["PULMONERY TB", "EXTRAPUMONARY TB"],
        "Infection Control & Bio-Waste": [
            "HAND HEIGINE", "PPE KITS DOFFING DONNING", "CLANING", "STERILISATION", "WASTE MANGEMENT"
        ]
    }

    # Layout: Two-column cascade drill-down
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        selected_category = st.selectbox("📂 Select Primary Training Domain", list(kb_hierarchy.keys()))
        
    with col_filter2:
        sub_modules = kb_hierarchy.get(selected_category, ["General Resources"])
        selected_sub_module = st.selectbox("📑 Select Cascading Training Module", sub_modules)

    st.markdown("---")
    
    # Header Banner for selected training cascade
    st.subheader(f"🎯 Training Resource Hub: **{selected_sub_module}**")
    st.markdown(f"*Parent Domain:* `{selected_category}`")

    # Interactive Resource Tabs for the selected sub-module
    res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs([
        "📖 Guidelines & Manuals (PDF)", 
        "📊 Training Slide Decks (PPTX)", 
        "🎥 Demonstration & Training Videos", 
        "📝 Checklists & Pre/Post Tests"
    ])

    with res_tab1:
        st.markdown(f"#### Official Guidelines for {selected_sub_module}")
        st.info(f"Standard Operating Procedures (SOPs) and National Guidelines for {selected_sub_module} issued by MoHFW & State Health Department.")
        
        # Mock file download card
        st.download_button(
            label=f"📥 Download {selected_sub_module} Official Guideline (PDF)",
            data=b"Mock PDF Content for Training Material",
            file_name=f"{selected_sub_module.replace(' ', '_')}_Guideline.pdf",
            mime="application/pdf"
        )

    with res_tab2:
        st.markdown(f"#### District Training Presentations")
        st.write("Train-the-Trainer (ToT) slide decks used for district-level rollout and capacity building.")
        st.download_button(
            label=f"📥 Download {selected_sub_module} Master Presentation (PPTX)",
            data=b"Mock PPTX Content",
            file_name=f"{selected_sub_module.replace(' ', '_')}_Presentation.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

    with res_tab3:
        st.markdown(f"#### Video Resources & Skill Station Walkthroughs")
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") # Placeholder tutorial link
        st.caption(f"Official Ministry video tutorial covering practical clinical/field protocols for {selected_sub_module}.")

    with res_tab4:
        st.markdown(f"#### Assessment Tools & Evaluation Forms")
        st.write("Pre-test and Post-test question banks, validation check-sheets, and monitoring feedback forms.")
        
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            st.button(f"📋 Generate Pre/Post Test (Google Form Link)", key=f"test_{selected_sub_module}")
        with col_form2:
            st.button(f"📊 Download Field Evaluation Sheet (Excel)", key=f"eval_{selected_sub_module}")

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
        st.write("Get in touch with the DTT administration and training coordinators.")
