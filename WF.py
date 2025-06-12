import streamlit as st
import pandas as pd
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="Recruiting Dashboard", layout="wide")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Headcount Adjustments", "Adjusted Hiring Goals", "Recruiter Capacity Model"])

if "headcount_data" in st.session_state:
    df_headcount = st.session_state.headcount_data

if page == "Recruiter Capacity Model":
    st.title("Recruiter Capacity Model")

    st.sidebar.subheader("Hiring Distribution Mode")
    auto_distribution = st.sidebar.radio("Select Mode", ["Automated 25% per Quarter", "Manual Entry"])

    weeks_left_to_hire = st.sidebar.slider("Weeks Left to Hire", 4, 52, 26)

    hiring_distribution = {}
    if auto_distribution == "Automated 25% per Quarter":
        for allocation in df_headcount["Allocation"].unique():
            hiring_distribution[allocation] = [25, 25, 25, 25]
    else:
        for allocation in df_headcount["Allocation"].unique():
            st.sidebar.subheader(f"{allocation} Hiring Distribution")
            q1 = st.sidebar.slider(f"{allocation} - Q1 %", 0, 100, 25, 1)
            q2 = st.sidebar.slider(f"{allocation} - Q2 %", 0, 100, 25, 1)
            q3 = st.sidebar.slider(f"{allocation} - Q3 %", 0, 100, 25, 1)
            q4 = st.sidebar.slider(f"{allocation} - Q4 %", 0, 100, 25, 1)
            hiring_distribution[allocation] = [q1, q2, q3, q4]

    consolidated_hiring = df_headcount.groupby("Allocation").sum(numeric_only=True).reset_index()

    hiring_quarters = {}
    for allocation in consolidated_hiring["Allocation"]:
        total_hires = consolidated_hiring[consolidated_hiring["Allocation"] == allocation]["Final Hiring Target"].values[0]
        q1, q2, q3, q4 = hiring_distribution[allocation]
        hiring_quarters[allocation] = [round(total_hires * (q1 / 100)), round(total_hires * (q2 / 100)),
                                       round(total_hires * (q3 / 100)), round(total_hires * (q4 / 100))]

    df_hiring_schedule = pd.DataFrame.from_dict(hiring_quarters, orient="index", columns=["Q1", "Q2", "Q3", "Q4"])
    df_hiring_schedule.insert(0, "Allocation", df_hiring_schedule.index)
    st.write("### Hiring Requirement by Quarter (Consolidated by Allocation)")
    st.dataframe(df_hiring_schedule)

    recruiter_speed = {"Business": 10, "Machine Learning": 4, "Core R&D": 7}
    recruiter_quarters = {}
    for allocation in df_hiring_schedule["Allocation"]:
        recruiter_quarters[allocation] = [round(df_hiring_schedule[df_hiring_schedule["Allocation"] == allocation][q].values[0] / recruiter_speed.get(allocation, 10), 1) for q in ["Q1", "Q2", "Q3", "Q4"]]

    df_recruiter_schedule = pd.DataFrame.from_dict(recruiter_quarters, orient="index", columns=["Q1", "Q2", "Q3", "Q4"])
    df_recruiter_schedule.insert(0, "Allocation", df_recruiter_schedule.index)
    st.write("### Recommended Recruiters Needed Per Quarter")
    st.dataframe(df_recruiter_schedule)

    st.subheader("Recruiters Needed vs. Available (Color-Coded)")

    available_recruiters = {}
    recruiter_allocation = {}
    for allocation in df_headcount["Allocation"].unique():
        available_recruiters[allocation] = st.sidebar.slider(f"Available {allocation} Recruiters", 1, 50, 10)
        recruiter_allocation[allocation] = available_recruiters[allocation]

    df_recruiter_allocation = pd.DataFrame.from_dict(recruiter_allocation, orient="index", columns=["Available Recruiters"])
    df_recruiter_allocation.insert(0, "Allocation", df_recruiter_allocation.index)

    df_recruiter_allocation["Required Recruiters"] = df_recruiter_schedule.sum(axis=1, numeric_only=True)
    df_recruiter_allocation["Shortfall"] = df_recruiter_allocation["Required Recruiters"] - df_recruiter_allocation["Available Recruiters"]
    df_recruiter_allocation["Status"] = df_recruiter_allocation["Shortfall"].apply(lambda x: "Red" if x > 0 else "Green")

    st.dataframe(df_recruiter_allocation[["Allocation", "Required Recruiters", "Available Recruiters", "Shortfall", "Status"]])

    st.subheader("Cross-Functional Recruiter Allocation")

    surplus_allocations = df_recruiter_allocation[df_recruiter_allocation["Shortfall"] < 0]["Allocation"].tolist()
    deficit_allocations = df_recruiter_allocation[df_recruiter_allocation["Shortfall"] > 0]["Allocation"].tolist()

    if surplus_allocations and deficit_allocations:
        allocation_from = st.selectbox("Select Surplus Allocation", surplus_allocations)
        allocation_to = st.selectbox("Select Deficit Allocation", deficit_allocations)
        transfer_amount = st.slider("Number of Recruiters to Transfer", 0, abs(df_recruiter_allocation[df_recruiter_allocation["Allocation"] == allocation_from]["Shortfall"].values[0]), 1)

        if st.button("Allocate Recruiters"):
            df_recruiter_allocation.loc[df_recruiter_allocation["Allocation"] == allocation_from, "Available Recruiters"] -= transfer_amount
            df_recruiter_allocation.loc[df_recruiter_allocation["Allocation"] == allocation_to, "Available Recruiters"] += transfer_amount

            df_recruiter_allocation["Shortfall"] = df_recruiter_allocation["Required Recruiters"] - df_recruiter_allocation["Available Recruiters"]
            df_recruiter_allocation["Status"] = df_recruiter_allocation["Shortfall"].apply(lambda x: "Red" if x > 0 else "Green")

            st.write("### Updated Recruiter Allocation")
            st.dataframe(df_recruiter_allocation[["Allocation", "Required Recruiters", "Available Recruiters", "Shortfall", "Status"]])

    fig_capacity = px.bar(df_recruiter_allocation, x="Allocation", y=["Available Recruiters", "Required Recruiters"], barmode="group",
                          title="Recruiter Capacity vs. Demand", color_discrete_map={"Available Recruiters": "green", "Required Recruiters": "red"})
    st.plotly_chart(fig_capacity)
