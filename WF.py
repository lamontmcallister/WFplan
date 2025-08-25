import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

st.set_page_config(page_title="Roostock Property Ops Dashboard", layout="wide")

# --- Styles ---
st.markdown("""
<style>
    body { background:#1e1e1e !important; color:#fff !important; }
    .stDataFrame, .stNumberInput input, .stTextInput input, .stSelectbox, .stMultiSelect { background:#333 !important; color:#fff !important; }
    .stButton > button { background:#ff4b2b; color:white; }
    .stButton > button:hover { background:#ff6b4b; }
</style>
""", unsafe_allow_html=True)

# --- Canonical Roles (from mapping) ---
SEED_MAPPING = pd.DataFrame({'HRIS Title': ['Leasing Admin', 'Leasing Associate', 'Screening Admin', 'Screening Analyst', 'Team Lead, Leasing', 'Team Lead, Screening', 'Lease Marketing Admin', 'Lease Marketing Associate', 'Manager, Leasing', 'Manager, Applicant Screening', 'Manager, Lease Marketing', 'Contact Center Associate', 'Senior Manager, Contact Center', 'Team Lead, Contact Center', 'Field Dispatcher', 'Senior Field Dispatcher', 'Team Lead, Field Dispatcher', 'Field Operations Specialist', 'Portfolio Associate', 'Senior Portfolio Associate', 'Maintenance Project Coordinator', 'Senior Maintenance Project Coordinator', 'Senior Manager, Maintenance', 'Team Lead, Maintenance', 'Trade Specialist', 'Maintenance Technician', 'Senior Maintenance Technician', 'Regional Service Manager', 'Team Lead, Field Operations', 'Accounting Assistant', 'Accounts Payable Associate', 'Accounts Payable Generalist', 'Accounts Payable Specialist', 'Utilities Accounts Payable Specialist', 'Cash Accountant', 'Fixed Asset Accountant', 'Property Accountant', 'Senior Property Accountant', 'Senior Property Accountant - Institutional', 'Manager, Accounts Payable', 'Manager, Property Accounting', 'Manager, Treasury', 'Senior Manager, Accounting', 'Senior Manager, Property Accounting', 'HOA Compliance Specialist', 'HOA Implementation Specialist', 'HOA Implementation Specialist II', 'HOA Mail Management Specialist', 'Team Lead, HOA Compliance', 'Manager, HOA Implementation', 'Property Administration Associate', 'Property Administration Specialist', 'Property Administration Lead', 'Manager, Property Administration', 'Team Lead, Property Administration', 'Utilities Specialist', 'Team Lead, Utilities', 'Manager, Utilities', 'Affordable Housing Specialist', 'Affordable Housing Specialist II', 'Senior Affordable Housing Specialist', 'Quality Assurance Specialist', 'Renovation Project Coordinator', 'Construction Specialist', 'Team Lead, Renovation Projects', 'Director, Turns', 'Director, Disposition Turns', 'Resident Experience Manager', 'Regional Manager, Resident Experience', 'Senior Manager, Resident Experience', 'Account Resolution Specialist', 'Senior Account Resolution Specialist', 'Move-In Coordinator', 'Senior Move-In Coordinator', 'Move-Out Coordinator', 'Junior Move-in Coordinator', 'Junior Resident Experience Manager', 'Property Manager', 'Senior Property Manager', 'Assistant Property Manager', 'Senior Institutional Property Manager', 'Institutional Property Manager', 'Property Management Team Lead', 'Team Lead, Property Management', 'Team Lead, Institutional Property Management', 'Senior Regional Manager, Property Management', 'Regional Manager, Property Management', 'Asset Manager', 'Senior Asset Manager', 'Senior Manager, Asset Management', 'Rent Underwriting Associate', 'Senior Rent Underwriting Associate', 'Team Lead, Rent Underwriting', 'Onsite Manager', 'Porter'], 'Mapped Role': ['Leasing Associate', 'Leasing Associate', 'Leasing Associate', 'Leasing Associate', 'Team Lead, Leasing', 'Team Lead, Leasing', 'Lease Marketing', 'Lease Marketing', 'Manager, Leasing', 'Manager, Leasing', 'Manager, Leasing', 'Contact Center Associate', 'Manager, Contact Center', 'Contact Center Team Lead', 'Field Dispatcher', 'Field Dispatcher', 'Team Lead, Field Dispatcher', 'Field Dispatcher', 'Portfolio Associate', 'Portfolio Associate', 'Maintenance Project Coordinator', 'Sr. MPC', 'Maintenance Manager', 'Maintenance Manager', 'Trade Specialist', 'Service Technician', 'Team Lead - Service Technician', 'Regional Service Manager', 'Team Lead - Service Technician', 'Accounting Assistant', 'Accounts Payable', 'Accounts Payable', 'Accounts Payable', 'Accounts Payable', 'Property Accountant', 'Property Accountant', 'Property Accountant', 'Property Accountant', 'Property Accountant', 'Manager, Property Accountant', 'Manager, Property Accountant', 'Manager, Property Accountant', 'Manager, Property Accountant', 'Manager, Property Accountant', 'HOA', 'HOA', 'HOA', 'HOA', 'Team Lead, HOA', 'Team Lead, HOA', 'Property Administration', 'Property Administration', 'Property Administration', 'Manager, Property Administration', 'Team Lead, Property Administration', 'Utilities', 'Manager, Utilities', 'Manager, Utilities', 'Section 8', 'Section 8', 'Section 8', 'QA Specialist', 'Renovation Project Coordinator', 'Construction Specialist', 'Team Lead, Renovation Project', 'Director of Turns', 'Director of Turns', 'RXM', 'Regional Manager, RXM', 'RXM', 'Account Resolution', 'RXM', 'Move-In Coordination', 'Team Lead, Renovation Project', 'Move-Out Coordination', 'Move-In Coordination', 'RXM', 'Property Manager', 'Property Manager', 'Property Manager', 'Property Manager', 'Property Manager', 'Team Lead, Property Management', 'Team Lead, Property Management', 'Team Lead, Property Management', 'Regional Manager, Property Management', 'Regional Manager, Property Management', 'Asset Manager', 'Asset Manager', 'Asset Manager', 'Underwriting', 'Underwriting', 'Team Lead, Underwriting', 'Onsite Manager', 'Porter']})
CANONICAL_ROLES = sorted(list(SEED_MAPPING["Mapped Role"].unique()))

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CURRENT_MONTH = MONTHS[datetime.now().month-1]

