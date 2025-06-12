
# --- Cleaned-Up Recruiter Capacity Model ---

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.header("📈 Recruiter Capacity Model (Clean UI)")

# Sample department data
df_capacity = pd.DataFrame({
    "Allocation": ["Business", "Core R&D", "ML"],
    "Q1 Hiring Target": [40, 20, 5],
    "Q2 Hiring Target": [35, 18, 7],
    "Q3 Hiring Target": [30, 22, 6],
    "Q4 Hiring Target": [28, 24, 8],
    "Default Speed": [0.34, 0.22, 0.03]
})

weeks_left = st.slider("Weeks Left to Hire", 1, 12, 12)

# Select department
selected_dept = st.selectbox("Select Department", df_capacity["Allocation"].unique())

dept_row = df_capacity[df_capacity["Allocation"] == selected_dept].iloc[0]
speed = st.number_input("Hiring Speed per Recruiter (per week)", value=float(dept_row["Default Speed"]), step=0.01, key="speed_input")
recruiters = st.number_input("Number of Recruiters", min_value=0, value=1, step=1, key="recruiters_input")

capacity = speed * recruiters * weeks_left

# Show results
st.markdown(f"### 📊 Quarterly Capacity for **{selected_dept}**")

summary = {}
for q in ["Q1", "Q2", "Q3", "Q4"]:
    target = dept_row[f"{q} Hiring Target"]
    if capacity >= target:
        summary[q] = f"✅ Capacity OK (Target: {target}, Capacity: {round(capacity,1)})"
    else:
        needed = round((target - capacity) / speed, 1)
        summary[q] = f"❌ Shortfall: Need {needed} more recruiters"

for q, result in summary.items():
    st.markdown(f"- **{q}**: {result}")

# Bar Chart
chart_df = pd.DataFrame({
    "Quarter": ["Q1", "Q2", "Q3", "Q4"],
    "Target": [dept_row["Q1 Hiring Target"], dept_row["Q2 Hiring Target"], dept_row["Q3 Hiring Target"], dept_row["Q4 Hiring Target"]],
    "Capacity": [capacity] * 4
})

fig = px.bar(chart_df, x="Quarter", y=["Target", "Capacity"], barmode="group", title=f"{selected_dept}: Target vs Capacity")
st.plotly_chart(fig, use_container_width=True)
