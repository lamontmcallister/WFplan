import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Recruiting Dashboard", layout="wide")

# =============================================================================
# DEMO MODE (keeps UI smooth):
#   - Collapses all Sub-Depts into the 3 Allocation buckets:
#       Business, Core R&D, Machine Learning
#   - Fixes hiring math:
#       Recruiter Hiring Volume = Planned Hiring (FY26) + Attrition Backfill
#       Planned Hiring (FY26) = FY26 Planned + Open + FY26 Planned - not yet opened
#       Attrition Backfill = (Employees in seat + Future Starts) * Attrition Rate
# =============================================================================

DEMO_MODE = True  # flip to False later if you want the full sub-dept breakdown back

# --------------- Load or initialize data ----------------
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
    st.session_state.headcount_data = df_headcount
    st.session_state.original_headcount = df_headcount.copy()

df_headcount = st.session_state.headcount_data

# ---------------- DEMO collapse ----------------
if DEMO_MODE:
    # Collapse sub-depts into the Allocation buckets (keeps table simple)
    df_headcount["Sub-Dept"] = df_headcount["Allocation"]

    # Aggregate to ONLY 3 rows (ultra clean demo)
    df_headcount = (
        df_headcount
        .groupby(["Allocation", "Sub-Dept"], as_index=False)
        .sum(numeric_only=True)
    )

    # Persist the aggregated version in session for the rest of the app
    st.session_state.headcount_data = df_headcount

# --- Derived columns (recomputed every run so edits are reflected) ---
df_headcount["Workforce Baseline"] = df_headcount["Employees in seat"] + df_headcount["Future Starts"]
df_headcount["Planned Hiring (FY26)"] = df_headcount["FY26 Planned + Open"] + df_headcount["FY26 Planned - not yet opened"]
df_headcount["Total Workforce (EoY Projection)"] = df_headcount["Workforce Baseline"] + df_headcount["Planned Hiring (FY26)"]

# Allocation summary used across pages
df_allocation_summary = df_headcount.groupby("Allocation").sum(numeric_only=True).reset_index()

# Default attrition rates by allocation (editable on Adjusted Hiring Goals page)
default_attrition_rates = {allocation: 0.10 for allocation in df_allocation_summary["Allocation"].unique()}

# Attrition backfill based on baseline workforce (not planned hiring)
df_allocation_summary["Attrition Backfill"] = df_allocation_summary.apply(
    lambda row: row["Workforce Baseline"] * default_attrition_rates[row["Allocation"]],
    axis=1
)

# ✅ Recruiter hiring volume (what matters for capacity)
df_allocation_summary["Final_Hiring_Target"] = (
    df_allocation_summary["Planned Hiring (FY26)"] + df_allocation_summary["Attrition Backfill"]
)

# --------------- Sidebar Navigation ----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Headcount Adjustments", "Adjusted Hiring Goals", "Recruiter Capacity Model", "Finance Overview"])

