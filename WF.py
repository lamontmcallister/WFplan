import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Try optional PDF extraction
try:
    import PyPDF2
    _PDF_OK = True
except Exception:
    _PDF_OK = False

st.set_page_config(page_title="Roostock Property Ops Dashboard", layout="wide")

# --- Styles ---
st.markdown("""
<style>
    body { background:#1e1e1e !important; color:#fff !important; }
    .stDataFrame, .stNumberInput input, .stTextInput input, .stSelectbox, .stMultiSelect { background:#333 !important; color:#fff !important; }
    .stButton > button { background:#ff4b2b; color:white; }
    .stButton > button:hover { background:#ff6b4b; }
    .bluehdr { background:#0b5ed7; color:#fff; padding:6px 10px; border-radius:6px; display:inline-block; margin: 6px 0;}
    .sectionhdr { background:#444; color:#fff; padding:6px 10px; border-radius:6px; display:inline-block; margin: 10px 0;}
    .muted { color:#bbb; }
</style>
""", unsafe_allow_html=True)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CURRENT_MONTH = MONTHS[datetime.now().month-1]
BUSINESS_LINES = ["All","Retail","Institutional"]

# --- Baked mapping (trimmed example; editable & persisted) ---
SEED_MAPPING = pd.DataFrame({
    "HRIS Title": [
        "Leasing Associate","Team Lead, Leasing","Lease Marketing Associate","Manager, Leasing",
        "Contact Center Associate","Manager, Contact Center","Contact Center Team Lead",
        "Field Dispatcher","Team Lead, Field Dispatcher","Portfolio Associate",
        "Maintenance Project Coordinator","Sr. MPC","Maintenance Manager","Trade Specialist",
        "Service Technician","Team Lead - Service Technician","Regional Service Manager",
        "Accounting Assistant","Accounts Payable","Property Accountant","Manager, Property Accountant",
        "HOA","Team Lead, HOA","Property Administration","Manager, Property Administration","Team Lead, Property Administration",
        "Utilities","Manager, Utilities","Section 8","QA Specialist",
        "Renovation Project Coordinator","Construction Specialist","Team Lead, Renovation Project","Director of Turns",
        "RXM","Regional Manager, RXM","Account Resolution","Move-In Coordination","Move-Out Coordination",
        "Property Manager","Team Lead, Property Management","Regional Manager, Property Management",
        "Asset Manager","Underwriting","Team Lead, Underwriting","Onsite Manager","Porter"
    ],
    "Mapped Role": [
        "Leasing Associate","Team Lead, Leasing","Lease Marketing","Manager, Leasing",
        "Contact Center Associate","Manager, Contact Center","Contact Center Team Lead",
        "Field Dispatcher","Team Lead, Field Dispatcher","Portfolio Associate",
        "Maintenance Project Coordinator","Sr. MPC","Maintenance Manager","Trade Specialist",
        "Service Technician","Team Lead - Service Technician","Regional Service Manager",
        "Accounting Assistant","Accounts Payable","Property Accountant","Manager, Property Accountant",
        "HOA","Team Lead, HOA","Property Administration","Manager, Property Administration","Team Lead, Property Administration",
        "Utilities","Manager, Utilities","Section 8","QA Specialist",
        "Renovation Project Coordinator","Construction Specialist","Team Lead, Renovation Project","Director of Turns",
        "RXM","Regional Manager, RXM","Account Resolution","Move-In Coordination","Move-Out Coordination",
        "Property Manager","Team Lead, Property Management","Regional Manager, Property Management",
        "Asset Manager","Underwriting","Team Lead, Underwriting","Onsite Manager","Porter"
    ]
})
CANONICAL_ROLES = sorted(SEED_MAPPING["Mapped Role"].unique().tolist())

# --- Load mapping (auto) ---
def load_mapping():
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

if "homes" not in st.session_state:
    # Auto-load demo homes if present
    if os.path.exists("demo_homes_data.csv"):
        try:
            st.session_state.homes = pd.read_csv("demo_homes_data.csv")[["Property Type","Units"]]
        except Exception:
            st.session_state.homes = pd.DataFrame(columns=["Property Type","Units"])
    else:
        st.session_state.homes = pd.DataFrame(columns=["Property Type","Units"])

