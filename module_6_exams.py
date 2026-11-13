import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

@st.cache_data
def load_question_bank(bank_name):
    # Mapping friendly dropdown names to your JSON filenames
    file_mapping = {
        "SAM Training Question Bank": "SAM_Question_Bank.json",
        # As you add more JSON files later, add them here!
        # "Anemia Mukt Bharat (AMB)": "AMB_Question_Bank.json",
    }
    
    filename = file_mapping.get(bank_name)
    if not filename:
        return None
        
    # Check both root folder and 'question_banks' folder for flexibility
    paths_to_try = [filename, os.path.join("question_banks", filename)]
    
    for filepath in paths_to_try:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                continue
                
    return None

def render_mock_exams_module():
    st.title("📝 Interactive Mock Exams & Question Banks")
    st.markdown("Select a training program to launch the interactive quiz module, review official question banks, or conduct live batch evaluations.")

    # Master list of your 15 program question banks
    program_banks = [
        "SAM Training Question Bank",
        "Anemia Mukt Bharat (AMB)",
        "ASHA & ASHA Facilitator",
        "National Leprosy Eradication (NLEP)",
        "NTEP (TB Elimination)",
        "NVBDCP (Vector Borne Diseases)",
        "Family Planning (FP) Protocols",
        "Immunization Training",
        "KMC & Breastfeeding (B.F.)",
        "DSO Surveillance & Outbreaks",
        "Biomedical Waste Management (BMW)",
        "PPIUCD / IUCD Training",
        "NSSK (Newborn Stabilization)",
        "SAANS (Pneumonia)",
        "Non-Communicable Diseases (NCD)"
    ]

    selected_bank = st.selectbox("📂 Select Training Program Question Bank:", program_banks)

    # Attempt to load questions from JSON file
    questions_data = load_question_bank(selected_bank)

    q_tab1, q_tab2, q_tab3 = st.tabs(["📝 Interactive Practice Quiz", "📖 Master Question Bank & Key", "📊 Batch Analytics"])

    if questions_data:
        # --- TAB 1: INTERACTIVE QUIZ ---
        with q_tab1:
            st.markdown(f"### ⚡ Live Quiz Session: {selected_bank}")
            
            with st.form(key=f"quiz_form_{selected_bank}"):
                user_answers = {}
                for idx, item in enumerate(questions_data):
                    st.markdown(f"**Q{idx+1}: {item['q']}**")
                    choice = st.radio(
                        f"Choose option for Q{idx+1}", 
                        options=list(item['options'].keys()), 
                        format_func=lambda x: f"{x}) {item['options'][x]}",
                        key=f"q_{selected_bank}_{idx}",
                        label_visibility="collapsed"
                    )
                    user_answers[idx] = choice
                    st.markdown("---")

                submitted = st.form_submit_button("🚀 Submit & Evaluate Score")
                if submitted:
                    score = sum(1 for idx, item in enumerate(questions_data) if user_answers[idx] == item['answer'])
                    total = len(questions_data)
                    percentage = (score / total) * 100
                    
                    if percentage >= 75:
                        st.success(f"🎉 Excellent Performance! You scored {score} out of {total} ({percentage:.1f}%)")
                        st.balloons()
                    elif percentage >= 40:
                        st.info(f"👍 Good Effort! You scored {score} out of {total} ({percentage:.1f}%)")
                    else:
                        st.warning(f"⚠️ Needs Revision. You scored {score} out of {total} ({percentage:.1f}%)")

        # --- TAB 2: MASTER KEY ---
        with q_tab2:
            st.markdown(f"### 📖 Official Answer Key & Explanations: {selected_bank}")
            for idx, item in enumerate(questions_data):
                with st.expander(f"Q{idx+1}: {item['q']}"):
                    for opt_key, opt_val in item['options'].items():
                        prefix = "✅ **[CORRECT]**" if opt_key == item['answer'] else "•"
                        st.markdown(f"{prefix} **{opt_key})** {opt_val}")
    else:
        # Placeholder message for modules whose JSON files aren't uploaded yet
        with q_tab1:
            st.info(f"📌 **{selected_bank}** JSON file is pending upload. Select **'SAM Training Question Bank'** from the dropdown above to test the fully interactive quiz right now!")
        with q_tab2:
            st.info(f"📌 Question bank and answer key for **{selected_bank}** will appear here once uploaded.")

    # --- TAB 3: BATCH ANALYTICS ---
    with q_tab3:
        st.markdown(f"### 📊 District Analytics for {selected_bank}")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total Trainees Evaluated", "142")
        col_m2.metric("Average District Score", "78.5%", "+12.4% vs Pre-Test")

        perf_data = pd.DataFrame({
            "Taluka": ["Junagadh Rural", "Visavadar", "Malia", "Keshod", "Mangrol", "Bhesan"],
            "Average Score (%)": [82, 79, 75, 84, 71, 77]
        })
        fig_q = px.bar(perf_data, x="Taluka", y="Average Score (%)", color="Average Score (%)", color_continuous_scale="Teal", title="Taluka-wise Average Assessment Score")
        st.plotly_chart(fig_q, use_container_width=True)
