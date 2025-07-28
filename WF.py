import streamlit as st
import pandas as pd

import numpy as np
import random

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

regions = ["West", "Midwest", "South", "Northeast", "Pacific"]
types = ["Single-Family", "Multi-Unit", "Luxury"]

if "properties" not in st.session_state:
    st.session_state.properties = pd.DataFrame([{
        "Region": random.choice(regions),
        "Property Type": random.choice(types),
        "Units": random.randint(1, 12),
        "Complexity (1-5)": random.randint(1, 5)
    } for _ in range(100)])

if "regional_staffing" not in st.session_state:
    st.session_state.regional_staffing = {
        r: {
            "PMs Assigned": 2,
            "PM Capacity": random.choice([40, 45, 50, 60]),
            "Techs Assigned": 3,
            "Tech Capacity": random.choice([15, 20, 25])
        } for r in regions
    }

# Hierarchical sidebar navigation

navigation = {
    "🏠 Overview": [],
    "📍 Properties": [],
    "📊 Staffing Overview": ["👷 PM Capacity", "🔧 Tech Capacity"]
}


flat_pages = []
for main_tab, sub_tabs in navigation.items():
    flat_pages.append(main_tab)
    for sub in sub_tabs:
        flat_pages.append("   └─ " + sub)

page = st.sidebar.radio("Go to", flat_pages)

# Normalize page name for routing logic
clean_page = page.replace("   └─ ", "")


# Overview
if clean_page == "🏠 Overview":
    with st.expander("ℹ️ How to Use This Section"):
        st.markdown("""
**Understand and Optimize Your Property Ops Staffing**

This dashboard helps you determine whether you have enough Property Managers (PMs) and Technicians (Techs) to handle your property load.

**Step-by-Step:**
1. **Properties Tab** – Review or add properties with units and complexity.
2. **PM Capacity Tab** – Adjust how many homes a PM can cover and how many are assigned per region.
3. **Tech Capacity Tab** – Adjust how many service requests a Tech can handle and current staffing levels.
4. **Staffing Overview** – See whether you’re short or overstaffed by region.
5. **Run Demo Summary** – Get a high-level view of PM and Tech sufficiency across all regions.

_Use this tool to scenario plan, simulate efficiencies, or justify staffing needs._
""")
        st.markdown("""**How to Use This Section**  
This is your launchpad.  
- Use the 'Run Demo Summary' button to get a quick view of whether you have enough Property Managers and Technicians.
- The metrics compare your current staffing vs. what’s required based on properties and requests.""")
    st.title("Roostock Property Ops Dashboard")

    st.markdown("""
    Welcome to your centralized dashboard for managing **property coverage, staffing, and technician load** across geo-regions.

    🔍 Track properties by region  
    👷 Allocate Property Managers and Technicians  
    📈 Simulate efficiency improvements  
    📊 See staffing gaps before they impact operations
    """)

    if st.button("▶️ Run Demo Summary"):
        st.subheader("📊 Demo Summary")

        total_properties = st.session_state.properties["Units"].sum()
        total_pms = sum([d["PMs Assigned"] for d in st.session_state.regional_staffing.values()])
        avg_pm_capacity = np.mean([d["PM Capacity"] for d in st.session_state.regional_staffing.values()])
        pm_needed = int(np.ceil(total_properties / avg_pm_capacity))
        total_pm_capacity = sum([d["PM Capacity"] * d["PMs Assigned"] for d in st.session_state.regional_staffing.values()])

        total_techs = sum([d["Techs Assigned"] for d in st.session_state.regional_staffing.values()])
        avg_tech_capacity = np.mean([d["Tech Capacity"] for d in st.session_state.regional_staffing.values()])
        estimated_requests = total_properties * 2
        tech_needed = int(np.ceil(estimated_requests / avg_tech_capacity))
        total_tech_capacity = sum([d["Tech Capacity"] * d["Techs Assigned"] for d in st.session_state.regional_staffing.values()])

        st.metric("🏘️ Total Properties Managed", total_properties)
        st.metric("🧑‍💼 PMs Needed", f"{pm_needed} needed vs {total_pms} assigned")
        st.metric("🔧 Techs Needed", f"{tech_needed} needed vs {total_techs} assigned")

        if total_pm_capacity >= total_properties:
            st.success("✅ Property Manager coverage is sufficient")
        else:
            st.warning("⚠️ Additional PMs may be needed")

        if total_tech_capacity >= estimated_requests:
            st.success("✅ Technician coverage is sufficient")
        else:
            st.warning("⚠️ Additional Technicians may be needed")


