import streamlit as st
import pandas as pd
import numpy as np
import random

st.set_page_config(page_title="Roostock Property Ops Dashboard", layout="wide")

# Styling
st.markdown("""
    <style>
        body, .css-18e3th9, .css-1d391kg {
            background-color: #1e1e1e !important;
            color: white !important;
        }
        .stButton > button {
            background-color: #ff4b2b;
            color: white;
        }
        .stButton > button:hover {
            background-color: #ff6b4b;
        }
        .stDataFrame, .stNumberInput input {
            color: white !important;
            background-color: #333 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
regions = ["West", "Midwest", "South", "Northeast", "Pacific"]
if "properties" not in st.session_state:
    st.session_state.properties = pd.DataFrame([{
        "Region": random.choice(regions),
        "Property Type": random.choice(["Single-Family", "Multi-Unit", "Luxury"]),
        "Units": random.randint(1, 12),
        "Complexity (1-5)": random.randint(1, 5)
    } for _ in range(100)])

if "regional_staffing" not in st.session_state:
    st.session_state.regional_staffing = {
        r: {"PMs Assigned": 2, "Techs Assigned": 3} for r in regions
    }

# Sidebar navigation
page = st.sidebar.radio("Go to", [
    "🏠 Overview",
    "📍 Properties",
    "👷 PM Capacity",
    "🔧 Tech Capacity",
    "📊 Staffing Overview"
])

# Overview
if page == "🏠 Overview":
    st.title("Roostock Property Ops Dashboard")
    st.markdown("""
    Track property volume, allocate Property Managers (PMs) and Technicians (Techs), and forecast staffing needs across regions.
    """)

# Properties
if page == "📍 Properties":
    st.title("📍 Properties by Region")

    st.dataframe(st.session_state.properties)

    with st.expander("➕ Add Property"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            region = st.selectbox("Region", regions)
        with col2:
            ptype = st.selectbox("Type", ["Single-Family", "Multi-Unit", "Luxury"])
        with col3:
            units = st.number_input("Units", min_value=1, step=1)
        with col4:
            complexity = st.slider("Complexity", 1, 5, 3)
        if st.button("Add Property"):
            new_row = pd.DataFrame([[region, ptype, units, complexity]], columns=["Region", "Property Type", "Units", "Complexity (1-5)"])
            st.session_state.properties = pd.concat([st.session_state.properties, new_row], ignore_index=True)
            st.success("Added!")

# PM Capacity
if page == "👷 PM Capacity":
    st.title("👷 Property Manager Capacity Settings")

    for r in regions:
        with st.expander(f"{r}"):
            st.session_state.regional_staffing[r]["PMs Assigned"] = st.number_input(
                f"PMs Assigned in {r}", min_value=0,
                value=st.session_state.regional_staffing[r]["PMs Assigned"],
                key=f"pm_{r}"
            )

# Tech Capacity
if page == "🔧 Tech Capacity":
    st.title("🔧 Technician Capacity Settings")

    for r in regions:
        with st.expander(f"{r}"):
            st.session_state.regional_staffing[r]["Techs Assigned"] = st.number_input(
                f"Techs Assigned in {r}", min_value=0,
                value=st.session_state.regional_staffing[r]["Techs Assigned"],
                key=f"tech_{r}"
            )

# Staffing Overview
if page == "📊 Staffing Overview":
    st.title("📊 Regional Staffing Overview")
    efficiency_pct = st.slider("Efficiency Increase (%)", 0, 50, value=15)

    summary_rows = []
    for r in regions:
        df = st.session_state.properties
        df_region = df[df["Region"] == r]
        total_units = df_region["Units"].sum()
        avg_complexity = df_region["Complexity (1-5)"].mean() if not df_region.empty else 3

        pm_capacity = 50 * (1 + efficiency_pct / 100)
        tech_capacity = 20 * (1 + efficiency_pct / 100)
        reqs_per_home = 2

        pm_needed = np.ceil(total_units / pm_capacity)
        tech_needed = np.ceil((total_units * reqs_per_home) / tech_capacity)

        pm_assigned = st.session_state.regional_staffing[r]["PMs Assigned"]
        tech_assigned = st.session_state.regional_staffing[r]["Techs Assigned"]

        summary_rows.append({
            "Region": r,
            "Homes": total_units,
            "PMs Assigned": pm_assigned,
            "PMs Needed": int(pm_needed),
            "PM Status": "✅" if pm_assigned >= pm_needed else f"❌ +{int(pm_needed - pm_assigned)}",
            "Techs Assigned": tech_assigned,
            "Techs Needed": int(tech_needed),
            "Tech Status": "✅" if tech_assigned >= tech_needed else f"❌ +{int(tech_needed - tech_assigned)}"
        })

    df_summary = pd.DataFrame(summary_rows)
    st.dataframe(df_summary, use_container_width=True)