# --- Load mapping (auto) ---
def load_mapping():
    # If a saved mapping exists from a prior session, load it; else, use seed (baked-in) mapping
    if os.path.exists("title_mapping_saved.csv"):
        try:
            m = pd.read_csv("title_mapping_saved.csv")
            if set(["HRIS Title","Mapped Role"]).issubset(m.columns):
                return m[["HRIS Title","Mapped Role"]].copy()
        except Exception:
            pass
    return SEED_MAPPING.copy()

# --- Session State Init ---
if "title_mapping" not in st.session_state:
    st.session_state.title_mapping = load_mapping()

# Homes: only Property Type + Units
if "homes" not in st.session_state:
    st.session_state.homes = pd.DataFrame(columns=["Property Type","Units"])

# Planned vs Actual (annual)
def blank_plan_actual(colname):
    rows = []
    for role in CANONICAL_ROLES:
        for m in MONTHS:
            rows.append({"Role": role, "Month": m, colname: 0})
    return pd.DataFrame(rows)

if "planned" not in st.session_state:
    st.session_state.planned = blank_plan_actual("Planned")
if "actual" not in st.session_state:
    st.session_state.actual = blank_plan_actual("Actual")

# --- Navigation ---
NAV = {
    "🏠 Overview": [],
    "🏘️ Homes Under Management": ["👥 Role Headcount", "🗺️ Title Mapping", "📈 Ratios"]
}
page = st.sidebar.radio("Go to", list(NAV.keys()) + sum(NAV.values(), []))

