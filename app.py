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

# Sidebar Navigation matching your CSV modules
st.sidebar.title("🏛️ DTT Navigation")
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
            sh = client.open("DTT_Database")
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
        ["CHO Database", "MO Database", "AYUSH MO Database", "RBSK MO Database", "ANM Database", "MPHW Database", "ASHA Database"]
    )
    
    # ==========================================
    # SPECIALIZED ANALYTICAL DASHBOARD FOR CHO DATABASE
    # ==========================================
    if db_category == "CHO Database":
        st.markdown("### 🌟 CHO Training & District Analytics Dashboard")
        st.markdown("Comprehensive analytics and directory for Community Health Officer (CHO) trainings across Junagadh District.")

        # Data Loading Strategy for CHO Database (Supports both Google Sheets and Local Excel Fallback)
        @st.cache_data(ttl=600)
        def load_cho_training_data():
            try:
                if client:
                    sh = client.open("SMO_Database")
                    master_df = pd.DataFrame(sh.worksheet("MASTER").get_all_records())
                    return sh, master_df, "gspread"
            except Exception:
                pass
            
            # Fallback to local Excel file if gspread isn't configured or fails
            try:
                excel_path = "SMO_Database.xlsx"
                xls = pd.ExcelFile(excel_path)
                master_df = pd.read_excel(xls, sheet_name="MASTER")
                return xls, master_df, "excel"
            except Exception as e:
                st.error(f"Could not load database source: {e}")
                return None, None, None

        data_source, master_df, source_type = load_cho_training_data()

        if master_df is not None:
            # Clean master df (keeping only valid taluka rows, dropping summary/pending rows for clean calc)
            valid_talukas_df = master_df.dropna(subset=['TALUKA']).copy()
            valid_talukas_df = valid_talukas_df[~valid_talukas_df['TALUKA'].isin(['TOTAL', 'TRAINING PENDING'])]

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
                st.subheader("🌟 District Executive Summary")
                
                total_aam = valid_talukas_df['AAM'].sum() if 'AAM' in valid_talukas_df.columns else 0
                total_cho = valid_talukas_df['CHO FILLED'].sum() if 'CHO FILLED' in valid_talukas_df.columns else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total AAM / HWCs", int(total_aam))
                with col2:
                    st.metric("Total CHOs Filled", int(total_cho))
                with col3:
                    training_cols = [c for c in valid_talukas_df.columns if c not in ['SR NO', 'TALUKA', 'AAM', 'CHO FILLED']]
                    avg_completion = valid_talukas_df[training_cols].mean().mean()
                    st.metric("Avg Module Completion", f"{avg_completion:.1f} CHOs/Taluka")

                st.markdown("---")
                st.markdown("### 📈 District-Wide Training Module Completion")
                
                district_totals = valid_talukas_df[training_cols].sum().reset_index()
                district_totals.columns = ['Training Module', 'Completed Count']
                
                import plotly.express as px
                fig_bar = px.bar(
                    district_totals, 
                    x='Training Module', 
                    y='Completed Count',
                    text='Completed Count',
                    color='Completed Count',
                    color_continuousScale='Viridis',
                    title="Total CHOs Completed per Training Module (District Level)"
                )
                fig_bar.update_layout(xaxis_tickangle=-45, template="plotly_white")
                st.plotly_chart(fig_bar, use_container_width=True)

                st.markdown("### 📋 District Master Summary Table")
                st.dataframe(master_df, use_container_width=True)

            # ------------------------------------------
            # TAB 2: TALUKA & PHC DEEP DIVE
            # ------------------------------------------
            with tab2:
                st.subheader("🏢 Taluka-Wise Performance Analytics")
                
                taluka_list = valid_talukas_df['TALUKA'].tolist()
                selected_taluka = st.selectbox("Select Taluka for Deep Dive", taluka_list)
                
                if selected_taluka:
                    try:
                        if source_type == "gspread":
                            ws_taluka = data_source.worksheet(selected_taluka)
                            raw_data = ws_taluka.get_all_values()
                            taluka_df = pd.DataFrame(raw_data[2:], columns=raw_data[0])
                        else:
                            taluka_raw = pd.read_excel(data_source, sheet_name=selected_taluka, header=None)
                            headers = taluka_raw.iloc[0].values
                            taluka_df = taluka_raw.iloc[2:].copy()
                            taluka_df.columns = headers

                        taluka_df = taluka_df.dropna(subset=['CHO NAME'], how='all')

                        st.markdown(f"### 📍 Analytics for Taluka: **{selected_taluka}**")
                        
                        t_hwcs = len(taluka_df)
                        t_chos = taluka_df['CHO NAME'].nunique()
                        
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
                        st.warning(f"Could not load data for Taluka '{selected_taluka}': {e}")

            # ------------------------------------------
            # TAB 3: CHO DIRECTORY & TRAINING SEARCH
            # ------------------------------------------
            with tab3:
                st.subheader("🔍 Global CHO Directory & Training Tracker")
                st.markdown("Search across all talukas for specific CHOs, TMIS IDs, or check individual training completion statuses.")

                @st.cache_data
                def load_all_chos(talukas, src, stype):
                    all_records = []
                    for tal in talukas:
                        try:
                            if stype == "gspread":
                                ws = src.worksheet(tal)
                                vals = ws.get_all_values()
                                if len(vals) > 2:
                                    t_df = pd.DataFrame(vals[2:], columns=vals[0])
                                    t_df['TALUKA'] = tal
                                    all_records.append(t_df)
                            else:
                                t_raw = pd.read_excel(src, sheet_name=tal, header=None)
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

                global_chos = load_all_chos(taluka_list, data_source, source_type)

                if not global_chos.empty:
                    global_chos = global_chos.dropna(subset=['CHO NAME'])

                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        search_term = st.text_input("Search by CHO Name, TMIS ID, or PHC", "")
                    with col_s2:
                        filter_taluka = st.selectbox("Filter by Taluka", ["All Talukas"] + taluka_list, key="cho_filter_taluka")

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
        else:
            st.warning("⚠️ Master database sheet not found. Please verify your Google Sheet name or upload `SMO_Database.xlsx`.")

    # ==========================================
    # STANDARD DIRECTORY VIEW FOR OTHER DATABASES
    # ==========================================
    else:
        st.markdown(f"### Viewing: {db_category}")
        if client:
            try:
                sh = client.open("DTT_Database")
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
        st.write("Get in touch with the DTT administration and training coordinators.")
