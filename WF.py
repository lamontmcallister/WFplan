
# ------------------ Augment Data with Function + Region (Demo) ------------------
# You would replace this with real metadata if available in the future
import numpy as np
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
df_headcount["Region"] = np.random.choice(regions, size=len(df_headcount))  # Simulated region for now


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

# ------------------ Augment Data with Function + Region ------------------
functions = {
    "CS": "Customer Success", "Customer Success & Solutions": "Customer Success", "Marketing": "Marketing",
    "ProServ": "Professional Services", "Sales": "Sales", "Accounting": "G&A", "Biz Ops & Prog Mgmt": "G&A",
    "Finance": "G&A", "Legal": "G&A", "Ops & Admin": "G&A", "Employee Experience": "G&A",
    "People Operations": "HR", "Recruiting": "HR", "Workplace": "G&A", "Allos": "R&D",
    "COGS ops": "R&D", "Eng": "R&D", "G&A Biz sys": "G&A", "Prod": "Product",
    "R&D biz sys": "R&D", "Sales Biz sys": "Sales", "Machine Learning": "R&D"
}
import numpy as np
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

# --------------- Sidebar Navigation ----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Headcount Adjustments", "Adjusted Hiring Goals", "Recruiter Capacity Model", "Finance Overview", "Success Metrics"])

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
    st.markdown("Forecast recruiter bandwidth vs hiring demand with built-in role difficulty and quarterly needs.")

    effective_weeks = st.slider("Weeks Remaining in Quarter", 1, 52, 13)

    st.markdown("### Recruiter Productivity (Hires per Recruiter per Quarter by Level)")
    levels = [1, 2, 3, 4, 5, 6, 7, 8]
    level_speed = {}
    for lvl in levels:
        default = 10 if lvl <= 5 else 5 if lvl <= 7 else 2
        level_speed[lvl] = st.number_input(f"Level {lvl}", min_value=1, value=default, step=1)

    st.markdown("### Recruiters Available per Allocation")
    available_inputs = {}
    for alloc in df_allocation_summary["Allocation"].unique():
        available_inputs[alloc] = st.number_input(f"{alloc} Recruiters", min_value=0, value=1)

    # Assume 25% per quarter auto-distribution if % mode selected
    auto_quarters = {}
    for alloc in df_allocation_summary["Allocation"].unique():
        total = df_allocation_summary.loc[df_allocation_summary["Allocation"] == alloc, "Final_Hiring_Target"].values[0]
        per_q = round(total / 4)
        auto_quarters[alloc] = [per_q] * 4

    df_hiring = pd.DataFrame.from_dict(auto_quarters, orient='index', columns=["Q1", "Q2", "Q3", "Q4"])
    df_hiring.insert(0, "Allocation", df_hiring.index)
    st.subheader("🎯 Auto-Distributed Hiring Goals per Quarter (25%)")
    st.dataframe(df_hiring)

    st.markdown("### Avg Role Level per Allocation")
    role_level_inputs = {}
    for alloc in df_allocation_summary["Allocation"].unique():
        role_level_inputs[alloc] = st.slider(f"{alloc} Avg Level", 1, 8, 4)

    recruiter_summary = []
    for alloc in df_hiring["Allocation"]:
        hires = df_hiring.loc[alloc, ["Q1", "Q2", "Q3", "Q4"]].values
        level = role_level_inputs.get(alloc, 4)
        speed = level_speed.get(level, 10)
        available = available_inputs.get(alloc, 1)
        needed = [round(h / speed, 1) for h in hires]
        status = ["✅" if available >= n else f"❌ +{round(n - available, 1)}" for n in needed]
        recruiter_summary.append((alloc, *needed, *status))

    summary_cols = ["Allocation", "Q1 Needed", "Q2 Needed", "Q3 Needed", "Q4 Needed",
                    "Q1 Status", "Q2 Status", "Q3 Status", "Q4 Status"]
    df_summary = pd.DataFrame(recruiter_summary, columns=summary_cols)

    st.subheader("🧮 Recruiter Needs and Status by Quarter")
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


# --------------- Page 5: Success Metrics ----------------
if page == "Success Metrics":
    st.title("📊 Success Metrics & TA Benchmarks")

    st.markdown("These metrics help evaluate team performance and guide workforce strategy.")

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
