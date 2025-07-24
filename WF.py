# property_dashboard.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Property Capacity Dashboard", layout="wide")

# --- Styling ---
st.markdown("""
    <style>
        body {
            background-color: #1e1e1e;
            color: white;
        }
        .stButton>button {
            background-color: #ff4b2b;
            color: white;
        }
        .stTextInput>div>input,
        .stNumberInput input,
        .stSelectbox>div>div>div {
            background-color: #333;
            color: white;
        }
        .stDataFrame, .stDataTable {
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🏡 Property Management & Technician Capacity Dashboard")

# ------------------------------
# Initialize Session State
# ------------------------------
if "property_data" not in st.session_state:
    st.session_state.property_data = pd.DataFrame(columns=["Region", "Property Type", "Units", "Complexity Score"])

# ------------------------------
# Inputs for Property Additions
# ------------------------------
with st.expander("➕ Add Property Info"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        region = st.selectbox("Region", ["West", "Midwest", "South", "Northeast", "Pacific"])
    with col2:
        ptype = st.selectbox("Property Type", ["Single-Family", "Multi-Unit", "Luxury"])
    with col3:
        units = st.number_input("Units (e.g., 1 house or 10-unit building)", min_value=1, step=1)
    with col4:
        complexity = st.slider("Complexity Score (1 = easy, 5 = hard)", 1, 5, 3)

    if st.button("Add Property"):
        new_row = {"Region": region, "Property Type": ptype, "Units": units, "Complexity Score": complexity}
        st.session_state.property_data = st.session_state.property_data.append(new_row, ignore_index=True)

# ------------------------------
# Show Properties Table
# ------------------------------
st.subheader("🏘️ Current Property Inventory")
st.dataframe(st.session_state.property_data)

# ------------------------------
# Property Manager Capacity Model
# ------------------------------
st.subheader("🧮 Property Manager Capacity")
pm_capacity_per_score = {1: 70, 2: 60, 3: 50, 4: 40, 5: 30}
total_units = st.session_state.property_data["Units"].sum()
avg_complexity = st.session_state.property_data["Complexity Score"].mean() if not st.session_state.property_data.empty else 3
base_pm_capacity = pm_capacity_per_score.get(round(avg_complexity), 50)

num_managers = st.number_input("Number of Property Managers", min_value=1, step=1, value=3)
efficiency_boost = st.checkbox("Apply 15% Efficiency Boost?")

pm_current_capacity = base_pm_capacity * num_managers
pm_boosted_capacity = round(pm_current_capacity * 1.15) if efficiency_boost else pm_current_capacity

st.markdown(f"""
- 🔢 Average Complexity Score: **{avg_complexity:.1f}**
- 👷 Property Managers: **{num_managers}**
- 🏡 Homes Managed Now: **{pm_current_capacity}**
- 🚀 With Efficiency Boost: **{pm_boosted_capacity}**
""")

# ------------------------------
# Technician Capacity Model
# ------------------------------
st.subheader("🔧 Technician Capacity Model")

col1, col2, col3 = st.columns(3)
with col1:
    techs = st.number_input("Number of Technicians", min_value=1, step=1, value=5)
with col2:
    reqs_per_unit = st.number_input("Service Requests / Unit / Month", min_value=1.0, value=2.0, step=0.1)
with col3:
    tech_capacity = st.number_input("Requests Each Tech Can Handle / Month", min_value=1, value=20)

total_reqs = total_units * reqs_per_unit
homes_supported = (techs * tech_capacity) / reqs_per_unit
homes_supported_boosted = homes_supported * 1.15 if efficiency_boost else homes_supported

st.markdown(f"""
- 🧮 Total Requests: **{total_reqs:.0f} / month**
- 🔧 Techs: **{techs}**
- 🏘️ Homes Supported: **{homes_supported:.1f}**
- ⚡ With Efficiency Boost: **{homes_supported_boosted:.1f}**
""")
