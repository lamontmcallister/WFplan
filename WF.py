
# Roostock Property Dashboard with Demo Mode and Spruced-Up Landing Page

import streamlit as st
import pandas as pd
import numpy as np

# ----------------- Styling & Config -----------------
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

# ----------------- Sidebar Navigation -----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "🏠 Overview",
    "📍 Properties",
    "📊 Staffing Overview",
    "👷 PM Capacity",
    "🔧 Tech Capacity"
])

# ----------------- DEMO FUNCTION -----------------
def run_demo_mode():
    try:
        demo_df = pd.read_csv("demo_dummy_properties.csv")
        st.session_state.properties = demo_df
        st.session_state.num_pms = 5
        st.session_state.pm_capacity = 45
        st.session_state.num_techs = 12
        st.session_state.tech_capacity = 18
        st.session_state.requests_per_home = 2
        st.success("🎬 Demo mode loaded with 100 dummy properties!")
    except Exception as e:
        st.error(f"Demo load failed: {e}")

# ----------------- Overview -----------------
if page == "🏠 Overview":
    st.title("🏠 Roostock Property Operations Dashboard")
    st.markdown("""
    **Welcome to the future of scalable property management.**

    - Efficiently manage staffing across large regional portfolios  
    - Model property manager and technician workload by geography and complexity  
    - Simulate efficiency gains and optimize service delivery

    🧪 *Try the demo below to see how this works in action!*
    """)
    if st.button("🎬 Run Demo Mode"):
        run_demo_mode()

# ----------------- Properties Page -----------------
if page == "📍 Properties":
    st.title("📍 Properties by Region")

    st.subheader("Add Property")
    with st.form("add_property_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            region = st.selectbox("Region", ["West", "Midwest", "South", "Northeast", "Pacific"])
        with col2:
            ptype = st.selectbox("Property Type", ["Single-Family", "Multi-Unit", "Luxury"])
        with col3:
            units = st.number_input("Number of Units", min_value=1, value=1)
        complexity = st.number_input("Complexity (1 = easy, 5 = hard)", 1, 5, value=3)
        submitted = st.form_submit_button("Add Property")
        if submitted:
            new_row = pd.DataFrame([[region, ptype, units, complexity]],
                                   columns=["Region", "Property Type", "Units", "Complexity (1-5)"])
            st.session_state.properties = pd.concat([st.session_state.properties, new_row], ignore_index=True)
            st.success("✅ Property added!")

    st.subheader("Current Property Inventory")
    if not st.session_state.properties.empty:
        filter_region = st.selectbox("Filter by Region", ["All"] + list(st.session_state.properties["Region"].unique()))
        filter_type = st.selectbox("Filter by Property Type", ["All"] + list(st.session_state.properties["Property Type"].unique()))
        df_filtered = st.session_state.properties
        if filter_region != "All":
            df_filtered = df_filtered[df_filtered["Region"] == filter_region]
        if filter_type != "All":
            df_filtered = df_filtered[df_filtered["Property Type"] == filter_type]
        st.dataframe(df_filtered, use_container_width=True)
    else:
        st.warning("No properties added yet.")

# ----------------- Other Tabs Placeholder -----------------
if page == "📊 Staffing Overview":
    st.title("📊 Staffing Overview")
    st.markdown("Coming soon: Region-level sufficiency view and capacity planning matrix.")

if page == "👷 PM Capacity":
    st.title("👷 Property Manager Capacity")
    st.markdown("Coming soon: Region-specific PM capacity inputs and needs.")

if page == "🔧 Tech Capacity":
    st.title("🔧 Technician Capacity")
    st.markdown("Coming soon: Region-specific Tech capacity inputs and forecast.")