# Properties with Filters
if clean_page == "📍 Properties":
    st.title("📍 Properties by Region")
    with st.expander("ℹ️ How to Use This Section"):
        st.markdown("""
**Understand and Optimize Your Property Ops Staffing**

This dashboard helps you determine whether you have enough Property Managers (PMs) and Technicians (Techs) to handle your property load.

**Step-by-Step:**
1. **Properties Tab** – Review or add properties with units and complexity.
2. **PM Capacity Tab** – Adjust how many homes a PM can cover and how many are assigned per region.
3. **Tech Capacity Tab** – Adjust how many service requests a Tech can handle and current staffing levels.
4. **Staffing Overview** – See whether you’re short or overstaffed by region.
5. **Run Demo Summary** – Get a high-level view of PM and Tech sufficiency across all regions.

_Use this tool to scenario plan, simulate efficiencies, or justify staffing needs._
""")
        st.markdown("""**How to Use This Section**  
Use filters to narrow down by region or property type.  
- View all properties currently in the system.  
- Add new properties using the form below with region, type, units, and complexity.  
""")

    region_filter = st.selectbox("Filter by Region", ["All"] + regions)
    type_filter = st.selectbox("Filter by Property Type", ["All"] + types)

    df_filtered = st.session_state.properties.copy()
    if region_filter != "All":
        df_filtered = df_filtered[df_filtered["Region"] == region_filter]
    if type_filter != "All":
        df_filtered = df_filtered[df_filtered["Property Type"] == type_filter]

    st.dataframe(df_filtered)

    with st.expander("➕ Add Property"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            region = st.selectbox("Region", regions, key="add_region")
        with col2:
            ptype = st.selectbox("Type", types, key="add_type")
        with col3:
            units = st.number_input("Units", min_value=1, step=1, key="add_units")
        with col4:
            complexity = st.slider("Complexity", 1, 5, 3, key="add_complexity")
        if st.button("Add Property"):
            new_row = pd.DataFrame([[region, ptype, units, complexity]], columns=["Region", "Property Type", "Units", "Complexity (1-5)"])
            st.session_state.properties = pd.concat([st.session_state.properties, new_row], ignore_index=True)
            st.success("Added!")

# Staffing Overview
if clean_page == "📊 Staffing Overview":
    st.title("📊 Regional Staffing Overview")
    with st.expander("ℹ️ How to Use This Section"):
        st.markdown("""
**Understand and Optimize Your Property Ops Staffing**

This dashboard helps you determine whether you have enough Property Managers (PMs) and Technicians (Techs) to handle your property load.

**Step-by-Step:**
1. **Properties Tab** – Review or add properties with units and complexity.
2. **PM Capacity Tab** – Adjust how many homes a PM can cover and how many are assigned per region.
3. **Tech Capacity Tab** – Adjust how many service requests a Tech can handle and current staffing levels.
4. **Staffing Overview** – See whether you’re short or overstaffed by region.
5. **Run Demo Summary** – Get a high-level view of PM and Tech sufficiency across all regions.

_Use this tool to scenario plan, simulate efficiencies, or justify staffing needs._
""")
        st.markdown("""**How to Use This Section**  
This section shows whether your current staff levels meet the need.  
- Adjust the efficiency slider to simulate process improvements.  
- View required vs. actual PMs and Techs by region.  
""")
    efficiency_pct = st.number_input("Efficiency Increase (%)", min_value=0, max_value=50, value=15, step=1)

    summary_rows = []
    for r in regions:
        df_region = st.session_state.properties[st.session_state.properties["Region"] == r]
        total_units = df_region["Units"].sum()
        pm_capacity = st.session_state.regional_staffing[r]["PM Capacity"] * (1 + efficiency_pct / 100)
        tech_capacity = st.session_state.regional_staffing[r]["Tech Capacity"] * (1 + efficiency_pct / 100)
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

# PM Capacity
if clean_page == "👷 PM Capacity":
    st.title("👷 Property Manager Capacity Settings")
    with st.expander("ℹ️ How to Use This Section"):
        st.markdown("""
**Understand and Optimize Your Property Ops Staffing**

This dashboard helps you determine whether you have enough Property Managers (PMs) and Technicians (Techs) to handle your property load.

**Step-by-Step:**
1. **Properties Tab** – Review or add properties with units and complexity.
2. **PM Capacity Tab** – Adjust how many homes a PM can cover and how many are assigned per region.
3. **Tech Capacity Tab** – Adjust how many service requests a Tech can handle and current staffing levels.
4. **Staffing Overview** – See whether you’re short or overstaffed by region.
5. **Run Demo Summary** – Get a high-level view of PM and Tech sufficiency across all regions.

_Use this tool to scenario plan, simulate efficiencies, or justify staffing needs._
""")
        st.markdown("""**How to Use This Section**  
Manually adjust how many PMs are assigned per region and their home capacity.  
- This affects your staffing calculations in other views.  
""")
    for r in regions:
        with st.expander(f"{r}"):
            st.session_state.regional_staffing[r]["PMs Assigned"] = st.number_input(
                f"PMs Assigned in {r}", min_value=0,
                value=st.session_state.regional_staffing[r]["PMs Assigned"],
                key=f"pm_assigned_{r}"
            )
            st.session_state.regional_staffing[r]["PM Capacity"] = st.number_input(
                f"PM Capacity (Homes per PM) in {r}", min_value=1,
                value=st.session_state.regional_staffing[r]["PM Capacity"],
                key=f"pm_capacity_{r}"
            )

# Tech Capacity
if clean_page == "🔧 Tech Capacity":
    with st.expander("ℹ️ How to Use This Section"):
        st.markdown("""
**Understand and Optimize Your Property Ops Staffing**

This dashboard helps you determine whether you have enough Property Managers (PMs) and Technicians (Techs) to handle your property load.

**Step-by-Step:**
1. **Properties Tab** – Review or add properties with units and complexity.
2. **PM Capacity Tab** – Adjust how many homes a PM can cover and how many are assigned per region.
3. **Tech Capacity Tab** – Adjust how many service requests a Tech can handle and current staffing levels.
4. **Staffing Overview** – See whether you’re short or overstaffed by region.
5. **Run Demo Summary** – Get a high-level view of PM and Tech sufficiency across all regions.

_Use this tool to scenario plan, simulate efficiencies, or justify staffing needs._
""")
        st.markdown("""**How to Use This Section**  
- Set how many service requests each Tech can fulfill and how many Techs are staffed.
- The system assumes each property generates 2 monthly service requests.
- This will feed into your coverage calculation in the Demo or Forecast views.""")
    st.title("🔧 Technician Capacity Settings")
    for r in regions:
        with st.expander(f"{r}"):
            st.session_state.regional_staffing[r]["Techs Assigned"] = st.number_input(
                f"Techs Assigned in {r}", min_value=0,
                value=st.session_state.regional_staffing[r]["Techs Assigned"],
                key=f"tech_assigned_{r}"
            )
            st.session_state.regional_staffing[r]["Tech Capacity"] = st.number_input(
                f"Tech Capacity (Requests/Month) in {r}", min_value=1,
                value=st.session_state.regional_staffing[r]["Tech Capacity"],
                key=f"tech_capacity_{r}"
            )
