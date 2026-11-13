import streamlit as st
import pandas as pd
import plotly.express as px

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

    q_tab1, q_tab2, q_tab3 = st.tabs(["📝 Interactive Practice Quiz", "📖 Master Question Bank & Key", "📊 Batch Analytics"])

    # --- MOCK DATA LOADER (Scalable for your 15 JSON/CSV files later) ---
    # For now, this loads the AMB sample. Later, you'll load from a JSON file based on 'selected_bank'
    sample_questions = [
        {
            "q": "6 માસ થી 59 માસ ના બાળક નું નોર્મલ HB (g/dl) કેટલું હોવું જોઈએ?",
            "options": {"અ": "11.00", "બ": "12.00", "ક": "13.00", "ડ": "11.5"},
            "answer": "અ"
        },
        {
            "q": "સગર્ભા બહેનોનું નોર્મલ HB (g/dl) કેટલું હોવું જોઈએ?",
            "options": {"અ": "11.00", "બ": "12.00", "ક": "13.00", "ડ": "11.5"},
            "answer": "અ"
        },
        {
            "q": "6 માસ થી 12 માસ ના બાળકોમાં હળવા અને મધ્યમ એનીમિયા ની સારવાર નીચે માથી એક છે.",
            "options": {"અ": "રોજ 1 ML Iron Folic ACID Syrup 2 માસ સુધી", "બ": "રોજ 2 ML Iron Folic ACID Syrup 2 માસ સુધી", "ક": "રોજ 1.5ML Iron Folic ACID Syrup 2 માસ સુધી", "ડ": "ઉપરમાં થી એક પણ નહી."},
            "answer": "અ"
        },
        {
            "q": "3 વર્ષ થી 5 વર્ષ સુધીના બાળકોમાં હળવા અને મધ્યમ એનીમિયા ની સારવાર નીચે માથી એક છે.",
            "options": {"અ": "રોજ 1 ML Iron Folic ACID Syrup 2 માસ સુધી", "બ": "રોજ 2 ML Iron Folic ACID Syrup 2 માસ સુધી", "ક": "રોજ 1.5ML Iron Folic ACID Syrup 2 માસ સુધી", "ડ": "ઉપરમાં થી એક પણ નહી."},
            "answer": "બ"
        }
    ]

    # --- TAB 1: INTERACTIVE QUIZ ---
    with q_tab1:
        st.markdown(f"### ⚡ Live Quiz Session: {selected_bank}")
        
        with st.form(key=f"quiz_form_{selected_bank}"):
            user_answers = {}
            for idx, item in enumerate(sample_questions):
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
                score = sum(1 for idx, item in enumerate(sample_questions) if user_answers[idx] == item['answer'])
                total = len(sample_questions)
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
        st.markdown(f"### 📖 Official Answer Key: {selected_bank}")
        for idx, item in enumerate(sample_questions):
            with st.expander(f"Q{idx+1}: {item['q']}"):
                for opt_key, opt_val in item['options'].items():
                    prefix = "✅ **[CORRECT]**" if opt_key == item['answer'] else "•"
                    st.markdown(f"{prefix} **{opt_key})** {opt_val}")

    # --- TAB 3: BATCH ANALYTICS ---
    with q_tab3:
        st.markdown(f"### 📊 District Analytics for {selected_bank}")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total Trainees Evaluated", "284")
        col_m2.metric("Average Score", "82.5%", "+5.4%")

        perf_data = pd.DataFrame({
            "Taluka": ["Junagadh Rural", "Visavadar", "Malia", "Keshod", "Mangrol", "Bhesan"],
            "Average Score (%)": [82, 79, 75, 88, 71, 80]
        })
        fig_q = px.bar(perf_data, x="Taluka", y="Average Score (%)", color="Average Score (%)", color_continuous_scale="Teal", title="Taluka-wise Average Score")
        st.plotly_chart(fig_q, use_container_width=True)
