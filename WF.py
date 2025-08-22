import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Roostock Property Ops Dashboard", layout="wide")

# Styles
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

# Constants
regions = ["West", "Midwest", "South", "Northeast", "Pacific"]
roles = [
    "Field Ops", "Maintenance Techs", "PM G&A", "PM Accounting", "HOA & Compliance", "Sales Transition",
    "Leasing", "Resident Services", "Underwriting", "Turn Management", "R&M",
    "Vendor relationship", "Renovations", "Portfolio Management", "OSM"
]

# Load demo data if session is empty
if "properties" not in st.session_state or st.session_state.properties.empty:
    try:
        st.session_state.properties = pd.read_csv("demo_homes_data.csv")
    except:
        st.warning("⚠️ Demo homes data not found.")

if "role_counts" not in st.session_state or not st.session_state.role_counts:
    try:
        demo_roles_df = pd.read_csv("demo_role_counts.csv")
        st.session_state.role_counts = {r: {} for r in demo_roles_df["Region"].unique()}
        for _, row in demo_roles_df.iterrows():
            region, role, count = row["Region"], row["Role"], row["Count"]
            st.session_state.role_counts[region][role] = int(count)
    except:
        st.warning("⚠️ Demo role counts not found.")

# Sidebar Navigation
navigation = {
    "🏠 Overview": [],
    "🏘️ Homes Under Management": ["👥 Role Headcount", "📈 Ratios"]
}
page = st.sidebar.radio("Go to", list(navigation.keys()) + sum(navigation.values(), []))

# Overview Page
if page == "🏠 Overview":
    st.title("Roostock Property Ops Dashboard")
    with st.expander("ℹ️ How to Use This Section"):
        st.markdown("Launchpad to assess total staffing needs and regional load across PMs and Techs.")
    if st.button("▶️ Run Demo Summary"):
        total_units = st.session_state.properties["Units"].sum()
        st.metric("🏘️ Total Units", total_units)

# Homes Under Management Page
if page == "🏘️ Homes Under Management":
    st.title("🏘️ Homes Under Management")
    st.dataframe(st.session_state.properties, use_container_width=True)

    # Manual Add
    with st.expander("➕ Add New Home"):
        col1, col2, col3, col4 = st.columns(4)
        with col1: region = st.selectbox("Region", regions, key="add_region")
        with col2: ptype = st.selectbox("Type", ["Single-Family", "Multi-Unit", "Luxury"], key="add_type")
        with col3: units = st.number_input("Units", min_value=1, step=1, key="add_units")
        with col4: complexity = st.slider("Complexity", 1, 5, 3, key="add_complexity")
        if st.button("Add Home"):
            new_row = pd.DataFrame([[region, ptype, units, complexity]], columns=["Region", "Property Type", "Units", "Complexity (1-5)"])
            st.session_state.properties = pd.concat([st.session_state.properties, new_row], ignore_index=True)
            st.success("Home added!")

    # CSV Upload
    uploaded_csv = st.file_uploader("📤 Upload CSV to Replace Homes Data", type=["csv"])
    if uploaded_csv:
        df_csv = pd.read_csv(uploaded_csv)
        if all(col in df_csv.columns for col in ["Region", "Property Type", "Units", "Complexity (1-5)"]):
            st.session_state.properties = df_csv
            st.success("Homes data replaced successfully.")

# Ratios Page
if page == "📈 Ratios":
    st.title("📈 Ratios: Homes per Role")

    uploaded_roles = st.file_uploader("📤 Upload Role Headcounts CSV", type=["csv"], key="roles_upload")
    if uploaded_roles:
        df_roles = pd.read_csv(uploaded_roles)
        if all(col in df_roles.columns for col in ["Region", "Role", "Count"]):
            for _, row in df_roles.iterrows():
                r, role, count = row["Region"], row["Role"], row["Count"]
                if r in st.session_state.role_counts and role in st.session_state.role_counts[r]:
                    st.session_state.role_counts[r][role] = int(count)
            st.success("Role headcounts updated.")

    selected_regions = st.multiselect("Select Region(s)", regions, default=regions)
    selected_roles = st.multiselect("Select Role(s)", roles, default=roles)

    filtered_df = st.session_state.properties[st.session_state.properties["Region"].isin(selected_regions)]
    total_units = filtered_df["Units"].sum()

    data = []
    for role in selected_roles:
        total_headcount = sum(st.session_state.role_counts[r].get(role, 0) for r in selected_regions)
        ratio = total_units / total_headcount if total_headcount > 0 else None
        data.append({"Role": role, "Headcount": total_headcount, "Homes per Headcount": ratio if ratio else "⚠️ No coverage"})

    df_ratios = pd.DataFrame(data)
    st.dataframe(df_ratios)

    # Total ratio summary
    total_headcount = sum([sum(st.session_state.role_counts[r].get(role, 0) for role in selected_roles) for r in selected_regions])
    total_ratio = total_units / total_headcount if total_headcount > 0 else None
    st.markdown(f"### 📊 Total: {int(total_units):,} Homes / {total_headcount:,} Staff = **{total_ratio:.2f} Homes per Headcount**" if total_ratio else "⚠️ Not enough staffing to calculate total ratio.")


# Role Headcount Page
if page == "👥 Role Headcount":
    st.title("👥 Role Headcount by Region")
    st.markdown("Update the number of staff allocated to each role across different regions.")

    uploaded_roles = st.file_uploader("📤 Upload Role Headcounts CSV", type=["csv"], key="manual_roles_upload")
    if uploaded_roles:
        df_roles = pd.read_csv(uploaded_roles)
        if all(col in df_roles.columns for col in ["Region", "Role", "Count"]):
            for _, row in df_roles.iterrows():
                r, role, count = row["Region"], row["Role"], row["Count"]
                if r in st.session_state.role_counts and role in st.session_state.role_counts[r]:
                    st.session_state.role_counts[r][role] = int(count)
            st.success("✅ Headcounts updated from CSV.")

    for r in regions:
        with st.expander(f"{r}"):
            for role in roles:
                st.session_state.role_counts[r][role] = st.number_input(
                    f"{role} in {r}", min_value=0,
                    value=st.session_state.role_counts[r].get(role, 0),
                    key=f"{r}_{role}_input"
                )

# Placeholder for other pages
if page in navigation["🏘️ Homes Under Management"]:
    st.info("This section is available in the full build. Focus here is on 'Homes' and 'Ratios'.")
