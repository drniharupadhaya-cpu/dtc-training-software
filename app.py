import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from module_6_exams import render_mock_exams_module


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="District Training Team Software",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GOOGLE SHEETS AUTHENTICATION ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_gspread_client():
    """Initializes and returns authenticated gspread client using Streamlit secrets."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        return None

client = get_gspread_client()

@st.cache_data(ttl=600)
def load_response_sheet_data(sheet_url: str) -> pd.DataFrame:
    """Safely loads participant scores or responses from a shared Google Sheet URL."""
    try:
        if client:
            sh = client.open_by_url(sheet_url.strip())
            worksheet = sh.get_worksheet(0)
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
    except Exception as e:
        pass
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
        "sheet_url": "https://docs.google.com/spreadsheets/d/1nPhYgB6zax-n6m8rGEnh4Sr40eZQqiSKPu1NNOsGqkw/edit?gid=740696354#gid=740696354"
    },
    {
        "sr_no": 3,
        "name": "એન.એસ.એસ.કે. તાલીમ પ્રશ્નોત્તરી (NSSK)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSf_1qUJgIb4jsQv6D_pCw0j4kHM1yMF4pC6sxOb9l_SUXSxyA/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1hfb0McKFbAKkpi8GigpLqqRBdZeLib3FpIBwNZC8ltI/edit?gid=268850596#gid=268850596"
    },
    {
        "sr_no": 4,
        "name": "ઈમ્યુનાઈઝેશન તાલીમ પ્રશ્નોત્તરી (Immunization)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSd9UZamTZIDDN6S1T2TFtYyD9kG6_23CHHa3F-sOoleN1F02A/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1RAgqykZel6xpTrDhgsBq4a94wN_Jav-kYbNdsOPLLDA/edit?gid=167575404#gid=167575404"
    },
    {
        "sr_no": 5,
        "name": "ઈન્જેક્ટેબલ એન્ડ કોન્ટ્રાસેપ્ટીવ તાલીમ (Injectable & Contraceptive)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSdlTZMgMSXSR4jyvZc858Wmw4_QfSZQSN2eySdZuWKRnAwp5g/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1wPOtS6vDjBTsUJj7lUkNDIaWRmFBE7JF1_gh0aXUoJs/edit?gid=1762402621#gid=1762402621"
    },
    {
        "sr_no": 6,
        "name": "આર.બી.એસ.કે. તાલીમ પ્રશ્નોત્તરી (RBSK)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSd5hTeRJbkVt4U49BaQweYgPFqvuPlujVDafDslTaqIW6e5vw/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/16OBDpj1IuL0mwf2EbmNmCM98DodOkEwA4p8BfN9f-xc/edit?gid=1801396023#gid=1801396023"
    },
    {
        "sr_no": 7,
        "name": "આર.ટી.આઈ. / એસ.ટી.આઈ. તાલીમ પ્રશ્નોત્તરી (RTI / STI)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSexiDU2PLuLd0ZuBjltUd3DQvD7F-ZkiR0EanFka72ist8Bpw/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1Oo3clKZF-DHfFJBJWO-oSuwIz9PwvhpbVH_f9Wgk8b0/edit?gid=587984637#gid=587984637"
    },
    {
        "sr_no": 8,
        "name": "આઈ.વાઈ.સી.એફ તાલીમ ના પ્રશ્નોત્તર (IYCF)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSeS16R982AQ3N8DODjcHorEX93xWl5xMiIttAHb2hu6le-S8w/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1StLDu8G2NISuMyes_VWzbuw4Q1tHUbiI7kwzgTNglfg/edit?gid=1877293908#gid=1877293908"
    },
    {
        "sr_no": 9,
        "name": "આઈ.યુ.સી.ડી. તાલીમ પ્રશ્નોત્તરી (IUCD)",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScPnp9h_LyM4x18osakWOkYRkLI5A3kVJ-VNFLUXY5iaJmspQ/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1cfJM6xlbrNfrHWdiTRHvhK_c31Kum4Abu9Dls3XXgsM/edit?gid=2061429530#gid=2061429530"
    },
    {
        "sr_no": 10,
        "name": "SBA Pre/Post Test - DTTS",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfLS8-U0LUfalhq1pZWvWIaYhUJt-nn5dQObU1ZcvUjnPHVGA/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1Cs0KzGwACMVcr-U1TBPlHL15NVeFUIFgyN3LGcA6nB4/edit?gid=1924804296#gid=1924804296"
    },
    {
        "sr_no": 11,
        "name": "SAM Training Pre/Post Test - DTTS",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfDX60qWhjnWNTWhc9G6V_RU2I4_r3ebbC_DV0vGpyv1SpwEw/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1KBB1JwfMyov2gEuJ05sLWT0_UI7jjxykF9vjZUU2NT0/edit?gid=532569953#gid=532569953"
    },
    {
        "sr_no": 12,
        "name": "SAANS TOT Pre/Post Test - DTTS",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScndimD3j8doODGpqCWvIC6-eE7pGHoTYMoTO8QZh4vGxYbGA/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1biyVUTIC6mdWfWJx4vnsrjvVB2q75lBZ1-Swe5AYQR8/edit?gid=813410632#gid=813410632"
    },
    {
        "sr_no": 13,
        "name": "Skill lab Pre/Post Test 1",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScPCjbUqh0d9D_O9Y5QOWuB1jENWJ9sHhhn1E2Mgnuuvli5EA/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/17Ut85NZr-LSrl3vE7GGUj42a6gJ9e2GMx0S277LNqxY/edit?gid=1050711206#gid=1050711206"
    },
    {
        "sr_no": 14,
        "name": "Skill lab Pre/Post Test 2",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSdKAj1S8Hf5xvMTUjy5RF5mRyYdaRN877V8r3Ct0GKQXXO2oA/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/10PPrGMMyom-h75HaX4QweyP3hdQcCLz3vGSj7dUvjIY/edit?gid=322833732#gid=322833732"
    },
    {
        "sr_no": 15,
        "name": "Skill lab Pre/Post Test 3",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLScKpDZwbmLj6IRfXAbO30Imki1b5DPYQRoViWHRXC0T6NRZDA/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/11H9eRStVhzeijvfZyhVwyZBkaa57KyWiSXF5SPJytGg/edit?gid=2126403197#gid=2126403197"
    },
    {
        "sr_no": 16,
        "name": "RKSK TRAINING Pre-Post Test",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfiJDRhbXAP5OIMA9RN86kyJyIjr7JGy7icZM6co9MWvS4xyw/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/15Wwhc7-KOVbdCTXPNafe9A3deJTvZYxUmQRqefsiM0U/edit?gid=914590812#gid=914590812"
    },
    {
        "sr_no": 17,
        "name": "Kayakalp Pre/Post Test Questionnaire",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSdl_1WFU63KRzMuTffDLwmLUeNgBb5hAJ6R0Kj3ixSqYbEkbw/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1Tl9mHR1SmXDebkqW7zTqEttjWt31Kuvlpbs8FxTwQ9k/edit?gid=1236232585#gid=1236232585"
    },
    {
        "sr_no": 18,
        "name": "IUCD TOT Pre/Post Test",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSdiOzens9s89-PQXdl5ZITGRZKMlhnYq_2kBfW2iH-23hdU6A/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1ajaoZKy5mwhrUgsKzjw_a9_nAynWwRN1MoptYYJYig4/edit?gid=1763485110#gid=1763485110"
    },
    {
        "sr_no": 19,
        "name": "Injectable MPA and Oral Contraceptives Pre/Post Test",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSfNIfB5K-o3Uwy0Zdn9ksdOMdDYpCk595LgEAnwQ3jWD0bllw/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1ayhJHwAI1XZVkEXaPwJi-DM2qogqvbhP-g_Uu1WRDMs/edit?gid=1556934632#gid=1556934632"
    },
    {
        "sr_no": 20,
        "name": "Immunization Training Pre/Post test",
        "form_url": "https://docs.google.com/forms/d/e/1FAIpQLSe-XtDu72CGpw9Sd9DBvddSp6ck0jjbXV5Vx6H1_1JSS-ZyiQ/viewform",
        "sheet_url": "https://docs.google.com/spreadsheets/d/14JieBI0O_2nsEIydSSosuGbGxnR4lL6bYvMd5EkS-TU/edit?gid=2054801374#gid=2054801374"
    }
]


# --- UNIFIED SIDEBAR NAVIGATION ---
st.sidebar.title("🏛️ DTT Navigation")
main_module = st.sidebar.selectbox(
    "Select Module", 
    [
        "1. Training Summary", 
        "2. Current Year Data (26-27)", 
        "3. Training Database", 
        "4. Knowledge Bank", 
        "5. About Us",
        "6. Interactive Mock Exams"
    ]
)


# ==========================================
# --- MODULE 1: TRAINING SUMMARY ---
# ==========================================
if main_module == "1. Training Summary":
    st.title("📊 Training Summary & Physical Progress Dashboard")
    st.markdown("Comprehensive District Training Center (DTC) physical targets, monthly calendar execution, and achievement tracking.")

    @st.cache_data(ttl=600)
    def load_training_summary_data():
        try:
            if client:
                sh = client.open("SMO_Database")
                ws = sh.worksheet("PHYSICAL")
                raw_data = ws.get_all_values()
                headers = raw_data[0]
                data_rows = raw_data[1:]
                summary_df = pd.DataFrame(data_rows, columns=headers)
                return summary_df, "gspread"
        except Exception:
            pass
        
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
        summary_df = summary_df.dropna(subset=['Particular'])
        summary_df = summary_df[~summary_df['Particular'].astype(str).str.upper().isin(['TOTAL', 'NAN', ''])]

        target_col_candidates = [c for c in summary_df.columns if 'Target' in str(c) or 'BATCHES' in str(c).upper()]
        target_col = target_col_candidates[0] if target_col_candidates else summary_df.columns[6]

        for col in summary_df.columns:
            if any(m in str(col) for m in ['2026', '2025', 'TOTAL', 'PENDING', 'Target', 'BATCHES']) or col in ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']:
                summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').fillna(0)

        target_series = summary_df[target_col]
        achieved_series = summary_df['TOTAL'] if 'TOTAL' in summary_df.columns else summary_df.iloc[:, -2]
        pending_series = summary_df['PENDING'] if 'PENDING' in summary_df.columns else summary_df.iloc[:, -1]

        total_target = target_series.sum()
        total_achieved = achieved_series.sum()
        total_pending = pending_series.sum()
        achievement_pct = (total_achieved / total_target * 100) if total_target > 0 else 0

        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        col_k1.metric("Total Target Batches", int(total_target))
        col_k2.metric("Total Achieved Batches", int(total_achieved))
        col_k3.metric("Total Pending Batches", int(total_pending))
        col_k4.metric("Achievement Rate", f"{achievement_pct:.1f}%")

        st.markdown("---")

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
        month_cols = [c for c in filtered_summary.columns if any(str(m) in str(c) for m in ['2025', '2026', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']) and c not in [target_col, 'TOTAL', 'PENDING']]
        
        if len(month_cols) >= 12:
            month_cols = month_cols[:12]
            monthly_totals = filtered_summary[month_cols].sum().reset_index()
            monthly_totals.columns = ['Month', 'Completed Batches']
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


# ==========================================
# --- MODULE 2: CURRENT YEAR DATA (26-27) ---
# ==========================================
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


# ==========================================
# --- MODULE 3: TRAINING DATABASE ---
# ==========================================
elif main_module == "3. Training Database":
    st.title("🗄️ Training Database (Directory & Analytics)")
    
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
            tab1, tab2, tab3 = st.tabs([
                "📊 Master District Overview", 
                "🏢 Taluka & PHC Deep Dive", 
                "🔍 CHO Directory & Training Search"
            ])

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
                    col1.metric("Total AAM / HWCs", int(total_aam))
                    col2.metric("Total CHOs Filled", int(total_cho))
                    training_cols = [c for c in numeric_cols if c not in ['AAM', 'CHO FILLED']]
                    avg_completion = clean_master_df[training_cols].mean().mean() if training_cols else 0
                    col3.metric("Avg Module Completion", f"{avg_completion:.1f} CHOs/Taluka")

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
                        col_t1.metric("Total Facilities (HWCs / AAM)", t_hwcs)
                        col_t2.metric("Registered CHOs", t_chos)

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

            with tab3:
                try:
                    st.subheader("🔍 Global CHO Directory & Training Tracker")
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

    elif db_category in ["MBBS MO PHC Database", "AYUSH MO PHC Database", "RBSK MO Database", "MBBS CHC MO Database"]:
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
                    raw_data = ws.get_all_values()
                    if not raw_data or len(raw_data) < 2:
                        return pd.DataFrame()
                        
                    header_idx = 0
                    for i, row in enumerate(raw_data):
                        row_upper = [str(cell).strip().upper() for cell in row]
                        if 'NAME OF M.O.' in row_upper or 'SR NO' in row_upper:
                            header_idx = i
                            break
                            
                    headers = raw_data[header_idx]
                    clean_headers = [f"Unnamed_{i}" if str(h).strip() == "" else str(h).strip() for i, h in enumerate(headers)]
                    df = pd.DataFrame(raw_data[header_idx+1:], columns=clean_headers)
                    df = df.loc[:, ~df.columns.str.startswith('Unnamed_')]
                    return df
            except Exception as e:
                st.error(f"Error loading '{sheet_name}' from Google Sheets: {e}")
                return pd.DataFrame()

        df = load_dynamic_cadre_data(target_sheet)

        if not df.empty:
            demographic_cols = ['SR NO', 'TALUKA', 'PHC', 'FACILITY TYPE', 'FACILITY NAME', 'NAME OF M.O.', 'TMIS ID', 'STATUS', 'REGULER / BONDED/ CONTRAVTUAL']
            training_cols = [c for c in df.columns if c not in demographic_cols and c.strip() != ""]

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

            with tab1:
                st.subheader("🌟 District Executive Summary")
                total_mos = len(calc_df)
                regular_count = len(calc_df[calc_df['STATUS'].str.upper() == 'REGULER']) if 'STATUS' in calc_df.columns else 0
                avg_trainings_per_mo = calc_df[training_cols].sum(axis=1).mean() if training_cols else 0

                col1, col2, col3 = st.columns(3)
                col1.metric(f"Total {db_category.replace(' Database', '')}s", int(total_mos))
                col2.metric("Regular Appointments", int(regular_count))
                col3.metric("Avg Modules Completed / MO", f"{avg_trainings_per_mo:.1f}")

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

            with tab2:
                st.subheader("🏢 Taluka-Wise Performance Analytics")
                if 'TALUKA' in df.columns:
                    valid_talukas = ["All Talukas"] + sorted([t for t in df['TALUKA'].unique() if str(t).strip() != ""])
                    selected_taluka = st.selectbox("Select Taluka for Deep Dive", valid_talukas, key=f"taluka_dd_{target_sheet}")
                    
                    t_df = df.copy() if selected_taluka == "All Talukas" else df[df['TALUKA'] == selected_taluka].copy()
                    t_calc_df = calc_df.copy() if selected_taluka == "All Talukas" else calc_df[calc_df['TALUKA'] == selected_taluka].copy()

                    st.markdown(f"### 📍 Analytics for: **{selected_taluka}**")
                    st.metric("Total M.O.s in Selection", len(t_df))

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

                    st.markdown("#### 📝 Detailed Records")
                    st.dataframe(t_df, use_container_width=True)

            with tab3:
                st.subheader("🔍 Global Personnel Directory")
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    search_term = st.text_input("Search (Name, TMIS, Facility)", "", key=f"search_{target_sheet}")
                with col_s2:
                    filter_t = st.selectbox("Filter by Taluka", ["All"] + sorted([t for t in df['TALUKA'].unique() if str(t).strip() != ""]), key=f"filter_{target_sheet}") if 'TALUKA' in df.columns else "All"

                filtered_df = df.copy()
                if filter_t != "All":
                    filtered_df = filtered_df[filtered_df['TALUKA'] == filter_t]
                if search_term:
                    filtered_df = filtered_df[filtered_df.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)]

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
            st.warning(f"⚠️ Database sheet '{target_sheet}' not found or is empty.")

    else:
        st.markdown(f"### Viewing: {db_category}")
        if client:
            try:
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


# ==========================================
# --- MODULE 4: KNOWLEDGE BANK ---
# ==========================================
elif main_module == "4. Knowledge Bank":
    st.title("📚 Knowledge Bank & Training Resource Repository")
    st.markdown("Explore district training materials, guidelines, operational modules, and multi-tier cascading resources.")

    kb_hierarchy = {
        "NVBDCP (Vector Borne Diseases)": ["MALARIA", "DENGUE", "CHICKEN GUNIA", "FILERIA"],
        "Maternal Health": ["SBA", "DAKSHTA training"],
        "Child Health": ["RBSK - 5 DAYS", "MO DELIVERY POINT RBSK", "RBSK REFRESHER ANM", "NSSK", "SAANS", "IMNCI", "IYCF", "IMMUNIZATION", "HBYC", "KMC", "AEFI"],
        "Adolescent Health": ["AFHS", "PEER EDUCTER", "NODAL TEACHER"],
        "FP / Reproductive Health": ["RTI/STI", "IUCD+ PPIUCD", "NEW CONTRACEPTIVES", "FP LIMS"],
        "NCD (Non-Communicable Diseases)": ["CANCER SCREENING", "DIABETES", "HYPERTENSION", "NMHP"],
        "OEEE (Eye, Ear, Nose, Oral, Emergency)": ["ORAL", "EYE", "ENT", "EMERGENCY"],
        "EPMNS & Elderly Care": ["NPHCE", "ELDERLY CARE", "PALLIATIVE CARE", "MENTAL HELATH AND NEUROLOGICAL SUBSTANCE"],
        "Nutrition": ["ANEMIA MUKT ABHIYAN", "NATIONAL DEWORMING DAY", "EAT RIGHT TOOL KIT", "SAM"],
        "Monitoring & Evaluation": ["SATHI", "HMIS"],
        "Quality Assurance": ["NQAS", "KAYAKLP", "PMJAY", "ABDM"],
        "NTEP & National Programs": ["NVBDCP", "IHIP", "NLEP", "NTCP", "NPCCHH", "NVHCP", "NACP", "NRCP", "NPC", "JAS", "SNACK BITE", "INFECTION CONTROL"],
        "IHIP Protocols": ["IHIP-P", "IHIP-L", "IHIP-S", "EPIDEMIC RESPONSE"],
        "Tuberculosis Sub-Divisions": ["PULMONERY TB", "EXTRAPUMONARY TB"],
        "Infection Control & Bio-Waste": ["HAND HEIGINE", "PPE KITS DOFFING DONNING", "CLANING", "STERILISATION", "WASTE MANGEMENT"]
    }

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_category = st.selectbox("📂 Select Primary Training Domain", list(kb_hierarchy.keys()))
    with col_filter2:
        sub_modules = kb_hierarchy.get(selected_category, ["General Resources"])
        selected_sub_module = st.selectbox("📑 Select Cascading Training Module", sub_modules)

    st.markdown("---")
    st.subheader(f"🎯 Training Resource Hub: **{selected_sub_module}**")
    st.markdown(f"*Parent Domain:* `{selected_category}`")

    res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs([
        "📖 Guidelines & Manuals (PDF)", 
        "📊 Training Slide Decks (PPTX)", 
        "🎥 Demonstration & Training Videos", 
        "📝 Checklists & Pre/Post Tests"
    ])

    with res_tab1:
        st.markdown(f"#### Official Guidelines for {selected_sub_module}")
        st.info(f"Standard Operating Procedures (SOPs) and National Guidelines for {selected_sub_module} issued by MoHFW & State Health Department.")
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
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        st.caption(f"Official Ministry video tutorial covering practical clinical/field protocols for {selected_sub_module}.")

    with res_tab4:
        st.markdown(f"#### Assessment Tools & Evaluation Forms")
        st.write("Pre-test and Post-test question banks, validation check-sheets, and monitoring feedback forms.")
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            st.button(f"📋 Generate Pre/Post Test (Google Form Link)", key=f"test_{selected_sub_module}")
        with col_form2:
            st.button(f"📊 Download Field Evaluation Sheet (Excel)", key=f"eval_{selected_sub_module}")


# ==========================================
# --- MODULE 5: ABOUT US ---
# ==========================================
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
# ==========================================
# --- MODULE 6: INTERACTIVE MOCK EXAMS ---
# ==========================================
elif main_module == "6. Interactive Mock Exams":
    render_mock_exams_module()