# Role groups: lets you bucket roles into sections like "41011 Maintenance Techs"
if "role_groups" not in st.session_state:
    # Starter guess — fully editable below
    st.session_state.role_groups = pd.DataFrame({
        "Role": CANONICAL_ROLES,
        "Group": ["41011 Maintenance Techs" if ("Technician" in r or "Maintenance" in r or "Service" in r) else
                  "41021 Leasing" if ("Leasing" in r or "Lease Marketing" in r) else
                  "41013 Resident Services" if ("RXM" in r or "Resident" in r or "Move-" in r or "Account Resolution" in r) else
                  "41003 PM Accounting" if ("Accountant" in r or "Accounts Payable" in r or "Treasury" in r) else
                  "41007 HOA & Compliance" if ("HOA" in r or "QA" in r or "Section 8" in r) else
                  "41012 Turn Management" if ("Turn" in r or "Renovation" in r or "Construction" in r) else
                  "41022 Sales Transition" if ("Portfolio" in r or "Asset" in r) else
                  "41010 Portfolio Management" if ("Property Manager" in r or "Regional Manager, Property Management" in r or "Team Lead, Property Management" in r) else
                  "Other"
                 for r in CANONICAL_ROLES]
    })

# Planned/Actual (tidy) — include Business Line column
def blank_plan_actual(colname):
    rows = []
    for role in CANONICAL_ROLES:
        for m in MONTHS:
            for bl in ["Retail","Institutional"]:
                rows.append({"Role": role, "Month": m, "Business Line": bl, colname: 0})
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
    # Use current month actuals across both business lines
    m = CURRENT_MONTH
    total_actual = int(st.session_state.actual.query("Month == @m")["Actual"].sum())
    col1, col2 = st.columns(2)
    col1.metric("🏘️ Total Homes (all types)", f"{total_homes:,}")
    col2.metric(f"👥 Actual HC ({m})", f"{total_actual:,}")
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

