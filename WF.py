
import streamlit as st
import pandas as pd
import plotly.express as px

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
    st.markdown("Plan recruiter bandwidth by quarter based on target hires, available weeks, and productivity.")

    hiring_mode = st.radio("Choose Mode", ["Use % Distribution", "Manually Set Quarterly Hiring Targets"], horizontal=True)
    effective_weeks = st.slider("Weeks Remaining in Quarter", 1, 52, 13)

    st.markdown("### Recruiter Productivity (Hires per Recruiter per Week)")
    speed_inputs = {}
    for alloc in df_allocation_summary["Allocation"].unique():
        speed_inputs[alloc] = st.number_input(f"{alloc} Speed", min_value=0.1, value=0.6, step=0.1)

    st.markdown("### Recruiters Available")
    available_inputs = {}
    for alloc in df_allocation_summary["Allocation"].unique():
        available_inputs[alloc] = st.number_input(f"{alloc} Recruiters", min_value=0, value=1)

    hiring_quarters = {}
    if hiring_mode == "Use % Distribution":
        for alloc in df_allocation_summary["Allocation"].unique():
            col1, col2, col3, col4 = st.columns(4)
            with col1: q1 = st.slider(f"{alloc} Q1 %", 0, 100, 25, 1, key=f"{alloc}_q1")
            with col2: q2 = st.slider(f"{alloc} Q2 %", 0, 100, 25, 1, key=f"{alloc}_q2")
            with col3: q3 = st.slider(f"{alloc} Q3 %", 0, 100, 25, 1, key=f"{alloc}_q3")
            with col4: q4 = st.slider(f"{alloc} Q4 %", 0, 100, 25, 1, key=f"{alloc}_q4")
            total = df_allocation_summary.loc[df_allocation_summary["Allocation"] == alloc, "Final_Hiring_Target"].values[0]
            hiring_quarters[alloc] = [round(total * (q / 100)) for q in [q1, q2, q3, q4]]
    else:
        for alloc in df_allocation_summary["Allocation"].unique():
            col1, col2, col3, col4 = st.columns(4)
            with col1: q1 = st.number_input(f"{alloc} Q1 hires", min_value=0, value=5, key=f"{alloc}_m_q1")
            with col2: q2 = st.number_input(f"{alloc} Q2 hires", min_value=0, value=5, key=f"{alloc}_m_q2")
            with col3: q3 = st.number_input(f"{alloc} Q3 hires", min_value=0, value=5, key=f"{alloc}_m_q3")
            with col4: q4 = st.number_input(f"{alloc} Q4 hires", min_value=0, value=5, key=f"{alloc}_m_q4")
            hiring_quarters[alloc] = [q1, q2, q3, q4]

    df_hiring = pd.DataFrame.from_dict(hiring_quarters, orient='index', columns=["Q1", "Q2", "Q3", "Q4"])
    df_hiring.insert(0, "Allocation", df_hiring.index)
    st.subheader("🎯 Hiring Goals per Quarter")
    st.dataframe(df_hiring)

    recruiter_summary = []
    for alloc in df_hiring["Allocation"]:
        hires = df_hiring.loc[alloc, ["Q1", "Q2", "Q3", "Q4"]].values
        speed = speed_inputs.get(alloc, 0.6)
        available = available_inputs.get(alloc, 1)
        needed = [round(h / (speed * effective_weeks), 1) if speed > 0 else 0 for h in hires]
        status = ["✅" if available >= n else f"❌ +{round(n - available, 1)}" for n in needed]
        recruiter_summary.append((alloc, *needed, *status))

    summary_cols = ["Allocation", "Q1 Needed", "Q2 Needed", "Q3 Needed", "Q4 Needed",
                    "Q1 Status", "Q2 Status", "Q3 Status", "Q4 Status"]
    df_summary = pd.DataFrame(recruiter_summary, columns=summary_cols)

    st.subheader("🧮 Recruiter Needs and Status")
    st.dataframe(df_summary)


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
