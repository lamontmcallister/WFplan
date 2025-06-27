
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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
    "Adjusted Hiring Goals",
    "Hiring Plan by Level",
    "Recruiter Capacity Model",
    "Finance Overview",
    "Hiring Speed Settings",
    "Success Metrics",
    "Forecasting"
])



# ----------------- Page: Hiring Plan by Level -----------------
if page == "Hiring Plan by Level":
    st.title("📌 Hiring Plan by Level & Sub-Department")
    st.markdown("Select an allocation and sub-department to define role counts per level.")

    levels = list(range(1, 9))
    subdept_df = df_headcount[["Allocation", "Sub-Dept"]].drop_duplicates().reset_index(drop=True)

    if "roles_by_level_subdept" not in st.session_state:
        st.session_state.roles_by_level_subdept = {
            (row["Allocation"], row["Sub-Dept"]): {lvl: 0 for lvl in levels}
            for _, row in subdept_df.iterrows()
        }

    selected_alloc = st.selectbox("Select Allocation", subdept_df["Allocation"].unique())
    sub_options = subdept_df[subdept_df["Allocation"] == selected_alloc]["Sub-Dept"].unique()
    selected_sub = st.selectbox("Select Sub-Department", sub_options)

    st.subheader(f"{selected_alloc} – {selected_sub}")
    cols = st.columns(len(levels))
    for i, lvl in enumerate(levels):
        with cols[i]:
            key = f"{selected_alloc}_{selected_sub}_L{lvl}"
            st.session_state.roles_by_level_subdept[(selected_alloc, selected_sub)][lvl] = st.number_input(
                f"L{lvl}", min_value=0, value=st.session_state.roles_by_level_subdept[(selected_alloc, selected_sub)][lvl], key=key
            )

    if st.checkbox("Show full hiring plan table"):
        full_table_data = []
        for (alloc, sub), levels in st.session_state.roles_by_level_subdept.items():
            full_table_data.append({
                "Allocation": alloc,
                "Sub-Dept": sub,
                **levels
            })
        df_roles_by_subdept_level = pd.DataFrame(full_table_data)
        st.dataframe(df_roles_by_subdept_level)


# ----------------- Page: Hiring Speed Settings -----------------
if page == "Hiring Speed Settings":
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

    for dept in sub_depts:
        st.subheader(dept)
        cols = st.columns(len(level_bands))
        for i, (band, _) in enumerate(level_bands.items()):
            with cols[i]:
                key = f"{dept}_{band}"
                st.session_state.speed_settings[dept][band] = st.number_input(
                    f"{band} (days)", min_value=1, max_value=180, value=st.session_state.speed_settings[dept][band],
                    step=1, key=key
                )

    st.success("Time-to-hire by sub-department and level band saved to state.")







# ----------------- Page: Recruiter Capacity Model -----------------
if page == "Recruiter Capacity Model":
    st.title("🧮 Recruiter Capacity by Quarter (Enhanced)")
    st.markdown("Estimate recruiter need based on quarter, role level, and productivity by department.")

    quarters = ["Q1", "Q2", "Q3", "Q4"]
    level_productivity = {1: 15, 2: 12, 3: 10, 4: 8, 5: 6, 6: 4, 7: 3, 8: 2}

    if "roles_by_level_subdept" not in st.session_state:
        st.warning("Please complete the Hiring Plan by Level first.")
    else:
        show_all = st.checkbox("Show full recruiter needs by department and quarter", value=False)
        recruiter_rows = []

        all_sub_depts = list(st.session_state.roles_by_level_subdept.keys())
        sub_options = [f"{a} – {s}" for (a, s) in all_sub_depts]

        if not show_all:
            selected = st.selectbox("Select Allocation – Sub-Department", sub_options)
            selected_alloc, selected_sub = selected.split(" – ")
            sub_list = [(selected_alloc, selected_sub)]
        else:
            sub_list = all_sub_depts

        for (alloc, sub) in sub_list:
            levels = st.session_state.roles_by_level_subdept[(alloc, sub)]
            total_roles = sum(levels.values())

            q_weights = [0.25, 0.25, 0.25, 0.25]
            if not show_all:
                col1, col2 = st.columns(2)
                with col1:
                    assigned = st.number_input(f"{sub} - Recruiters Assigned", min_value=0, value=1, key=f"assigned_{sub}")
                with col2:
                    for i, q in enumerate(quarters):
                        q_weights[i] = st.number_input(f"{sub} {q} %", min_value=0.0, max_value=1.0, value=0.25, step=0.01, key=f"{sub}_{q}_dist")
            else:
                assigned = 1

            for q, q_pct in zip(quarters, q_weights):
                q_roles = total_roles * q_pct
                total_recruiters_needed = 0
                for lvl, count in levels.items():
                    q_lvl_roles = count * q_pct
                    if level_productivity.get(lvl, 1) > 0:
                        total_recruiters_needed += q_lvl_roles / level_productivity[lvl]
                total_recruiters_needed = round(total_recruiters_needed, 2)
                status = "✅" if assigned >= total_recruiters_needed else f"❌ +{round(total_recruiters_needed - assigned, 2)}"
                recruiter_rows.append((alloc, sub, q, round(q_roles), round(total_recruiters_needed, 2), assigned, status))

        df_recruiter_need = pd.DataFrame(recruiter_rows, columns=["Allocation", "Sub-Dept", "Quarter", "Open Roles", "Recruiters Needed", "Assigned", "Status"])
        st.dataframe(df_recruiter_need, use_container_width=True)