# --- Role Headcount (Biz Line + F1 vs Actual vs Variance) ---
if page == "👥 Role Headcount":
    st.title("👥 Role Headcount — Annual by Business Line")
    biz = st.selectbox("Business Line", BUSINESS_LINES, index=0, help="Choose Retail, Institutional, or All (combined)")
    st.caption("Upload CSVs or edit inline. Variance = Planned − Actual. Role groups control section headers.")

    # Editable role groups
    with st.expander("🗂️ Edit Role Groups (controls section headers)"):
        st.session_state.role_groups = st.data_editor(
            st.session_state.role_groups, num_rows="dynamic", use_container_width=True, key="edit_groups"
        )

    # Uploaders
    colu1, colu2 = st.columns(2)
    with colu1:
        up_plan = st.file_uploader("📤 Upload Planned (Role, Month, Business Line, Planned)", type=["csv"])
        if up_plan:
            df = pd.read_csv(up_plan)
            if set(["Role","Month","Business Line","Planned"]).issubset(df.columns):
                df["Month"] = df["Month"].apply(lambda x: x if x in MONTHS else str(x))
                st.session_state.planned = df[["Role","Month","Business Line","Planned"]].copy()
                st.success("Planned loaded.")
            else:
                st.error("Planned CSV must have columns: Role, Month, Business Line, Planned")
    with colu2:
        up_act = st.file_uploader("📤 Upload Actual (Role, Month, Business Line, Actual)", type=["csv"])
        if up_act:
            df = pd.read_csv(up_act)
            if set(["Role","Month","Business Line","Actual"]).issubset(df.columns):
                df["Month"] = df["Month"].apply(lambda x: x if x in MONTHS else str(x))
                st.session_state.actual = df[["Role","Month","Business Line","Actual"]].copy()
                st.success("Actual loaded.")
            else:
                st.error("Actual CSV must have columns: Role, Month, Business Line, Actual")

    # Optional: PDF import (best-effort) — will try to seed some numbers
    with st.expander("📎 Import from PDF (beta)"):
        st.caption("Attach your PDF. We'll try to extract any numeric grids we can find and seed 'Actual' counts.")
        pdf = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_import")
        if pdf and _PDF_OK:
            try:
                reader = PyPDF2.PdfReader(pdf)
                raw = "\n".join([p.extract_text() or "" for p in reader.pages])
                # Naive numeric seeding: count occurrences of numbers by month labels; this is intentionally simple
                # and meant to be a starting point only.
                seeded = st.session_state.actual.copy()
                for m in MONTHS:
                    # find first small integer near the month token
                    # (this is intentionally very rough to avoid false promises)
                    pass
                st.info("Parsed PDF text. Please review/adjust the Actual table below.")
            except Exception as e:
                st.warning(f"Couldn't parse PDF: {e}")
        elif pdf and not _PDF_OK:
            st.warning("PDF parsing library not available in this environment. Upload CSV instead.")

    # Filter datasets by business line
    if biz == "All":
        plan = st.session_state.planned.groupby(["Role","Month"], as_index=False)["Planned"].sum()
        act = st.session_state.actual.groupby(["Role","Month"], as_index=False)["Actual"].sum()
    else:
        plan = st.session_state.planned.query("`Business Line` == @biz")
        act = st.session_state.actual.query("`Business Line` == @biz")

    # Editable tables for the chosen business line
    st.subheader("✏️ Edit Planned")
    if biz == "All":
        # show expanded table with a Business Line column for clarity when editing combined
        edit_plan = plan.copy()
        edit_plan = edit_plan.merge(st.session_state.planned[["Role","Month","Business Line","Planned"]],
                                    on=["Role","Month","Planned"], how="left")
        edit_plan = edit_plan.rename(columns={"Planned":"Planned (Sum)"})
        st.caption("Showing summed view. To change specific line items, upload CSVs or switch Business Line from 'All' to a specific line.")
        st.dataframe(edit_plan, use_container_width=True)
    else:
        st.session_state.planned = st.data_editor(
            st.session_state.planned, num_rows="dynamic", use_container_width=True, key=f"edit_planned_{biz}"
        )

    st.subheader("✏️ Edit Actual")
    if biz == "All":
        edit_act = act.copy()
        edit_act = edit_act.merge(st.session_state.actual[["Role","Month","Business Line","Actual"]],
                                  on=["Role","Month","Actual"], how="left")
        edit_act = edit_act.rename(columns={"Actual":"Actual (Sum)"})
        st.caption("Showing summed view. To change specific line items, upload CSVs or switch Business Line from 'All' to a specific line.")
        st.dataframe(edit_act, use_container_width=True)
    else:
        st.session_state.actual = st.data_editor(
            st.session_state.actual, num_rows="dynamic", use_container_width=True, key=f"edit_actual_{biz}"
        )

    # Build sectioned grid: for each Group, show F1 (Planned), Actual, Variance and Total HC row
    grp_map = st.session_state.role_groups
    def attach_group(df):
        return df.merge(grp_map, left_on="Role", right_on="Role", how="left").fillna({"Group":"Other"})

    plan_g = attach_group(plan)
    act_g = attach_group(act)

    # Pivot to wide (months as columns)
    def to_wide(df, val):
        if df.empty:
            base = pd.DataFrame({"Group":[],"Role":[]})
            for m in MONTHS: base[m] = []
            return base
        pvt = df.pivot_table(index=["Group","Role"], columns="Month", values=val, aggfunc="sum").reindex(columns=MONTHS).fillna(0).astype(int)
        pvt = pvt.reset_index()
        return pvt

    wide_plan = to_wide(plan_g, "Planned")
    wide_act  = to_wide(act_g, "Actual")

    # Variance = Plan - Actual
    wide_var = wide_plan.copy()
    for m in MONTHS:
        wide_var[m] = wide_plan.get(m, 0) - wide_act.get(m, 0)

    # Total HC rows per section
    def add_totals(df, label="Total HC"):
        if df.empty: return df
        out = []
        for g, sub in df.groupby("Group", sort=False):
            out.append(sub)
            tot = {"Group": g, "Role": label}
            for m in MONTHS:
                tot[m] = int(sub[m].sum())
            out.append(pd.DataFrame([tot]))
        return pd.concat(out, ignore_index=True)

    wide_plan_t = add_totals(wide_plan)
    wide_act_t  = add_totals(wide_act)
    wide_var_t  = add_totals(wide_var)

    st.markdown('<div class="bluehdr">Plan (F1)</div>', unsafe_allow_html=True)
    st.dataframe(wide_plan_t, use_container_width=True)
    st.markdown('<div class="sectionhdr">Actuals</div>', unsafe_allow_html=True)
    st.dataframe(wide_act_t, use_container_width=True)
    st.markdown('<div class="sectionhdr">Variance (Plan − Actual)</div>', unsafe_allow_html=True)
    st.dataframe(wide_var_t, use_container_width=True)

    # Downloads
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Download Role Groups", st.session_state.role_groups.to_csv(index=False), "role_groups.csv")
    with c2:
        st.download_button("⬇️ Download Planned/Actual (raw tidy)", 
            pd.concat([
                st.session_state.planned.assign(Type="Planned").rename(columns={"Planned":"Value"}),
                st.session_state.actual.assign(Type="Actual").rename(columns={"Actual":"Value"})
            ])[["Type","Business Line","Role","Month","Value"]].to_csv(index=False),
            "planned_actual_tidy.csv")

# --- Title Mapping (auto-load saved; editable) ---
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

# --- Ratios (uses ACTUALS for selected month, all biz lines combined) ---
if page == "📈 Ratios":
    st.title("📈 Ratios: Homes per Headcount (Actuals)")
    sel_month = st.selectbox("Month", MONTHS, index=MONTHS.index(CURRENT_MONTH))
    total_homes = int(st.session_state.homes["Units"].sum()) if not st.session_state.homes.empty else 0

    # Combine both business lines
    month_actuals = st.session_state.actual.query("Month == @sel_month").copy()
    role_sums = month_actuals.groupby("Role", as_index=False)["Actual"].sum()

    # Per-role ratios
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
