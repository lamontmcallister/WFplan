
# --- Streamlit App: Workforce Planning Dashboard ---
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Recruiting & Finance Dashboard", layout="wide")

st.title("📊 Workforce Planning Dashboard")

# --- Sidebar Inputs ---
st.sidebar.header("Headcount Planning Inputs")
weeks_left_to_hire = st.sidebar.slider("Weeks Left to Hire", 1, 12, 12)

# Sample DataFrame for demonstration
df_allocation_summary = pd.DataFrame({
    "Allocation": ["Business", "Core R&D", "ML"],
    "Q1 Hiring Target": [40, 20, 5],
    "Q2 Hiring Target": [35, 18, 7],
    "Q3 Hiring Target": [30, 22, 6],
    "Q4 Hiring Target": [28, 24, 8]
})

# Recruiters & speed inputs
st.header("📈 Recruiter Capacity Model")

st.markdown("### 👥 Recruiters per Department")
recruiters = {}
speeds = {}
defaults = {"Business": 0.34, "Core R&D": 0.22, "ML": 0.03}
for dept in df_allocation_summary["Allocation"]:
    recruiters[dept] = st.number_input(f"Recruiters for {dept}", min_value=0, value=1, key=f"recruiter_{dept}")
    speeds[dept] = st.number_input(f"Hiring Speed ({dept}) per Recruiter/Week", value=defaults.get(dept, 0.25), key=f"speed_{dept}")

st.markdown("### 🧮 Recruiter Needs per Quarter + Status")
status_data = []
for _, row in df_allocation_summary.iterrows():
    dept = row["Allocation"]
    recs = recruiters[dept]
    speed = speeds[dept]
    cap = recs * speed * weeks_left_to_hire
    result = {"Allocation": dept}
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        target = row[f"{q} Hiring Target"]
        if cap >= target:
            result[f"{q} Status"] = "✅"
        else:
            needed = round((target - cap) / speed, 1)
            result[f"{q} Status"] = f"❌ +{needed}"
    status_data.append(result)

df_status = pd.DataFrame(status_data)
st.dataframe(df_status, use_container_width=True)

st.markdown("### 📌 Summary")
shortages = []
for _, row in df_status.iterrows():
    dept = row["Allocation"]
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        if "❌" in row[f"{q} Status"]:
            shortage = row[f"{q} Status"].split("+")[1]
            shortages.append(f"❌ {dept} in {q}: Need {shortage} more recruiters")

if shortages:
    for item in shortages:
        st.markdown(f"- {item}")
else:
    st.success("✅ All departments are fully staffed for the quarter.")
