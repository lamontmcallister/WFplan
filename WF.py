
import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Demo settings ----------------
# Flip this to False to restore full Sub-Dept detail.
DEMO_MODE = True


st.set_page_config(page_title="Recruiting Dashboard", layout="wide")

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
    df_headcount["Total Headcount"] = df_headcount[
        ["Employees in seat", "Future Starts", "FY26 Planned + Open", "FY26 Planned - not yet opened"]
    ].sum(axis=1)

    # ---------------- Demo Mode: simplify to 3 top-level allocations ----------------
    if DEMO_MODE:
        # Aggregate to Allocation level so the UI (and demo story) stays clean.
        df_headcount = df_headcount.groupby("Allocation", as_index=False).sum(numeric_only=True)
        df_headcount["Sub-Dept"] = df_headcount["Allocation"]

        # Re-order columns for nicer display
        cols_front = ["Allocation", "Sub-Dept"]
        cols_rest = [c for c in df_headcount.columns if c not in cols_front]
        df_headcount = df_headcount[cols_front + cols_rest]

    st.session_state.headcount_data = df_headcount
    st.session_state.original_headcount = df_headcount.copy()

df_headcount = st.session_state.headcount_data
df_headcount["Total Headcount"] = df_headcount[
    ["Employees in seat", "Future Starts", "FY26 Planned + Open", "FY26 Planned - not yet opened"]
].sum(axis=1)

df_allocation_summary = df_headcount.groupby("Allocation").sum(numeric_only=True).reset_index()
default_attrition_rates = {allocation: 0.10 for allocation in df_allocation_summary["Allocation"].unique()}
df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
    lambda row: row["Total Headcount"] * default_attrition_rates[row["Allocation"]],
    axis=1
)
df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

# --------------- Sidebar Navigation ----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Headcount Adjustments", "Adjusted Hiring Goals", "Recruiter Capacity Model", "Finance Overview"])

# --------------- Page 1: Headcount Adjustments ----------------
if page == "Headcount Adjustments":
    st.title("📊 Headcount Adjustments")
    st.markdown("Adjust headcount inputs across departments. Totals update in real time.")
    edited_df = st.data_editor(df_headcount, num_rows="dynamic")
    edited_df["Total Headcount"] = edited_df[
        ["Employees in seat", "Future Starts", "FY26 Planned + Open", "FY26 Planned - not yet opened"]
    ].sum(axis=1)

    if DEMO_MODE:
        edited_df = edited_df.groupby("Allocation", as_index=False).sum(numeric_only=True)
        edited_df["Sub-Dept"] = edited_df["Allocation"]
        cols_front = ["Allocation", "Sub-Dept"]
        cols_rest = [c for c in edited_df.columns if c not in cols_front]
        edited_df = edited_df[cols_front + cols_rest]

    st.session_state.headcount_data = edited_df

    df_allocation_summary = edited_df.groupby("Allocation").sum(numeric_only=True).reset_index()
    df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
        lambda row: row["Total Headcount"] * default_attrition_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

    st.subheader("📌 Summary by Allocation")
    st.dataframe(df_allocation_summary)

    st.subheader("📈 Total Headcount by Allocation (Bar Chart)")
    chart = px.bar(df_allocation_summary, x="Allocation", y="Total Headcount", color="Allocation", title="Total Headcount by Allocation")
    st.plotly_chart(chart)

# --------------- Page 2: Adjusted Hiring Goals ----------------
if page == "Adjusted Hiring Goals":
    st.title("📈 Adjusted Hiring Goals")
    st.sidebar.subheader("Adjust Attrition Percentage by Allocation")
    attrition_rates = {allocation: st.sidebar.slider(f"{allocation} Attrition Rate (%)", 0, 50, 10, 1) / 100 for allocation in df_allocation_summary["Allocation"].unique()}
    df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
        lambda row: row["Total Headcount"] * attrition_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

    st.subheader("📌 Final Targets After Attrition")
    st.dataframe(df_allocation_summary)

    st.subheader("📉 Final Hiring Targets by Allocation")
    chart = px.bar(df_allocation_summary, x="Allocation", y="Final_Hiring_Target", color="Allocation", title="Final Hiring Targets After Attrition")
    st.plotly_chart(chart)

# --------------- Page 3: Recruiter Capacity Model ----------------
if page == "Recruiter Capacity Model":
    st.title("🧮 Recruiter Capacity Model")
    hiring_mode = st.sidebar.radio("Choose Mode", ["Use % Distribution", "Manually Set Quarterly Hiring Targets"])
    weeks_left_to_hire = st.sidebar.slider("Weeks Left to Hire", 4, 52, 13)
    effective_weeks = min(weeks_left_to_hire, 13)

    st.sidebar.markdown("### Recruiter Speed (Hires per Quarter)")
    business_speed = st.sidebar.number_input("Business", value=8)
    core_speed = st.sidebar.number_input("Core R&D", value=6)
    ml_speed = st.sidebar.number_input("Machine Learning", value=2)

    recruiter_speed_per_quarter = {
        "Business": business_speed,
        "Core R&D": core_speed,
        "Machine Learning": ml_speed
    }

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
    st.dataframe(df_hiring_schedule)

    recruiter_quarters = {}
    recruiter_status_by_quarter = {}

    for allocation in df_hiring_schedule["Allocation"]:
        hires = df_hiring_schedule.loc[df_hiring_schedule["Allocation"] == allocation, ["Q1", "Q2", "Q3", "Q4"]].values[0]
        speed = recruiter_speed_per_quarter.get(allocation, 8) / 13  # hires/week
        available = recruiter_count_by_dept.get(allocation, 0)
        status_list = []
        rec_counts = []

        for h in hires:
            needed = round(h / (speed * effective_weeks), 1)
            rec_counts.append(needed)
            if available >= needed:
                status_list.append("✅")
            else:
                status_list.append(f"❌ +{round(needed - available, 1)}")

        recruiter_quarters[allocation] = rec_counts
        recruiter_status_by_quarter[allocation] = status_list

    df_recruiter_schedule = pd.DataFrame.from_dict(recruiter_quarters, orient="index", columns=["Q1 Needed", "Q2 Needed", "Q3 Needed", "Q4 Needed"])
    df_recruiter_schedule.insert(0, "Allocation", df_recruiter_schedule.index)

    df_status = pd.DataFrame.from_dict(recruiter_status_by_quarter, orient="index", columns=["Q1 Status", "Q2 Status", "Q3 Status", "Q4 Status"])
    df_status.insert(0, "Allocation", df_status.index)

    st.subheader("🧮 Recruiter Needs Per Quarter")
    st.dataframe(df_recruiter_schedule)

    st.subheader("🟩 Recruiter Status Per Quarter")
    st.dataframe(df_status)

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
