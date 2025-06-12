
import streamlit as st
import pandas as pd
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="Recruiting Dashboard", layout="wide")

# Load and store updated headcount data in session state
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

df_headcount = st.session_state.headcount_data
df_allocation_summary = df_headcount.groupby("Allocation").sum(numeric_only=True).reset_index()

# Precompute hiring targets to prevent KeyErrors
default_attrition_rates = {allocation: 0.10 for allocation in df_allocation_summary["Allocation"].unique()}
df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
    lambda row: row["Total Headcount"] * default_attrition_rates[row["Allocation"]],
    axis=1
)
df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Headcount Adjustments", "Adjusted Hiring Goals", "Recruiter Capacity Model"])

if page == "Headcount Adjustments":
    st.title("Headcount Adjustments")
    st.write("### Adjust Headcount by Allocation and Sub-Dept")
    edited_df = st.data_editor(df_headcount, num_rows="dynamic")
    st.session_state.headcount_data = edited_df

    st.write("### Headcount Summary by Allocation")
    st.dataframe(df_allocation_summary)

if page == "Adjusted Hiring Goals":
    st.title("Adjusted Hiring Goals")
    st.write("### Hiring Targets Adjusted for Attrition and Headcount Planning")

    # Sidebar for attrition rate adjustments
    st.sidebar.subheader("Adjust Attrition Percentage by Allocation")
    attrition_rates = {allocation: st.sidebar.slider(f"{allocation} Attrition Rate (%)", 0, 50, 10, 1) / 100 for allocation in df_allocation_summary["Allocation"].unique()}

    # Compute attrition impact and final targets
    df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(lambda row: row["Total Headcount"] * attrition_rates[row["Allocation"]], axis=1)
    df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

    st.dataframe(df_allocation_summary[["Allocation", "Employees in seat", "Future Starts", "FY26 Planned + Open", "FY26 Planned - not yet opened", "Total Headcount", "Attrition Impact", "Final_Hiring_Target"]])

if page == "Recruiter Capacity Model":
    st.title("Recruiter Capacity Model")

    st.sidebar.subheader("Hiring Distribution Mode")
    auto_distribution = st.sidebar.radio("Select Mode", ["Automated 25% per Quarter", "Manual Entry"])
    weeks_left_to_hire = st.sidebar.slider("Weeks Left to Hire", 4, 52, 26)

    hiring_distribution = {}
    if auto_distribution == "Automated 25% per Quarter":
        for allocation in df_allocation_summary["Allocation"].unique():
            hiring_distribution[allocation] = [25, 25, 25, 25]
    else:
        for allocation in df_allocation_summary["Allocation"].unique():
            st.sidebar.subheader(f"{allocation} Hiring Distribution")
            q1 = st.sidebar.slider(f"{allocation} - Q1 %", 0, 100, 25, 1)
            q2 = st.sidebar.slider(f"{allocation} - Q2 %", 0, 100, 25, 1)
            q3 = st.sidebar.slider(f"{allocation} - Q3 %", 0, 100, 25, 1)
            q4 = st.sidebar.slider(f"{allocation} - Q4 %", 0, 100, 25, 1)
            hiring_distribution[allocation] = [q1, q2, q3, q4]

    hiring_quarters = {}
    for allocation in df_allocation_summary["Allocation"]:
        total_hires = df_allocation_summary.loc[df_allocation_summary["Allocation"] == allocation, "Final_Hiring_Target"].values[0]
        q1, q2, q3, q4 = hiring_distribution[allocation]
        hiring_quarters[allocation] = [round(total_hires * (q1 / 100)), round(total_hires * (q2 / 100)),
                                       round(total_hires * (q3 / 100)), round(total_hires * (q4 / 100))]

    df_hiring_schedule = pd.DataFrame.from_dict(hiring_quarters, orient="index", columns=["Q1", "Q2", "Q3", "Q4"])
    df_hiring_schedule.insert(0, "Allocation", df_hiring_schedule.index)
    st.write("### Candidates to Hire Per Quarter (Adjusted for Attrition)")
    st.dataframe(df_hiring_schedule)

    recruiter_speed_per_week = {"Business": 0.34, "Machine Learning": 0.03, "Core R&D": 0.22}
    recruiter_actual_weeks = {"Business": 26, "Machine Learning": 21, "Core R&D": 24}

    recruiter_quarters = {}
    for allocation in df_hiring_schedule["Allocation"]:
        recruiter_speed = recruiter_speed_per_week.get(allocation, 0.34)
        actual_weeks = recruiter_actual_weeks.get(allocation, 26)
        adjusted_weeks = min(actual_weeks, weeks_left_to_hire)
        recruiter_quarters[allocation] = [round(df_hiring_schedule.loc[df_hiring_schedule["Allocation"] == allocation, q].values[0] / (recruiter_speed * adjusted_weeks), 1) for q in ["Q1", "Q2", "Q3", "Q4"]]

    df_recruiter_schedule = pd.DataFrame.from_dict(recruiter_quarters, orient="index", columns=["Q1", "Q2", "Q3", "Q4"])
    df_recruiter_schedule.insert(0, "Allocation", df_recruiter_schedule.index)
    st.write("### Recommended Recruiters Needed Per Quarter (Adjusted for Hiring Timeline)")
    st.dataframe(df_recruiter_schedule)
