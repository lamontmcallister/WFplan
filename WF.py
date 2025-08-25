import streamlit as st
import pandas as pd
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
    .bluehdr { background:#0b5ed7; color:#fff; padding:6px 10px; border-radius:6px; display:inline-block; margin: 6px 0;}
    .sectionhdr { background:#444; color:#fff; padding:6px 10px; border-radius:6px; display:inline-block; margin: 10px 0;}
</style>
""", unsafe_allow_html=True)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CURRENT_MONTH = MONTHS[datetime.now().month-1]

# ---------- Mapping loader (Department + Business Line) ----------
MAPPING_FILENAMES = [
    "PM HC Trend by Department - 1. Title Mapping.csv",
    "title_mapping_saved.csv",
    "title_mapping.csv"
]

def _normalize_mapping(df):
    cmap = {c.lower().strip(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in cmap: return cmap[n]
        return None
    # required role column
    role_col = pick("mapped role","role")
    if not role_col:
        raise ValueError("Mapping CSV must include 'Mapped Role' or 'Role'.")
    dept_col = pick("department","dept","staffing ratio group","group")
    bl_col   = pick("business line","biz line","line")
    out = pd.DataFrame({"Role": df[role_col].astype(str).str.strip()})
    out["Department"]   = df[dept_col].astype(str).str.strip() if dept_col else "Unassigned"
    out["Business Line"]= df[bl_col].astype(str).str.strip()   if bl_col   else "All"
    return out.drop_duplicates()

def load_mapping():
    # try known filenames
    for fn in MAPPING_FILENAMES:
        if os.path.exists(fn):
            try:
                return _normalize_mapping(pd.read_csv(fn))
            except Exception:
                pass
    # scan directory for a plausible CSV
    for fn in os.listdir("."):
        if fn.lower().endswith(".csv"):
            try:
                df = pd.read_csv(fn)
                lc = [c.lower().strip() for c in df.columns]
                if ("mapped role" in lc) or ("role" in lc):
                    return _normalize_mapping(df)
            except Exception:
                continue
    return pd.DataFrame(columns=["Role","Department","Business Line"])

# ---------- Session init ----------
if "mapping" not in st.session_state:
    st.session_state.mapping = load_mapping()

if "roles" not in st.session_state:
    st.session_state.roles = sorted(st.session_state.mapping["Role"].unique().tolist()) if not st.session_state.mapping.empty else []

# Homes (demo fallback to 19,300)
if "homes" not in st.session_state:
    demo = None
    if os.path.exists("demo_homes_data.csv"):
        try:
            demo = pd.read_csv("demo_homes_data.csv")[["Property Type","Units"]]
        except Exception:
            demo = None
    if demo is None or demo.empty:
        demo = pd.DataFrame([
            {"Property Type":"Single-Family Rental","Units":15000},
            {"Property Type":"Short Term Rental","Units":4300},
        ])
    st.session_state.homes = demo.copy()

def blank_pa(colname):
    rows = []
    for r in st.session_state.roles:
        for m in MONTHS:
            rows.append({"Role": r, "Month": m, colname: 0})
    return pd.DataFrame(rows)

if "planned" not in st.session_state:
    st.session_state.planned = blank_pa("Planned")
if "actual" not in st.session_state:
    st.session_state.actual = blank_pa("Actual")

def departments():
    if st.session_state.mapping.empty: return ["All"]
    return ["All"] + sorted(st.session_state.mapping["Department"].dropna().unique().tolist())

def business_lines():
    if st.session_state.mapping.empty: return ["All"]
    return ["All"] + sorted(st.session_state.mapping["Business Line"].dropna().unique().tolist())

# ---------- Navigation ----------
NAV = {
    "🏠 Overview": [],
    "🏘️ Homes Under Management": ["👥 Headcount", "🗺️ Title Mapping", "📈 Ratios"]
}
page = st.sidebar.radio("Go to", list(NAV.keys()) + sum(NAV.values(), []))

# ---------- Overview ----------
if page == "🏠 Overview":
    st.title("Roostock Property Ops Dashboard")
    total_homes = int(st.session_state.homes["Units"].sum()) if not st.session_state.homes.empty else 0
    m = CURRENT_MONTH
    total_actual = int(st.session_state.actual.query("Month == @m")["Actual"].sum()) if not st.session_state.actual.empty else 0
    c1, c2 = st.columns(2)
    c1.metric("🏘️ Total Homes", f"{total_homes:,}")
    c2.metric(f"👥 Actual HC ({m})", f"{total_actual:,}")
    if st.session_state.mapping.empty:
        st.warning("No mapping loaded. Upload Title Mapping in '🗺️ Title Mapping' to enable Department/Business Line.")

# ---------- Homes ----------
if page == "🏘️ Homes Under Management":
    st.title("🏘️ Homes Under Management")
    st.dataframe(st.session_state.homes, use_container_width=True)
    if not st.session_state.homes.empty:
        idx = st.number_input("Row index to delete", min_value=0, max_value=len(st.session_state.homes)-1, step=1)
        if st.button("Delete Home"):
            st.session_state.homes.drop(index=idx, inplace=True)
            st.session_state.homes.reset_index(drop=True, inplace=True)
            st.success("Deleted.")
    with st.expander("➕ Add Home"):
        col1, col2 = st.columns(2)
        with col1: ptype = st.selectbox("Property Type", ["Single-Family Rental","Short Term Rental"])
        with col2: units = st.number_input("Units", min_value=1, step=1)
        if st.button("Add"):
            st.session_state.homes = pd.concat([st.session_state.homes, pd.DataFrame([{"Property Type": ptype, "Units": int(units)}])], ignore_index=True)
            st.success("Home added.")
    up = st.file_uploader("📤 Upload CSV to REPLACE homes (Property Type, Units)", type=["csv"])
    if up:
        df = pd.read_csv(up)
        if all(c in df.columns for c in ["Property Type","Units"]):
            st.session_state.homes = df[["Property Type","Units"]].copy()
            st.success("Homes replaced.")
        else:
            st.error("CSV must include: Property Type, Units")

# ---------- Title Mapping ----------
if page == "🗺️ Title Mapping":
    st.title("🗺️ Title Mapping (HRIS → Role → Department + Business Line)")
    st.caption("App auto-loads a mapping CSV in the working directory. Upload to override; Save to persist.")
    up_map = st.file_uploader("📤 Upload Mapping CSV (must include Role/Mapped Role; optional Department/Group; optional Business Line)", type=["csv"])
    if up_map:
        try:
            df = pd.read_csv(up_map)
            # normalize
            cmap = {c.lower().strip(): c for c in df.columns}
            role_col = cmap.get("mapped role") or cmap.get("role")
            if not role_col: st.stop()
            dept_col = cmap.get("department") or cmap.get("dept") or cmap.get("staffing ratio group") or cmap.get("group")
            bl_col   = cmap.get("business line") or cmap.get("biz line") or cmap.get("line")
            new = pd.DataFrame({"Role": df[role_col].astype(str).str.strip()})
            new["Department"]    = df[dept_col].astype(str).str.strip() if dept_col else "Unassigned"
            new["Business Line"] = df[bl_col].astype(str).str.strip() if bl_col else "All"
            st.session_state.mapping = new.drop_duplicates()
            st.session_state.roles = sorted(st.session_state.mapping["Role"].unique().tolist())
            st.success("Mapping loaded into app state.")
        except Exception as e:
            st.error(f"Couldn't read mapping CSV: {e}")

    if st.button("💾 Save Mapping to CSV (title_mapping_saved.csv)"):
        st.session_state.mapping.to_csv("title_mapping_saved.csv", index=False)
        st.success("Saved title_mapping_saved.csv")

    st.dataframe(st.session_state.mapping, use_container_width=True)

# ---------- Helpers ----------
def attach_dept_bl(df):
    if df.empty: return df.assign(Department="Unassigned", **({"Business Line":"All"} if "Business Line" not in df.columns else {}))
    m = st.session_state.mapping
    if m.empty: return df.assign(Department="Unassigned", **({"Business Line":"All"} if "Business Line" not in df.columns else {}))
    return df.merge(m, on="Role", how="left")

def pivot_months(df, value_col):
    if df.empty:
        base = pd.DataFrame({"Department":[],"Business Line":[],"Role":[]})
        for mo in MONTHS: base[mo] = []
        return base
    idx_cols = [c for c in ["Department","Business Line","Role"] if c in df.columns]
    pvt = df.pivot_table(index=idx_cols, columns="Month", values=value_col, aggfunc="sum").reindex(columns=MONTHS).fillna(0).astype(int)
    return pvt.reset_index()

def add_totals(df, group_cols, label="Total HC"):
    if df.empty: return df
    parts = []
    for keys, sub in df.groupby(group_cols, sort=False):
        parts.append(sub)
        tot = {c: keys[i] for i, c in enumerate(group_cols)} if isinstance(keys, tuple) else {group_cols[0]: keys}
        tot.update({"Role": label})
        for mo in MONTHS:
            if mo in sub.columns: tot[mo] = int(sub[mo].sum())
        parts.append(pd.DataFrame([tot]))
    return pd.concat(parts, ignore_index=True)

# ---------- Headcount ----------
if page == "👥 Headcount":
    st.title("👥 Headcount — Planned vs Actual")
    sel_month = st.selectbox("Month", ["All"] + MONTHS, index=(MONTHS.index(CURRENT_MONTH)+1))
    sel_bl = st.selectbox("Business Line", business_lines(), index=0)
    sel_dept = st.selectbox("Department", departments(), index=0)
    st.caption("Variance = Planned − Actual.")

    # Upload
    c1, c2 = st.columns(2)
    with c1:
        up_plan = st.file_uploader("📤 Upload Planned (Role, Month, Planned)", type=["csv"])
        if up_plan:
            df = pd.read_csv(up_plan)
            if set(["Role","Month","Planned"]).issubset(df.columns):
                df["Month"] = df["Month"].apply(lambda x: x if x in MONTHS else str(x))
                st.session_state.planned = df[["Role","Month","Planned"]].copy()
                st.success("Planned loaded.")
            else:
                st.error("Planned CSV must have columns: Role, Month, Planned")
    with c2:
        up_act = st.file_uploader("📤 Upload Actual (Role, Month, Actual)", type=["csv"])
        if up_act:
            df = pd.read_csv(up_act)
            if set(["Role","Month","Actual"]).issubset(df.columns):
                df["Month"] = df["Month"].apply(lambda x: x if x in MONTHS else str(x))
                st.session_state.actual = df[["Role","Month","Actual"]].copy()
                st.success("Actual loaded.")
            else:
                st.error("Actual CSV must have columns: Role, Month, Actual")

    plan = attach_dept_bl(st.session_state.planned)
    act  = attach_dept_bl(st.session_state.actual)

    if sel_bl != "All":
        plan = plan.query("`Business Line` == @sel_bl")
        act  = act .query("`Business Line` == @sel_bl")
    if sel_dept != "All":
        plan = plan.query("Department == @sel_dept")
        act  = act .query("Department == @sel_dept")

    wide_plan = pivot_months(plan, "Planned")
    wide_act  = pivot_months(act , "Actual")

    if sel_month != "All":
        wp = wide_plan[["Department","Business Line","Role", sel_month]].rename(columns={sel_month:"Planned"})
        wa = wide_act [ ["Department","Business Line","Role", sel_month]].rename(columns={sel_month:"Actual"})
        wv = wp.merge(wa, on=["Department","Business Line","Role"], how="outer").fillna(0)
        wv["Variance"] = wv["Planned"].astype(int) - wv["Actual"].astype(int)

        st.markdown('<div class="bluehdr">Plan (F1)</div>', unsafe_allow_html=True)
        st.dataframe(wp, use_container_width=True)
        st.markdown('<div class="sectionhdr">Actuals</div>', unsafe_allow_html=True)
        st.dataframe(wa, use_container_width=True)
        st.markdown('<div class="sectionhdr">Variance (Plan − Actual)</div>', unsafe_allow_html=True)
        st.dataframe(wv[["Department","Business Line","Role","Variance"]], use_container_width=True)
    else:
        # Annual view with totals at Department + Business Line
        st.markdown('<div class="bluehdr">Plan (F1)</div>', unsafe_allow_html=True)
        st.dataframe(add_totals(wide_plan, ["Department","Business Line"]), use_container_width=True)
        st.markdown('<div class="sectionhdr">Actuals</div>', unsafe_allow_html=True)
        st.dataframe(add_totals(wide_act , ["Department","Business Line"]), use_container_width=True)
        # Variance grid
        wide_var = wide_plan.copy()
        for mo in MONTHS:
            wide_var[mo] = wide_plan.get(mo, 0) - wide_act.get(mo, 0)
        st.markdown('<div class="sectionhdr">Variance (Plan − Actual)</div>', unsafe_allow_html=True)
        st.dataframe(add_totals(wide_var, ["Department","Business Line"]), use_container_width=True)

# ---------- Ratios ----------
if page == "📈 Ratios":
    st.title("📈 Homes per Headcount (Actuals)")
    sel_month = st.selectbox("Month", MONTHS, index=MONTHS.index(CURRENT_MONTH))
    sel_bl    = st.selectbox("Business Line", business_lines(), index=0)
    sel_dept  = st.selectbox("Department", departments(), index=0)

    total_homes = int(st.session_state.homes["Units"].sum()) if not st.session_state.homes.empty else 0

    act = attach_dept_bl(st.session_state.actual)
    if sel_bl != "All":
        act = act.query("`Business Line` == @sel_bl")
    if sel_dept != "All":
        act = act.query("Department == @sel_dept")

    month_actuals = act.query("Month == @sel_month").copy()
    # Summaries by Department + Business Line + Role
    role_sums = month_actuals.groupby(["Department","Business Line","Role"], as_index=False)["Actual"].sum()

    rows = []
    for _, r in role_sums.iterrows():
        hc = int(r["Actual"])
        ratio = (total_homes / hc) if hc > 0 else None
        rows.append({
            "Business Line": r["Business Line"],
            "Department": r["Department"],
            "Role": r["Role"],
            "Actual HC": hc,
            "Homes per HC": (round(ratio,2) if ratio else "⚠️ No coverage")
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    total_hc = int(role_sums["Actual"].sum()) if not role_sums.empty else 0
    total_ratio = (total_homes / total_hc) if total_hc > 0 else None
    if total_ratio:
        st.markdown(f"### 📊 Total: {total_homes:,} Homes / {total_hc:,} Staff = **{total_ratio:.2f} Homes per Headcount**")
    else:
        st.warning("⚠️ Not enough staffing to calculate total ratio.")