# --------------- Page 1: Headcount Adjustments ----------------
if page == "Headcount Adjustments":
    st.title("📊 Headcount Adjustments")
    st.markdown("Adjust headcount inputs across departments. Totals update in real time.")

    edited_df = st.data_editor(df_headcount, num_rows="dynamic")

    # Recompute derived columns
    edited_df["Workforce Baseline"] = edited_df["Employees in seat"] + edited_df["Future Starts"]
    edited_df["Planned Hiring (FY26)"] = edited_df["FY26 Planned + Open"] + edited_df["FY26 Planned - not yet opened"]
    edited_df["Total Workforce (EoY Projection)"] = edited_df["Workforce Baseline"] + edited_df["Planned Hiring (FY26)"]

    st.session_state.headcount_data = edited_df

    df_allocation_summary = edited_df.groupby("Allocation").sum(numeric_only=True).reset_index()
    df_allocation_summary["Attrition Backfill"] = df_allocation_summary.apply(
        lambda row: row["Workforce Baseline"] * default_attrition_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = (
        df_allocation_summary["Planned Hiring (FY26)"] + df_allocation_summary["Attrition Backfill"]
    )

    st.subheader("📌 Summary by Allocation")
    st.dataframe(
        df_allocation_summary[
            ["Allocation", "Workforce Baseline", "Planned Hiring (FY26)", "Attrition Backfill", "Final_Hiring_Target", "Total Workforce (EoY Projection)"]
        ],
        use_container_width=True
    )

    st.subheader("📈 Recruiter Hiring Volume Components (Planned + Attrition)")
    chart = px.bar(
        df_allocation_summary,
        x="Allocation",
        y=["Planned Hiring (FY26)", "Attrition Backfill"],
        title="Recruiter Hiring Volume Components",
        barmode="group",
    )
    st.plotly_chart(chart, use_container_width=True)

# --------------- Page 2: Adjusted Hiring Goals ----------------
if page == "Adjusted Hiring Goals":
    st.title("📈 Adjusted Hiring Goals")
    st.sidebar.subheader("Adjust Attrition Percentage by Allocation")

    attrition_rates = {
        allocation: st.sidebar.slider(f"{allocation} Attrition Rate (%)", 0, 50, 10, 1) / 100
        for allocation in df_allocation_summary["Allocation"].unique()
    }

    current_df = st.session_state.headcount_data.copy()
    current_df["Workforce Baseline"] = current_df["Employees in seat"] + current_df["Future Starts"]
    current_df["Planned Hiring (FY26)"] = current_df["FY26 Planned + Open"] + current_df["FY26 Planned - not yet opened"]

    df_allocation_summary = current_df.groupby("Allocation").sum(numeric_only=True).reset_index()

    df_allocation_summary["Attrition Backfill"] = df_allocation_summary.apply(
        lambda row: row["Workforce Baseline"] * attrition_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = (
        df_allocation_summary["Planned Hiring (FY26)"] + df_allocation_summary["Attrition Backfill"]
    )

    st.subheader("📌 Final Targets After Attrition (Recruiter Hiring Volume)")
    st.dataframe(
        df_allocation_summary[["Allocation", "Planned Hiring (FY26)", "Attrition Backfill", "Final_Hiring_Target"]],
        use_container_width=True
    )

    st.subheader("📉 Final Hiring Targets by Allocation")
    chart = px.bar(
        df_allocation_summary,
        x="Allocation",
        y="Final_Hiring_Target",
        color="Allocation",
        title="Recruiter Hiring Volume (Planned + Attrition Backfill)"
    )
    st.plotly_chart(chart, use_container_width=True)

# --------------- Page 3: Recruiter Capacity Model ----------------
if page == "Recruiter Capacity Model":
    st.title("🧮 Recruiter Capacity Model")

    current_df = st.session_state.headcount_data.copy()
    current_df["Workforce Baseline"] = current_df["Employees in seat"] + current_df["Future Starts"]
    current_df["Planned Hiring (FY26)"] = current_df["FY26 Planned + Open"] + current_df["FY26 Planned - not yet opened"]

    df_allocation_summary = current_df.groupby("Allocation").sum(numeric_only=True).reset_index()
    df_allocation_summary["Attrition Backfill"] = df_allocation_summary.apply(
        lambda row: row["Workforce Baseline"] * default_attrition_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = (
        df_allocation_summary["Planned Hiring (FY26)"] + df_allocation_summary["Attrition Backfill"]
    )

    hiring_mode = st.sidebar.radio("Choose Mode", ["Use % Distribution", "Manually Set Quarterly Hiring Targets"])
    weeks_left_to_hire = st.sidebar.slider("Weeks Left to Hire", 4, 52, 13)
    effective_weeks = min(weeks_left_to_hire, 13)

    st.sidebar.markdown("### Recruiter Speed (Hires per Quarter)")
    business_speed = st.sidebar.number_input("Business", value=8)
    core_speed = st.sidebar.number_input("Core R&D", value=6)
    ml_speed = st.sidebar.number_input("Machine Learning", value=2)

    recruiter_speed_per_quarter = {"Business": business_speed, "Core R&D": core_speed, "Machine Learning": ml_speed}

    recruiter_count_by_dept = {}
    for allocation in df_allocation_summary["Allocation"].unique():
        recruiter_count_by_dept[allocation] = st.sidebar.number_input(f"{allocation} - Recruiters Available", min_value=0, value=1)

    hiring_quarters = {}
    if hiring_mode == "Use % Distribution":
        for allocation in df_allocation_summary["Allocation"].unique():
            q1 = st.sidebar.slider(f"{allocation} - Q1 %", 0, 100, 25, 1)
            q2 = st.sidebar.slider(f"{allocation} - Q2 %", 0, 100, 25, 1)
            q3 = st.sidebar.slider(f"{allocation} - Q3 %", 0, 100, 25, 1)
            q4 = st.sidebar.slider(f"{allocation} - Q4 %", 0, 100, 25, 1)

            total = df_allocation_summary.loc[df_allocation_summary["Allocation"] == allocation, "Final_Hiring_Target"].values[0]
            hiring_quarters[allocation] = [round(total * (q / 100)) for q in [q1, q2, q3, q4]]
    else:
        for allocation in df_allocation_summary["Allocation"].unique():
            q1 = st.sidebar.number_input(f"{allocation} - Q1 hires", min_value=0, value=5)
            q2 = st.sidebar.number_input(f"{allocation} - Q2 hires", min_value=0, value=5)
            q3 = st.sidebar.number_input(f"{allocation} - Q3 hires", min_value=0, value=5)
            q4 = st.sidebar.number_input(f"{allocation} - Q4 hires", min_value=0, value=5)
            hiring_quarters[allocation] = [q1, q2, q3, q4]

    df_hiring_schedule = pd.DataFrame.from_dict(hiring_quarters, orient="index", columns=["Q1", "Q2", "Q3", "Q4"])
    df_hiring_schedule.insert(0, "Allocation", df_hiring_schedule.index)

    st.subheader("🎯 Candidates to Hire Per Quarter")
    st.dataframe(df_hiring_schedule, use_container_width=True)

    recruiter_quarters = {}
    recruiter_status_by_quarter = {}

    for allocation in df_hiring_schedule["Allocation"]:
        hires = df_hiring_schedule.loc[df_hiring_schedule["Allocation"] == allocation, ["Q1", "Q2", "Q3", "Q4"]].values[0]
        speed = recruiter_speed_per_quarter.get(allocation, 8) / 13  # hires/week
        available = recruiter_count_by_dept.get(allocation, 0)

        status_list = []
        rec_counts = []

        for h in hires:
            needed = round(h / (speed * effective_weeks), 1) if speed > 0 else 0
            rec_counts.append(needed)
            status_list.append("✅" if available >= needed else f"❌ +{round(needed - available, 1)}")

        recruiter_quarters[allocation] = rec_counts
        recruiter_status_by_quarter[allocation] = status_list

    df_recruiter_schedule = pd.DataFrame.from_dict(recruiter_quarters, orient="index", columns=["Q1 Needed", "Q2 Needed", "Q3 Needed", "Q4 Needed"])
    df_recruiter_schedule.insert(0, "Allocation", df_recruiter_schedule.index)

    df_status = pd.DataFrame.from_dict(recruiter_status_by_quarter, orient="index", columns=["Q1 Status", "Q2 Status", "Q3 Status", "Q4 Status"])
    df_status.insert(0, "Allocation", df_status.index)

    st.subheader("🧮 Recruiter Needs Per Quarter")
    st.dataframe(df_recruiter_schedule, use_container_width=True)

    st.subheader("🟩 Recruiter Status Per Quarter")
    st.dataframe(df_status, use_container_width=True)

# --------------- Page 4: Finance Overview ----------------
if page == "Finance Overview":
    st.title("💰 Finance Overview")

    # Finance tracks changes in PLANNED HIRING (not total workforce)
    original_df = st.session_state.original_headcount.copy()
    current_df = st.session_state.headcount_data.copy()

    for d in (original_df, current_df):
        if DEMO_MODE:
            d["Sub-Dept"] = d["Allocation"]
            d = d.groupby(["Allocation", "Sub-Dept"], as_index=False).sum(numeric_only=True)
        d["Planned Hiring (FY26)"] = d["FY26 Planned + Open"] + d["FY26 Planned - not yet opened"]

    # Recreate from session copy (after grouping above if DEMO_MODE)
    original_df = st.session_state.original_headcount.copy()
    current_df = st.session_state.headcount_data.copy()

    if DEMO_MODE:
        original_df["Sub-Dept"] = original_df["Allocation"]
        current_df["Sub-Dept"] = current_df["Allocation"]
        original_df = original_df.groupby(["Allocation", "Sub-Dept"], as_index=False).sum(numeric_only=True)
        current_df = current_df.groupby(["Allocation", "Sub-Dept"], as_index=False).sum(numeric_only=True)

    original_df["Planned Hiring (FY26)"] = original_df["FY26 Planned + Open"] + original_df["FY26 Planned - not yet opened"]
    current_df["Planned Hiring (FY26)"] = current_df["FY26 Planned + Open"] + current_df["FY26 Planned - not yet opened"]

    delta_df = current_df.copy()
    delta_df = delta_df.merge(
        original_df[["Allocation", "Sub-Dept", "Planned Hiring (FY26)"]].rename(columns={"Planned Hiring (FY26)": "Original Planned Hiring"}),
        on=["Allocation", "Sub-Dept"],
        how="left"
    )

    delta_df["Change (Planned Hiring)"] = delta_df["Planned Hiring (FY26)"] - delta_df["Original Planned Hiring"]
    delta_df["Approval Required"] = delta_df["Change (Planned Hiring)"].apply(lambda x: "Yes" if x > 0 else "No")

    st.subheader("📊 Planned Hiring Changes")
    st.dataframe(
        delta_df[["Allocation", "Sub-Dept", "Original Planned Hiring", "Planned Hiring (FY26)", "Change (Planned Hiring)", "Approval Required"]],
        use_container_width=True
    )

    st.subheader("📉 Change Summary (Bar Chart)")
    fig = px.bar(
        delta_df,
        x="Sub-Dept",
        y="Change (Planned Hiring)",
        color="Allocation",
        title="Planned Hiring Change vs Original Plan"
    )
    st.plotly_chart(fig, use_container_width=True)
