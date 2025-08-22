
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roostock Ops Dashboard", layout="wide")

# Initialize session state
if "staff_data" not in st.session_state:
    st.session_state.staff_data = pd.DataFrame(columns=["Name", "Position", "Region", "COGS/OPEX"])
if "homes_data" not in st.session_state:
    st.session_state.homes_data = pd.DataFrame(columns=["Region", "Homes Under Management"])

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Overview", "📊 PM Capacity Model", "📐 Staffing Ratios"])

if page == "🏠 Overview":
    st.title("🏠 Roostock Property Ops Dashboard")
    with st.expander("ℹ️ How to Use This Section"):
        st.markdown("Use this dashboard to track property management operations across geo-regions. "
                    "Start by uploading or entering home and staffing data. Navigate between tabs to analyze capacity and ratios.")
    st.markdown("Welcome to your centralized dashboard for managing **property coverage, staffing, and technician load** across geo-regions.")
    st.markdown("""
🔍 Track properties by region  
👷 Allocate Property Managers and Technicians  
📈 Simulate efficiency improvements  
📊 See staffing gaps before they impact operations
""")
    with st.form("home_data_entry"):
        st.subheader("🏘️ Homes Under Management")
        region = st.text_input("Region")
        homes = st.number_input("Homes Under Management", min_value=0)
        submitted = st.form_submit_button("Add/Update Region")
        if submitted and region:
            st.session_state.homes_data = st.session_state.homes_data[st.session_state.homes_data.Region != region]
            st.session_state.homes_data = pd.concat([st.session_state.homes_data, pd.DataFrame([{"Region": region, "Homes Under Management": homes}])], ignore_index=True)

    st.dataframe(st.session_state.homes_data)

elif page == "📊 PM Capacity Model":
    st.title("📊 PM Capacity Model")
    with st.expander("ℹ️ How to Use This Section"):
        st.markdown("This section estimates staffing needs based on homes under management. "
                    "You can adjust average capacity and compare it against current staff levels.")
    st.subheader("Upload or Add Staffing Data")
    uploaded_file = st.file_uploader("Upload staff CSV", type="csv")
    if uploaded_file:
        st.session_state.staff_data = pd.read_csv(uploaded_file)

    with st.form("manual_entry"):
        name = st.text_input("Name")
        position = st.text_input("Position")
        region = st.text_input("Region")
        cost_type = st.selectbox("COGS or OPEX", ["COGS", "OPEX"])
        add_row = st.form_submit_button("Add Staff")
        if add_row and name and position:
            st.session_state.staff_data = pd.concat([
                st.session_state.staff_data,
                pd.DataFrame([{"Name": name, "Position": position, "Region": region, "COGS/OPEX": cost_type}])
            ], ignore_index=True)

    st.dataframe(st.session_state.staff_data)

elif page == "📐 Staffing Ratios":
    st.title("📐 Staffing Ratios by Region")
    with st.expander("ℹ️ How to Use This Section"):
        st.markdown("Select positions and regions to compare Homes Under Management to staff counts. "
                    "This provides insight into your operational coverage and potential inefficiencies.")
    all_positions = sorted(st.session_state.staff_data["Position"].unique())
    selected_positions = st.multiselect("Select Positions", options=all_positions, default=all_positions)
    all_regions = sorted(st.session_state.homes_data["Region"].unique())
    selected_regions = st.multiselect("Select Regions", options=all_regions, default=all_regions)

    if selected_positions and selected_regions:
        filtered_staff = st.session_state.staff_data[
            st.session_state.staff_data["Position"].isin(selected_positions) &
            st.session_state.staff_data["Region"].isin(selected_regions)
        ]
        staff_counts = filtered_staff.groupby(["Region", "Position"]).size().reset_index(name="Staff Count")
        homes_counts = st.session_state.homes_data[st.session_state.homes_data["Region"].isin(selected_regions)]

        ratio_table = pd.merge(staff_counts, homes_counts, on="Region", how="left")
        ratio_table["Homes per Staff"] = ratio_table["Homes Under Management"] / ratio_table["Staff Count"]
        st.dataframe(ratio_table)

    st.markdown("🔄 Bonus Features We Can Add Later:")
    st.markdown("""
- Export to Excel or PDF  
- Drill-down by city or sub-region  
- Time-based trend analysis  
- Role-based access controls  
- Live sync with HR systems  
""")