# ----------------- Page: Forecasting -----------------
if page == "Forecasting":
    st.title("📈 Hiring Forecast")
    st.markdown("Uses hiring plan + time-to-hire settings to forecast recruiter velocity by Sub-Dept and Level.")

    level_bands = {
        "L1–4": list(range(1, 5)),
        "L5–7": list(range(5, 8)),
        "L8–10": list(range(8, 11))
    }

    if "roles_by_level_subdept" not in st.session_state or "speed_settings" not in st.session_state:
        st.warning("Please complete the 'Hiring Plan by Level' and 'Hiring Speed Settings' pages first.")
    else:
        forecast_rows = []
        for (alloc, sub), levels in st.session_state.roles_by_level_subdept.items():
            for lvl, count in levels.items():
                if count > 0:
                    # Determine band
                    band = next((b for b, lvls in level_bands.items() if lvl in lvls), "L1–4")
                    speed = st.session_state.speed_settings.get(sub, {}).get(band, 30)
                    velocity = round(30 / speed * count, 2)
                    forecast_rows.append((alloc, sub, lvl, count, speed, velocity))

        df_forecast = pd.DataFrame(forecast_rows, columns=[
            "Allocation", "Sub-Dept", "Level", "Planned Roles", "Time to Hire (days)", "Monthly Hiring Velocity"
        ])
        st.dataframe(df_forecast, use_container_width=True)
        st.info("Velocity is an estimate of how many roles can be filled monthly based on current hiring speed.")



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
    st.dataframe(df_allocation_summary)

    st.subheader("📈 Hiring Goals by Quarter (Line Chart)")
    chart_data = df_allocation_summary.copy()
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        chart_data[q] = chart_data["Final_Hiring_Target"] * 0.25
    df_long = chart_data.melt(id_vars="Allocation", value_vars=["Q1", "Q2", "Q3", "Q4"], var_name="Quarter", value_name="Hires")
    fig = px.line(df_long, x="Quarter", y="Hires", color="Allocation", markers=True, title="Quarterly Hiring Goals by Allocation")
    st.plotly_chart(fig, use_container_width=True)


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
    fig = px.line(df_long, x="Quarter", y="Hires", color="Allocation", markers=True, title="Final Hiring Targets by Quarter")
    st.plotly_chart(fig, use_container_width=True)


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
    st.dataframe(delta_df[["Allocation", "Sub-Dept", "Original Total", "Total Headcount", "Change", "Approval Required"]])

    st.subheader("📉 Change Summary (Bar Chart)")
    fig = px.bar(delta_df, x="Sub-Dept", y="Change", color="Allocation", title="Headcount Change vs Original Plan")
    st.plotly_chart(fig)


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
    st.title("📊 Pure Storage Workforce Planning Dashboard")
    st.markdown("""
    Welcome to the Pure Storage capacity model.  
    This dashboard helps Talent Operations and Finance align on hiring needs, capacity planning, and recruiter deployment.

    Use the sidebar to explore the hiring plan, adjust headcount goals, model recruiter demand by level and quarter, and review time-to-hire assumptions.

    _Let’s build smarter, faster, and more strategically._
    """)