# --- Overview ---
if page == "🏠 Overview":
    st.title("Roostock Property Ops Dashboard")
    total_homes = int(st.session_state.homes["Units"].sum()) if not st.session_state.homes.empty else 0
    total_actual = int(st.session_state.actual["Actual"].sum()) if not st.session_state.actual.empty else 0
    col1, col2 = st.columns(2)
    col1.metric("🏘️ Total Homes (all types)", f"{total_homes:,}")
    col2.metric("👥 Total Actual Headcount (sum of all months)", f"{total_actual:,}")
    st.caption("Ratios use **Actuals** for the selected month in the Ratios tab.")

# --- Homes Under Management ---
if page == "🏘️ Homes Under Management":
    st.title("🏘️ Homes Under Management")
    st.caption("Columns: Property Type, Units. Upload to replace or add/delete inline.")
    st.dataframe(st.session_state.homes, use_container_width=True)
    if not st.session_state.homes.empty:
        idx_to_del = st.number_input("Row index to delete", min_value=0, max_value=len(st.session_state.homes)-1, step=1)
        if st.button("Delete Home"):
            st.session_state.homes.drop(index=idx_to_del, inplace=True)
            st.session_state.homes.reset_index(drop=True, inplace=True)
            st.success("Deleted.")

    with st.expander("➕ Add Home"):
        col1, col2 = st.columns(2)
        with col1:
            ptype = st.selectbox("Property Type", ["Single-Family Rental","Short Term Rental"])
        with col2:
            units = st.number_input("Units", min_value=1, step=1)
        if st.button("Add"):
            st.session_state.homes = pd.concat([st.session_state.homes, pd.DataFrame([{"Property Type": ptype, "Units": int(units)}])], ignore_index=True)
            st.success("Home added.")

    up = st.file_uploader("📤 Upload CSV to REPLACE homes", type=["csv"])
    if up:
        df = pd.read_csv(up)
        needed = ["Property Type","Units"]
        if all(c in df.columns for c in needed):
            st.session_state.homes = df[needed].copy()
            st.success("Homes replaced.")
        else:
            st.error("CSV must include columns: Property Type, Units")

