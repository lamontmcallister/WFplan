
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
    "Headcount Adjustments",
    "Adjusted Hiring Goals",
    "Recruiter Capacity Model",
    "Success Metrics"
])
