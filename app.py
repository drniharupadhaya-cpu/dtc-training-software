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

# --- MODULE 1: TRAINING SUMMARY (PHYSICAL & FINANCIAL TARGETS) ---
elif main_module == "1. Training Summary":
    st.title("📊 Training Summary & Physical Progress Dashboard")
    st.markdown("Comprehensive District Training Center (DTC) physical targets, monthly calendar execution, and achievement tracking.")

    # Data Loading Strategy (Google Sheets with Local Excel Fallback)
    @st.cache_data(ttl=600)
    def load_training_summary_data():
        try:
            if client:
                sh = client.open("DTT_Report_2025_26")
                ws = sh.worksheet("PHYSICAL")
                raw_data = ws.get_all_values()
                # Row 1 is header, Row 2 is monthly subheaders, Row 3+ is data
                headers = raw_data[1]
                data_rows = raw_data[3:] # Adjust based on exact row start
                summary_df = pd.DataFrame(data_rows, columns=headers)
                return summary_df, "gspread"
        except Exception:
            pass
        
        # Fallback to local Excel file
        try:
            excel_path = "@DTT REPORT 2025-26 SUMMERY  (6).xlsx"
            xls = pd.ExcelFile(excel_path)
            # Read raw to construct clean columns
            raw_df = pd.read_excel(xls, sheet_name="PHYSICAL", header=None)
            headers = [
                "New FMR", "Old FMR", "Particular", "Pool", "Program Division", 
                "Fund Allocation", "Target", "Apr", "May", "Jun", "Jul", 
                "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", 
                "TOTAL", "PENDING", "Col22", "Col23", "Col24"
            ]
            summary_df = raw_df.iloc[3:75].copy() # slicing valid data rows
            summary_df = summary_df.iloc[:, :21] # take first 21 relevant columns
            summary_df.columns = headers[:21]
            return summary_df, "excel"
        except Exception as e:
            st.error(f"Could not load Training Summary data source: {e}")
            return None, None

    summary_df, summary_source_type = load_training_summary_data()

    if summary_df is not None and not summary_df.empty:
        import plotly.express as px

        # Clean data: drop rows where Particular is NaN or empty
        summary_df = summary_df.dropna(subset=['Particular'])
        summary_df = summary_df[summary_df['Particular'] != 'TOTAL']

        # Ensure numeric columns are properly converted
        numeric_cols = ['Target', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'TOTAL', 'PENDING']
        for col in numeric_cols:
            if col in summary_df.columns:
                summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').fillna(0)

        # ------------------------------------------
        # KPI METRICS BAR
        # ------------------------------------------
        total_target = summary_df['Target'].sum() if 'Target' in summary_df.columns else 0
        total_achieved = summary_df['TOTAL'].sum() if 'TOTAL' in summary_df.columns else 0
        total_pending = summary_df['PENDING'].sum() if 'PENDING' in summary_df.columns else 0
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
            pools = ["All Pools"] + sorted(summary_df['Pool'].dropna().unique().tolist()) if 'Pool' in summary_df.columns else ["All Pools"]
            selected_pool = st.selectbox("Filter by Funding Pool", pools)
        with col_f2:
            divisions = ["All Divisions"] + sorted(summary_df['Program Division'].dropna().unique().tolist()) if 'Program Division' in summary_df.columns else ["All Divisions"]
            selected_div = st.selectbox("Filter by Program Division", divisions)

        filtered_summary = summary_df.copy()
        if selected_pool != "All Pools":
            filtered_summary = filtered_summary[filtered_summary['Pool'] == selected_pool]
        if selected_div != "All Divisions":
            filtered_summary = filtered_summary[filtered_summary['Program Division'] == selected_div]

        st.markdown("### 📈 Monthly Training Execution Timeline (F.Y. 2025-26)")
        
        months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
        monthly_totals = filtered_summary[months].sum().reset_index()
        monthly_totals.columns = ['Month', 'Completed Batches']

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
        st.warning("⚠️ Training summary data not found. Please verify your Google Sheet `DTT_Report_2025_26` or upload the Excel report.")

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

        # Data Loading Strategy for CHO Database (Cached master dataframe only)
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
                            # Re-open fresh gspread session to avoid expired session token errors
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
                
                search_query = st.text_input(f"Search in {db_category}", key="other_db_search")
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
