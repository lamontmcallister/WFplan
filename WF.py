# Part 1: Property Management + Technician Capacity Dashboard (Roostock-Ready)
# --- Full Streamlit Rework ---

import streamlit as st
import pandas as pd
import numpy as np

# --------------- Styling ---------------
st.set_page_config(page_title="Roostock Property Ops Dashboard", layout="wide")

st.markdown("""
    <style>
        body, .css-18e3th9, .css-1d391kg {
            background-color: #1e1e1e !important;
            color: white !important;
        }
        .stButton > button {
            background-color: #ff4b2b;
            color: white;
            border: none;
            padding: 0.5rem 1.25rem;
            font-size: 1rem;
            border-radius: 6px;
        }
        .stButton > button:hover {
            background-color: #ff6b4b;
            transition: 0.3s;
        }
        .stTextInput > div > input,
        .stNumberInput input {
            background-color: #333 !important;
            color: white !important;
        }
        .stDataFrame, .stDataTable, .stMarkdown {
            color: white !important;
        }
        .st-expanderContent {
            background-color: #222 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- Sidebar Nav -----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "🏠 Overview",
    "📍 Add Properties by Region",
    "🧑‍💼 Property Manager Capacity",
    "🔧 Technician Capacity",
    "📈 Efficiency Forecast"
])

# ----------------- Session Init -----------------
if "properties" not in st.session_state:
    st.session_state.properties = pd.DataFrame(columns=["Region", "Property Type", "Units", "Complexity (1-5)"])
if "pm_capacity" not in st.session_state:
    st.session_state.pm_capacity = 50
if "tech_capacity" not in st.session_state:
    st.session_state.tech_capacity = 10
if "requests_per_home" not in st.session_state:
    st.session_state.requests_per_home = 2
if "num_pms" not in st.session_state:
    st.session_state.num_pms = 4
if "num_techs" not in st.session_state:
    st.session_state.num_techs = 10

# ----------------- Page 1: Overview -----------------
if page == "🏠 Overview":
    st.title("🏠 Roostock Property Ops Dashboard")
    st.markdown("""
    Welcome to your all-in-one dashboard for managing properties, staffing capacity, and technician forecasting.

    - 📍 Track properties by region and type
    - 🧑‍💼 Model property manager workload by complexity
    - 🔧 Forecast technician needs by service volume
    - 📈 Simulate improvements in efficiency to see impact on output
    """)

# ----------------- Page 2: Add Properties -----------------
if page == "📍 Add Properties by Region":
    st.title("📍 Properties by Region")
    with st.form("add_property_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            region = st.selectbox("Region", ["West", "Midwest", "South", "Northeast", "Pacific"])
        with col2:
            ptype = st.selectbox("Property Type", ["Single-Family", "Multi-Unit", "Luxury"])
        with col3:
            units = st.number_input("Number of Units", min_value=1, value=1)
        complexity = st.slider("Complexity (1 = easy, 5 = very complex)", 1, 5, value=3)
        submitted = st.form_submit_button("Add Property")
        if submitted:
            new_row = pd.DataFrame([[region, ptype, units, complexity]],
                                   columns=["Region", "Property Type", "Units", "Complexity (1-5)"])
            st.session_state.properties = pd.concat([st.session_state.properties, new_row], ignore_index=True)
            st.success("✅ Property added!")

    st.subheader("Current Property Inventory")
    st.dataframe(st.session_state.properties, use_container_width=True)

# ----------------- Page 3: Property Manager Capacity -----------------
if page == "🧑‍💼 Property Manager Capacity":
    st.title("🧑‍💼 Property Manager Capacity")

    st.number_input("Total Property Managers", min_value=1, step=1,
                    value=st.session_state.num_pms, key="num_pms")
    st.number_input("Avg Homes per PM (base)", min_value=1, step=1,
                    value=st.session_state.pm_capacity, key="pm_capacity")

    total_capacity = st.session_state.num_pms * st.session_state.pm_capacity
    efficiency_pct = st.slider("Efficiency Increase (%)", 0, 50, value=15)
    improved_capacity = int(total_capacity * (1 + efficiency_pct / 100))

    st.metric("Current Capacity", f"{total_capacity} Homes")
    st.metric("🔧 With Efficiency Increase", f"{improved_capacity} Homes")

# ----------------- Page 4: Technician Capacity -----------------
if page == "🔧 Technician Capacity":
    st.title("🔧 Technician Capacity Model")

    st.number_input("Total Technicians", min_value=1, step=1,
                    value=st.session_state.num_techs, key="num_techs")
    st.number_input("Requests per Technician / Month", min_value=1, step=1,
                    value=st.session_state.tech_capacity, key="tech_capacity")
    st.number_input("Avg Requests per Home / Month", min_value=1, step=1,
                    value=st.session_state.requests_per_home, key="requests_per_home")

    homes_supported = (st.session_state.num_techs * st.session_state.tech_capacity) / st.session_state.requests_per_home
    homes_improved = homes_supported * (1 + efficiency_pct / 100)

    st.metric("Current Home Support Capacity", f"{int(homes_supported)} Homes")
    st.metric("🚀 With Efficiency Increase", f"{int(homes_improved)} Homes")

# ----------------- Page 5: Forecast -----------------
if page == "📈 Efficiency Forecast":
    st.title("📈 Efficiency Forecasting")

    st.markdown("Use this page to simulate improvements in service and property management capacity.")
    efficiency_pct = st.slider("Efficiency Increase (%)", 0, 50, value=15)

    pm_base = st.session_state.pm_capacity * st.session_state.num_pms
    tech_base = (st.session_state.tech_capacity * st.session_state.num_techs) / st.session_state.requests_per_home

    pm_out = int(pm_base * (1 + efficiency_pct / 100))
    tech_out = int(tech_base * (1 + efficiency_pct / 100))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("🏘️ PM Capacity (Homes)", f"{pm_out}")
    with col2:
        st.metric("🔧 Technician Capacity (Homes)", f"{tech_out}")

    st.caption("Note: Technician capacity is based on monthly service request assumptions.")
