import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
import re

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
</style>
""", unsafe_allow_html=True)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CURRENT_MONTH = MONTHS[datetime.now().month-1]

# --- Seed mapping (trim, editable later) ---
SEED_MAPPING = pd.DataFrame({
    "HRIS Title": ["Leasing Associate","Team Lead, Leasing","Lease Marketing Associate","Manager, Leasing","Contact Center Associate","Field Dispatcher",
                   "Maintenance Project Coordinator","Maintenance Manager","Service Technician","Regional Service Manager",
                   "Property Accountant","Accounts Payable","HOA","Property Administration","Utilities",
                   "Renovation Project Coordinator","Construction Specialist","RXM","Property Manager","Asset Manager","Underwriting","Onsite Manager","Porter"],
    "Mapped Role": ["Leasing Associate","Team Lead, Leasing","Lease Marketing","Manager, Leasing","Contact Center Associate","Field Dispatcher",
                    "Maintenance Project Coordinator","Maintenance Manager","Service Technician","Regional Service Manager",
                    "Property Accountant","Accounts Payable","HOA","Property Administration","Utilities",
                    "Renovation Project Coordinator","Construction Specialist","RXM","Property Manager","Asset Manager","Underwriting","Onsite Manager","Porter"]
})

CANONICAL_ROLES = sorted(SEED_MAPPING["Mapped Role"].unique().tolist())

def load_mapping():
    if os.path.exists("title_mapping_saved.csv"):
        try:
            m = pd.read_csv("title_mapping_saved.csv")
            if set(["HRIS Title","Mapped Role"]).issubset(m.columns):
                return m[["HRIS Title","Mapped Role"]].copy()
        except Exception:
            pass
    return SEED_MAPPING.copy()

# --- Role normalizer to align variants like "1. Service Technician" with "Service Technician" ---
def normalize_role_series(s: pd.Series) -> pd.Series:
    def _norm(x):
        if pd.isna(x):
            return x
        x = str(x)
        x = x.strip()
        # drop leading numbering/bullets: "1. ", "01) ", "2 - ", etc.
        x = re.sub(r"^\s*\d+\s*[\.\)\-\–:\s]+\s*", "", x)
        # collapse multiple spaces
        x = re.sub(r"\s+", " ", x)
        return x.lower()
    return s.map(_norm)

# --- Session state init ---
if "title_mapping" not in st.session_state:
    st.session_state.title_mapping = load_mapping()

# Homes: ensure demo data exists (total ~19,300) even if CSV missing
if "homes" not in st.session_state:
    demo_df = None
    if os.path.exists("demo_homes_data.csv"):
        try:
            demo_df = pd.read_csv("demo_homes_data.csv")[["Property Type","Units"]]
        except Exception:
            demo_df = None
    if demo_df is None or demo_df.empty:
        demo_df = pd.DataFrame([
            {"Property Type":"Single-Family Rental","Units":15000},
            {"Property Type":"Short Term Rental","Units":4300},
        ])
    st.session_state.homes = demo_df.copy()

# Business Lines used for filters & section headers
if "role_business_lines" not in st.session_state:
    st.session_state.role_business_lines = pd.DataFrame({
        "Role": CANONICAL_ROLES,
        "Business Line": ["41011 Maintenance Techs" if ("Technician" in r or "Maintenance" in r or "Service" in r) else
                          "41021 Leasing" if ("Leasing" in r or "Lease Marketing" in r) else
                          "41013 Resident Services" if ("RXM" in r or "Resident" in r) else
                          "41003 PM Accounting" if ("Accountant" in r or "Accounts Payable" in r) else
                          "41007 HOA & Compliance" if ("HOA" in r) else
                          "41012 Turn Management" if ("Renovation" in r or "Construction" in r) else
                          "41010 Portfolio Management" if ("Property Manager" in r) else
                          "41022 Sales Transition" if ("Asset" in r) else
                          "41016 OSM" if ("Onsite Manager" in r) else
                          "Other"
                         for r in CANONICAL_ROLES]
    })

# maintain a normalized join key inside session for robust merges
st.session_state.role_business_lines["__role_key"] = normalize_role_series(st.session_state.role_business_lines["Role"])

def refresh_business_lines_list():
    return ["All"] + sorted(st.session_state.role_business_lines["Business Line"].unique().tolist())

BUSINESS_LINES = refresh_business_lines_list()

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

# Helper: upsert Role→Business Line pairs from any uploaded df
def upsert_business_lines_from_df(df: pd.DataFrame):
    if "Role" not in df.columns or "Business Line" not in df.columns:
        return
    work = df[["Role","Business Line"]].copy()
    work["Role"] = work["Role"].astype(str).str.strip()
    work["Business Line"] = work["Business Line"].astype(str).str.strip()
    work["__role_key"] = normalize_role_series(work["Role"])
    work = work[work["Business Line"].ne("")]  # non-empty only
    if work.empty:
        return
    # Existing map
    map_df = st.session_state.role_business_lines
    # Create dict of updates
    upd = work.dropna(subset=["Business Line"]).drop_duplicates(subset=["__role_key"])
    # Update existing rows
    map_df = map_df.copy()
    map_lookup = dict(zip(upd["__role_key"], upd["Business Line"]))
    map_df["Business Line"] = map_df.apply(lambda r: map_lookup.get(r["__role_key"], r["Business Line"]), axis=1)
    # Add missing keys
    missing_keys = set(upd["__role_key"]) - set(map_df["__role_key"])
    if missing_keys:
        to_add = upd[upd["__role_key"].isin(missing_keys)][["Role","Business Line","__role_key"]].copy()
        map_df = pd.concat([map_df, to_add], ignore_index=True)
    st.session_state.role_business_lines = map_df

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

# --- Title Mapping ---
if page == "🗺️ Title Mapping":
    st.title("🗺️ Title Mapping (HRIS → Reporting Roles)")
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


# --- Role Headcount (Month + Business Line filters) ---
if page == "👥 Role Headcount":
    st.title("👥 Role Headcount — Planned vs Actual")
    sel_months = st.multiselect("Months", ["All"] + MONTHS, default=["All"])
    BUSINESS_LINES = refresh_business_lines_list()
    sel_bline = st.selectbox("Business Line", BUSINESS_LINES, index=0, help="Filter by role → business line")
    st.caption("Variance = Planned − Actual (filtered by Business Line).")

    # Editable Business Lines
    with st.expander("🗂️ Edit Business Lines (Role → Business Line)"):
        st.session_state.role_business_lines = st.data_editor(
            st.session_state.role_business_lines, num_rows="dynamic", use_container_width=True, key="edit_business_lines"
        )
        st.caption("Tip: Upload a CSV with columns: Role, Business Line from the three-dot menu in the editor.")
        st.session_state.role_business_lines["__role_key"] = normalize_role_series(st.session_state.role_business_lines["Role"])

    # Merge Business Line for filtering
    def attach_business_line(df):
        work = df.copy()
        work["__role_key"] = normalize_role_series(work["Role"])
        map_df = st.session_state.role_business_lines[["Business Line","__role_key"]].copy().rename(columns={"Business Line":"BL_map"})
        work = work.merge(map_df, on="__role_key", how="left")
        if "Business Line" in work.columns:
            work["Business Line"] = work["Business Line"].replace("", np.nan)
            work["Business Line"] = work["Business Line"].fillna(work["BL_map"])
        else:
            work["Business Line"] = work["BL_map"]
        work["Business Line"] = work["Business Line"].fillna("Other")
        work = work.drop(columns=["__role_key","BL_map"])
        return work

    plan_g = attach_business_line(st.session_state.planned)
    act_g  = attach_business_line(st.session_state.actual)

    if sel_bline != "All":
        plan_g = plan_g.query("`Business Line` == @sel_bline")
        act_g  = act_g.query("`Business Line` == @sel_bline")

    def to_wide(df, val, months):
        if df.empty:
            base = pd.DataFrame({"Business Line":[],"Role":[]})
            for m in months: base[m] = []
            return base
        pvt = df.pivot_table(index=["Business Line","Role"], columns="Month", values=val, aggfunc="sum").reindex(columns=months).fillna(0).astype(int)
        pvt = pvt.reset_index()
        return pvt

    if "All" in sel_months:
        months_to_show = MONTHS
    else:
        months_to_show = sel_months if sel_months else [CURRENT_MONTH]

    wide_plan = to_wide(plan_g, "Planned", months_to_show)
    wide_act  = to_wide(act_g , "Actual" , months_to_show)

    # Variance
    wide_var = wide_plan.copy()
    for m in months_to_show:
        wide_var[m] = wide_plan.get(m, 0) - wide_act.get(m, 0)

    def add_totals(df, label="Total HC"):
        if df.empty: return df
        out = []
        for g, sub in df.groupby("Business Line", sort=False):
            out.append(sub)
            tot = {"Business Line": g, "Role": label}
            for m in months_to_show:
                tot[m] = int(sub[m].sum())
            out.append(pd.DataFrame([tot]))
        return pd.concat(out, ignore_index=True)

    st.markdown('<div class="bluehdr">Plan (F1)</div>', unsafe_allow_html=True)
    st.dataframe(add_totals(wide_plan), use_container_width=True)

    st.markdown('<div class="sectionhdr">Actuals</div>', unsafe_allow_html=True)
    st.dataframe(add_totals(wide_act), use_container_width=True)

    st.markdown('<div class="sectionhdr">Variance (Plan − Actual)</div>', unsafe_allow_html=True)
    st.dataframe(add_totals(wide_var), use_container_width=True)

# --- Ratios (Month + Business Line filters) ---
if page == "📈 Ratios":
    st.title("📈 Ratios: Homes per Headcount (Actuals)")
    sel_month = st.selectbox("Month", MONTHS, index=MONTHS.index(CURRENT_MONTH))
    BUSINESS_LINES = refresh_business_lines_list()
    sel_bline  = st.selectbox("Business Line", BUSINESS_LINES, index=0)

    total_homes = int(st.session_state.homes["Units"].sum()) if not st.session_state.homes.empty else 0

    # Attach business line to actuals for filtering (prefer uploaded BL)
    act = st.session_state.actual.copy()
    act["__role_key"] = normalize_role_series(act["Role"])
    map_df = st.session_state.role_business_lines[["Business Line","__role_key"]].copy().rename(columns={"Business Line":"BL_map"})
    act = act.merge(map_df, on="__role_key", how="left")
    if "Business Line" in act.columns:
        act["Business Line"] = act["Business Line"].replace("", np.nan)
        act["Business Line"] = act["Business Line"].fillna(act["BL_map"])
    else:
        act["Business Line"] = act["BL_map"]
    act = act.drop(columns=["__role_key","BL_map"]).fillna({"Business Line":"Other"})
    if sel_bline != "All":
        act = act.query("`Business Line` == @sel_bline")

    month_actuals = act.query("Month == @sel_month").copy()
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
