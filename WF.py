
import streamlit as st
import pandas as pd
import numpy as np


# ----------------- Global Styling -----------------
st.markdown("""
    <style>
        body, .css-18e3th9, .css-1d391kg {
            background-color: #1e1e1e !important;
            color: white !important;
        }
        .stButton > button {
            background-color: #ff4b2b;
            color: white;
            border: none;
            padding: 0.5rem 1.25rem;
            font-size: 1rem;
            border-radius: 6px;
        }
        .stButton > button:hover {
            background-color: #ff6b4b;
            transition: 0.3s;
        }
        .stTextInput > div > input,
        .stNumberInput input {
            background-color: #333 !important;
            color: white !important;
        }
        .stDataFrame, .stDataTable, .stMarkdown {
            color: white !important;
        }
        .st-expanderContent {
            background-color: #222 !important;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Recruiting Dashboard", layout="wide")

# ----------------- Load or initialize data -----------------
if "headcount_data" not in st.session_state:
    headcount_data = {
        "Allocation": [
            "Business", "Business", "Business", "Business", "Business", "Business", "Business", "Business", "Business",
            "Business", "Business", "Business", "Business", "Business", "Core R&D", "Core R&D", "Core R&D", "Core R&D",
            "Core R&D", "Core R&D", "Core R&D", "Machine Learning"
        ],
        "Sub-Dept": [
            "CS", "Customer Success & Solutions", "Marketing", "ProServ", "Sales", "Accounting", "Biz Ops & Prog Mgmt",
            "Finance", "Legal", "Ops & Admin", "Employee Experience", "People Operations", "Recruiting", "Workplace",
            "Allos", "COGS ops", "Eng", "G&A Biz sys", "Prod", "R&D biz sys", "Sales Biz sys", "Machine Learning"
        ],
        "Employees in seat": [115, 46, 82, 9, 175, 29, 6, 13, 7, 2, 16, 5, 27, 8, 12, 20, 204, 7, 89, 17, 7, 32],
        "Future Starts": [6, 13, 8, 3, 5, 3, 0, 7, 0, 0, 0, 0, 4, 1, 1, 1, 19, 1, 4, 0, 0, 1],
        "FY26 Planned + Open": [7, 17, 2, 0, 26, 1, 0, 0, 2, 2, 0, 0, 1, 0, 0, 6, 57, 3, 18, 1, 4, 0],
        "FY26 Planned - not yet opened": [4, 16, 40, 10, 18, 3, 1, 2, 0, 1, 1, 0, 2, 1, 0, 2, 15, 0, 6, 6, 1, 0]
    }
    df_headcount = pd.DataFrame(headcount_data)
    df_headcount["Total Headcount"] = df_headcount[
        ["Employees in seat", "Future Starts", "FY26 Planned + Open", "FY26 Planned - not yet opened"]
    ].sum(axis=1)
    st.session_state.headcount_data = df_headcount
    st.session_state.original_headcount = df_headcount.copy()

df_headcount = st.session_state.headcount_data
df_headcount["Total Headcount"] = df_headcount[
    ["Employees in seat", "Future Starts", "FY26 Planned + Open", "FY26 Planned - not yet opened"]
].sum(axis=1)

# ------------------ Augment Data with Function + Region ------------------
functions = {
    "CS": "Customer Success", "Customer Success & Solutions": "Customer Success", "Marketing": "Marketing",
    "ProServ": "Professional Services", "Sales": "Sales", "Accounting": "G&A", "Biz Ops & Prog Mgmt": "G&A",
    "Finance": "G&A", "Legal": "G&A", "Ops & Admin": "G&A", "Employee Experience": "G&A",
    "People Operations": "HR", "Recruiting": "HR", "Workplace": "G&A", "Allos": "R&D",
    "COGS ops": "R&D", "Eng": "R&D", "G&A Biz sys": "G&A", "Prod": "Product",
    "R&D biz sys": "R&D", "Sales Biz sys": "Sales", "Machine Learning": "R&D"
}
regions = ["US", "EMEA", "APAC"]
df_headcount["Function"] = df_headcount["Sub-Dept"].map(functions).fillna("Other")
df_headcount["Region"] = np.random.choice(regions, size=len(df_headcount))

df_allocation_summary = df_headcount.groupby("Allocation").sum(numeric_only=True).reset_index()
default_attrition_rates = {allocation: 0.10 for allocation in df_allocation_summary["Allocation"].unique()}
df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
    lambda row: row["Total Headcount"] * default_attrition_rates[row["Allocation"]],
    axis=1
)
df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

# ----------------- Sidebar Navigation -----------------
st.sidebar.title("Navigation")

page = st.sidebar.radio("Go to", [
    "Welcome to Pure Storage",
    "Headcount Adjustments",
    "Recruiter Capacity Model",
    "   └ Hiring Plan by Level",
    "   └ Hiring Speed Settings",
    "Finance Overview",
    "Success Metrics",
    "Forecasting"
])





# ----------------- Page: Hiring Plan by Level -----------------
if page == "   └ Hiring Plan by Level":
    st.title("📌 Hiring Plan by Level, Sub-Dept & Quarter")
    st.markdown("Define planned hires per level by department and quarter.")

    levels = list(range(1, 9))
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    subdept_df = df_headcount[["Allocation", "Sub-Dept"]].drop_duplicates().reset_index(drop=True)

    if "roles_by_level_subdept_quarter" not in st.session_state:
        st.session_state.roles_by_level_subdept_quarter = {
            (row["Allocation"], row["Sub-Dept"], q): {lvl: 0 for lvl in levels}
            for _, row in subdept_df.iterrows() for q in quarters
        }

    selected_alloc = st.selectbox("Select Allocation", subdept_df["Allocation"].unique())
    sub_options = subdept_df[subdept_df["Allocation"] == selected_alloc]["Sub-Dept"].unique()
    selected_sub = st.selectbox("Select Sub-Department", sub_options)
    selected_qtr = st.selectbox("Select Quarter", quarters)

    st.subheader(f"{selected_alloc} – {selected_sub} – {selected_qtr}")
    cols = st.columns(len(levels))
    for i, lvl in enumerate(levels):
        with cols[i]:
            key = f"{selected_alloc}_{selected_sub}_{selected_qtr}_L{lvl}"
            st.session_state.roles_by_level_subdept_quarter[(selected_alloc, selected_sub, selected_qtr)][lvl] = st.number_input(
                f"L{lvl}", min_value=0,
                value=st.session_state.roles_by_level_subdept_quarter[(selected_alloc, selected_sub, selected_qtr)][lvl],
                key=key
            )

    if st.checkbox("Show full hiring plan table"):
        full_table_data = []
        for (alloc, sub, qtr), level_counts in st.session_state.roles_by_level_subdept_quarter.items():
            full_table_data.append({
                "Allocation": alloc,
                "Sub-Dept": sub,
                "Quarter": qtr,
                **level_counts
            })
        df_roles_by_subdept_level = pd.DataFrame(full_table_data)
        st.dataframe(df_roles_by_subdept_level)
# ----------------- Page: Hiring Speed Settings -----------------
if page == "   └ Hiring Speed Settings":
    st.title("⏱️ Hiring Speed Settings by Sub-Department")
    st.markdown("Define time-to-hire expectations for different role levels per sub-department.")

    level_bands = {
        "L1–4": list(range(1, 5)),
        "L5–7": list(range(5, 8)),
        "L8–10": list(range(8, 11))
    }
    sub_depts = df_headcount["Sub-Dept"].unique().tolist()

    if "speed_settings" not in st.session_state:
        st.session_state.speed_settings = {
            dept: {band: 30 for band in level_bands} for dept in sub_depts
        }

    uploaded_file = st.file_uploader("Optional: Upload historical time-to-hire CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            hist_df = pd.read_csv(uploaded_file)
            for dept in sub_depts:
                dept_data = hist_df[hist_df["Sub-Dept"] == dept]
                for band_name, band_levels in level_bands.items():
                    band_data = dept_data[dept_data["Level"].isin(band_levels)]
                    if not band_data.empty:
                        avg_time = round(band_data["Time to Hire"].mean())
                        st.session_state.speed_settings[dept][band_name] = avg_time
            st.success("Historical time-to-hire data applied.")
        except Exception as e:
            st.error(f"Failed to process CSV: {e}")

    selected_dept = st.selectbox("Select a Department", sub_depts)
    st.subheader(selected_dept)

    cols = st.columns(len(level_bands))
    for i, (band, _) in enumerate(level_bands.items()):
        with cols[i]:
            key = f"{selected_dept}_{band}"
            st.session_state.speed_settings[selected_dept][band] = st.number_input(
                f"{band} (days)", min_value=1, max_value=180,
                value=st.session_state.speed_settings[selected_dept][band],
                step=1, key=key
            )

    st.success("Time-to-hire by sub-department and level band saved to state.")











# ----------------- Page: Recruiter Capacity Model -----------------
if page == "Recruiter Capacity Model":
    st.title("🧮 Recruiter Capacity by Quarter")
st.markdown("Assign recruiter headcount by sub-department. Filter by Allocation above the table.")

selected_filter_alloc = st.selectbox("Filter by Allocation", sorted(set(df_headcount["Allocation"].unique())))

    quarters = ["Q1", "Q2", "Q3", "Q4"]
    level_productivity = {1: 15, 2: 12, 3: 10, 4: 8, 5: 6, 6: 4, 7: 3, 8: 2}

    if "roles_by_level_subdept_quarter" not in st.session_state:
        st.warning("Please complete the Hiring Plan by Level first.")
    else:
        recruiter_rows = []

        all_keys = list(st.session_state.roles_by_level_subdept_quarter.keys())
        unique_sub_depts = sorted(set([(a, s) for (a, s, q) in all_keys]))

        if "recruiters_assigned_subdept" not in st.session_state:
            st.session_state.recruiters_assigned_subdept = {
                f"{a} – {s}": 1 for (a, s) in unique_sub_depts
            }

        alloc_groups = sorted(set([a for (a, s) in unique_sub_depts]))
        for alloc in alloc_groups:
            with st.expander(f"📁 {alloc}"):
                for (a, s) in sorted(unique_sub_depts):
                    if a == alloc:
                        label = f"{s}"
                        key = f"recruiters_{a}_{s}"
                        st.session_state.recruiters_assigned_subdept[f"{a} – {s}"] = st.number_input(
                            f"{label}", min_value=0,
                            value=st.session_state.recruiters_assigned_subdept.get(f"{a} – {s}", 1),
                            step=1, key=key
                        )

        for (alloc, sub) in unique_sub_depts:
            if alloc != selected_filter_alloc:
                continue
            sub_label = f"{alloc} – {sub}"
            assigned = st.session_state.recruiters_assigned_subdept[sub_label]
            for qtr in quarters:
                levels = st.session_state.roles_by_level_subdept_quarter.get((alloc, sub, qtr), {})
                total_roles = sum(levels.values())
                total_recruiters_needed = 0
                for lvl, count in levels.items():
                    if level_productivity.get(lvl, 1) > 0:
                        total_recruiters_needed += count / level_productivity[lvl]
                total_recruiters_needed = round(total_recruiters_needed, 2)
                status = "✅" if assigned >= total_recruiters_needed else f"❌ +{round(total_recruiters_needed - assigned, 2)}"
                recruiter_rows.append((alloc, sub, qtr, total_roles, total_recruiters_needed, assigned, status))

        df_recruiter_need = pd.DataFrame(recruiter_rows, columns=[
            "Allocation", "Sub-Dept", "Quarter", "Open Roles", "Recruiters Needed", "Recruiters Assigned", "Status"
        ])
        st.dataframe(df_recruiter_need, use_container_width=True)
# ----------------- Page: Forecasting -----------------
if page == "Forecasting":
    st.title("📈 Hiring Forecast")
    st.markdown("Uses hiring plan + time-to-hire settings to forecast recruiter velocity by Sub-Dept, Level, and Quarter.")

    level_bands = {
        "L1–4": list(range(1, 5)),
        "L5–7": list(range(5, 8)),
        "L8–10": list(range(8, 11))
    }

    if "roles_by_level_subdept_quarter" not in st.session_state or "speed_settings" not in st.session_state:
        st.warning("Please complete the 'Hiring Plan by Level' and 'Hiring Speed Settings' pages first.")
    else:
        forecast_rows = []
        for (alloc, sub, qtr), levels in st.session_state.roles_by_level_subdept_quarter.items():
            for lvl, count in levels.items():
                if count > 0:
                    band = next((b for b, lvls in level_bands.items() if lvl in lvls), "L1–4")
                    speed = st.session_state.speed_settings.get(sub, {}).get(band, 30)
                    velocity = round(90 / speed * count, 2)
                    forecast_rows.append((alloc, sub, qtr, lvl, count, speed, velocity))

        df_forecast = pd.DataFrame(forecast_rows, columns=[
            "Allocation", "Sub-Dept", "Quarter", "Level", "Planned Roles", "Time to Hire (days)", "Quarterly Hiring Velocity"
        ])
        st.dataframe(df_forecast, use_container_width=True)
# ----------------- Page: Headcount Adjustments -----------------
if page == "Headcount Adjustments":
    st.title("📊 Headcount Adjustments")
    st.markdown("Adjust headcount inputs across departments. Totals update in real time.")

    edited_df = st.data_editor(df_headcount, num_rows="dynamic")
    edited_df["Total Headcount"] = edited_df[
        ["Employees in seat", "Future Starts", "FY26 Planned + Open", "FY26 Planned - not yet opened"]
    ].sum(axis=1)
    st.session_state.headcount_data = edited_df

    df_allocation_summary = edited_df.groupby("Allocation").sum(numeric_only=True).reset_index()
    df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
        lambda row: row["Total Headcount"] * default_attrition_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

    
    st.subheader("📌 Summary by Allocation")

    manual_rates = {}
    for alloc in df_allocation_summary["Allocation"]:
        manual_rates[alloc] = st.number_input(f"Attrition Rate (%) for {alloc}", min_value=0.0, max_value=100.0,
                                              value=float(default_attrition_rates.get(alloc, 10.0)*100), step=0.1) / 100

    df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
        lambda row: row["Total Headcount"] * manual_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]
    st.dataframe(df_allocation_summary)


        # ----------------- Page: Adjusted Hiring Goals -----------------
if page == "Adjusted Hiring Goals":
    st.title("📈 Adjusted Hiring Goals")
    st.sidebar.subheader("Adjust Attrition Rate for Selected Allocation")
    selected_allocation = st.sidebar.selectbox("Choose Allocation", df_allocation_summary["Allocation"].unique())
    new_rate = st.sidebar.slider("Attrition Rate (%)", 0, 50, int(default_attrition_rates[selected_allocation] * 100), 1)
    default_attrition_rates[selected_allocation] = new_rate / 100

    df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
        lambda row: row["Total Headcount"] * default_attrition_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

    st.subheader("📌 Final Hiring Targets After Attrition")
    st.dataframe(df_allocation_summary)

    st.subheader("📉 Final Hiring Targets by Quarter (Line Chart)")
    chart_data = df_allocation_summary.copy()
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        chart_data[q] = chart_data["Final_Hiring_Target"] * 0.25
    df_long = chart_data.melt(id_vars="Allocation", value_vars=["Q1", "Q2", "Q3", "Q4"], var_name="Quarter", value_name="Hires")
    # --------------- Page 4: Finance Overview ----------------
if page == "Finance Overview":
    st.title("💰 Finance Overview")
    original_df = st.session_state.original_headcount
    current_df = st.session_state.headcount_data
    delta_df = current_df.copy()
    delta_df["Original Total"] = original_df["Total Headcount"]
    delta_df["Change"] = delta_df["Total Headcount"] - delta_df["Original Total"]
    delta_df["Approval Required"] = delta_df["Change"].apply(lambda x: "Yes" if x > 0 else "No")

    st.subheader("📊 Headcount Changes by Sub-Dept")
selected_finance_alloc = st.selectbox("Filter by Allocation", delta_df["Allocation"].unique())
filtered_finance = delta_df[delta_df["Allocation"] == selected_finance_alloc]
st.dataframe(filtered_finance[["Allocation", "Sub-Dept", "Original Total", "Total Headcount", "Change", "Approval Required"]])

    # --------------- Page 5: Success Metrics ----------------

# ----------------- Page: Success Metrics -----------------
if page == "Success Metrics":
    st.title("📊 Success Metrics & TA Benchmarks")

    metrics_data = {
        "Metric": [
            "Avg Hires per Recruiter per Quarter",
            "Sourcer-to-Recruiter Ratio",
            "Coordinator Load (Reqs per Coordinator)",
            "Avg Time-to-Fill (days)",
            "Offer Acceptance Rate (%)"
        ],
        "Current Value": ["9.3", "1.2:1", "18", "34", "86%"],
        "Benchmark": [">= 8", "1.5:1", "< 20", "< 40", ">= 85%"]
    }

    df_metrics = pd.DataFrame(metrics_data)
    st.dataframe(df_metrics)
    st.info("Benchmarks are general estimates. Customize to your organization as needed.")



# ----------------- Page: Welcome to Pure Storage -----------------
if page == "Welcome to Pure Storage":
    st.set_page_config(page_title="Workforce Planning Portal", layout="wide")

    st.markdown("""
        <style>
            body, .css-18e3th9, .css-1d391kg {
                background-color: #1e1e1e !important;
                color: white;
            }
            .stButton > button {
                background-color: #ff4b2b;
                color: white;
                border: none;
                padding: 0.5rem 1.25rem;
                font-size: 1rem;
                border-radius: 6px;
            }
            .stButton > button:hover {
                background-color: #ff6b4b;
                transition: 0.3s;
            }
            .stTextInput > div > input {
                background-color: #333;
                color: white;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='background: linear-gradient(90deg, #ff4b2b, #ff416c); padding: 2rem; border-radius: 0 0 20px 20px;'>
            <h1 style='color: white; font-size: 2.5rem;'>Welcome to the Workforce Planning Portal</h1>
            <p style='color: white; font-size: 1.1rem;'>This dashboard helps Talent Operations and Finance align on hiring needs, capacity planning, and recruiter deployment.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='padding: 2rem 0 1rem 0;'>
            <p style='color: white; font-size: 1.05rem;'>Use the sidebar to explore the hiring plan, adjust headcount goals, model recruiter demand by level and quarter, and review time-to-hire assumptions.</p>
            <p style='color: white; font-size: 1.05rem;'>Let’s build smarter, faster, and more strategically.</p>
        </div>
    """, unsafe_allow_html=True)