# --- Role Headcount (annual Planned vs Actual, variance) ---
if page == "👥 Role Headcount":
    st.title("👥 Role Headcount — Annual (Planned vs Actual)")
    st.caption("Upload CSVs or edit inline. Variance = Planned − Actual. This feeds Ratios via Actuals.")

    colu1, colu2 = st.columns(2)
    with colu1:
        up_plan = st.file_uploader("📤 Upload Planned (Role, Month, Planned)", type=["csv"])
        if up_plan:
            df = pd.read_csv(up_plan)
            if set(["Role","Month","Planned"]).issubset(df.columns):
                df["Month"] = df["Month"].apply(lambda x: x if x in MONTHS else str(x))
                st.session_state.planned = df[["Role","Month","Planned"]].copy()
                st.success("Planned loaded.")
            else:
                st.error("Planned CSV must have columns: Role, Month, Planned")
    with colu2:
        up_act = st.file_uploader("📤 Upload Actual (Role, Month, Actual)", type=["csv"])
        if up_act:
            df = pd.read_csv(up_act)
            if set(["Role","Month","Actual"]).issubset(df.columns):
                df["Month"] = df["Month"].apply(lambda x: x if x in MONTHS else str(x))
                st.session_state.actual = df[["Role","Month","Actual"]].copy()
                st.success("Actual loaded.")
            else:
                st.error("Actual CSV must have columns: Role, Month, Actual")

    st.subheader("✏️ Edit Planned")
    st.session_state.planned = st.data_editor(st.session_state.planned, num_rows="dynamic", use_container_width=True, key="edit_planned")

    st.subheader("✏️ Edit Actual")
    st.session_state.actual = st.data_editor(st.session_state.actual, num_rows="dynamic", use_container_width=True, key="edit_actual")

    merged = st.session_state.planned.merge(st.session_state.actual, on=["Role","Month"], how="outer").fillna(0)
    merged["Planned"] = merged["Planned"].astype(int)
    merged["Actual"] = merged["Actual"].astype(int)
    merged["Variance"] = merged["Planned"] - merged["Actual"]

    st.subheader("📊 Annual View (Role × Month)")
    st.dataframe(merged.sort_values(["Role","Month"]), use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("⬇️ Download Planned CSV", st.session_state.planned.to_csv(index=False), "planned_headcount.csv")
    with c2:
        st.download_button("⬇️ Download Actual CSV", st.session_state.actual.to_csv(index=False), "actual_headcount.csv")
    with c3:
        if st.button("💾 Save Mapping to CSV"):
            st.session_state.title_mapping.to_csv("title_mapping_saved.csv", index=False)
            st.success("Mapping saved to title_mapping_saved.csv")

# --- Title Mapping (auto-load saved; editable; upload/download) ---
if page == "🗺️ Title Mapping":
    st.title("🗺️ Title Mapping (HRIS → Reporting Roles)")
    st.caption("Auto-loads your saved mapping if present; otherwise uses baked-in defaults. You can edit, upload, and save here.")

    up_map = st.file_uploader("📤 Upload Mapping CSV (HRIS Title, Mapped Role)", type=["csv"])
    if up_map:
        df = pd.read_csv(up_map)
        if set(["HRIS Title","Mapped Role"]).issubset(df.columns):
            st.session_state.title_mapping = df[["HRIS Title","Mapped Role"]].copy()
            st.success("Mapping loaded.")
        else:
            st.error("CSV must include columns: HRIS Title, Mapped Role")

    st.session_state.title_mapping = st.data_editor(
        st.session_state.title_mapping, num_rows="dynamic", use_container_width=True, key="edit_mapping"
    )

    colm1, colm2 = st.columns(2)
    with colm1:
        st.download_button("⬇️ Download Current Mapping", st.session_state.title_mapping.to_csv(index=False), "title_mapping.csv")
    with colm2:
        if st.button("💾 Save Mapping to CSV"):
            st.session_state.title_mapping.to_csv("title_mapping_saved.csv", index=False)
            st.success("Saved to title_mapping_saved.csv")

# --- Ratios (uses ACTUALS for selected month) ---
if page == "📈 Ratios":
    st.title("📈 Ratios: Homes per Headcount (Actuals)")
    sel_month = st.selectbox("Month", MONTHS, index=MONTHS.index(CURRENT_MONTH))
    # Optional filter: only roles that exist in mapping's Mapped Role column
    mapped_roles = sorted(list(set(st.session_state.title_mapping["Mapped Role"].dropna().astype(str).tolist())))
    if not mapped_roles:
        mapped_roles = CANONICAL_ROLES
    sel_roles = st.multiselect("Filter Roles", mapped_roles, default=mapped_roles)

    total_homes = int(st.session_state.homes["Units"].sum()) if not st.session_state.homes.empty else 0

    # Actuals for month & roles
    month_actuals = st.session_state.actual.query("Month == @sel_month and Role in @sel_roles").copy()
    role_sums = month_actuals.groupby("Role", as_index=False)["Actual"].sum()

    rows = []
    for _, r in role_sums.iterrows():
        role = r["Role"]; hc = int(r["Actual"])
        ratio = (total_homes / hc) if hc > 0 else None
        rows.append({"Role": role, "Actual HC": hc, "Homes per HC": (round(ratio,2) if ratio else "⚠️ No coverage")})
    df_rat = pd.DataFrame(rows)
    st.dataframe(df_rat, use_container_width=True)

    total_hc = int(role_sums["Actual"].sum()) if not role_sums.empty else 0
    total_ratio = (total_homes / total_hc) if total_hc > 0 else None
    if total_ratio:
        st.markdown(f"### 📊 Total: {total_homes:,} Homes / {total_hc:,} Staff = **{total_ratio:.2f} Homes per Headcount**")
    else:
        st.warning("⚠️ Not enough staffing to calculate total ratio.")
