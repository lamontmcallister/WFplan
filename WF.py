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
  .hdr { background:#0b5ed7; color:#fff; padding:6px 10px; border-radius:6px; display:inline-block; margin: 10px 0;}
</style>
""", unsafe_allow_html=True)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CURRENT_MONTH = MONTHS[datetime.now().month-1]

# ---------- Helpers ----------
MAPPING_BASENAME = "PM HC Trend by Department - 1. Title Mapping.csv"

def _guess_col(df, candidates):
    for key in candidates:
        for c in df.columns:
            if key in c.lower():
                return c
    return None

def load_role_group_mapping():
    """
    Load Role->Group mapping from the official CSV if present.
    """
    if os.path.exists(MAPPING_BASENAME):
        try:
            raw = pd.read_csv(MAPPING_BASENAME)
            role_col  = _guess_col(raw, ["mapped role","role","staffing ratio name","staffing ratio names"])
            group_col = _guess_col(raw, ["group","department","staffing ratio group","dept"])
            if role_col and group_col:
                rg = raw[[role_col, group_col]].rename(columns={role_col:"Role", group_col:"Group"})
                rg["Role"] = rg["Role"].astype(str).str.strip()
                rg["Group"] = rg["Group"].astype(str).str.strip()
                return rg.drop_duplicates().reset_index(drop=True)
        except Exception as e:
            st.warning(f"Couldn't read mapping CSV '{MAPPING_BASENAME}': {e}")

    # fallback minimal
    return pd.DataFrame({
        "Role":["Accounting Assistant","Accounts Payable","Property Accountant","Service Technician","Property Manager","Leasing Associate"],
        "Group":["41003 PM Accounting","41003 PM Accounting","41003 PM Accounting","41011 Maintenance Techs","41010 Portfolio Management","41021 Leasing"]
    })

def ensure_demo_homes():
    if os.path.exists("demo_homes_data.csv"):
        try:
            df = pd.read_csv("demo_homes_data.csv")[["Property Type","Units"]]
            if not df.empty: return df
        except: pass
    return pd.DataFrame([
        {"Property Type":"Single-Family Rental","Units":15000},
        {"Property Type":"Short Term Rental","Units":4300},
    ])

def blank_plan_actual(colname, roles):
    rows = []
    for r in roles:
        for m in MONTHS:
            rows.append({"Role": r, "Month": m, colname: 0})
    return pd.DataFrame(rows)

# ---------- Session init ----------
if "role_groups" not in st.session_state:
    st.session_state.role_groups = load_role_group_mapping()

CANONICAL_ROLES = sorted(st.session_state.role_groups["Role"].unique().tolist())
DEPARTMENTS = ["All"] + sorted(st.session_state.role_groups["Group"].unique().tolist())

if "homes" not in st.session_state:
    st.session_state.homes = ensure_demo_homes()

if "planned" not in st.session_state:
    st.session_state.planned = blank_plan_actual("Planned", CANONICAL_ROLES)
if "actual" not in st.session_state:
    st.session_state.actual = blank_plan_actual("Actual", CANONICAL_ROLES)

# ---------- Navigation ----------
NAV = {
    "🏠 Overview": [],
    "🏘️ Homes Under Management": ["👥 Role Headcount", "🗺️ Title Mapping", "📈 Ratios"]
}
page = st.sidebar.radio("Go to", list(NAV.keys()) + sum(NAV.values(), []))

# ---------- Overview ----------
if page == "🏠 Overview":
    st.title("Roostock Property Ops Dashboard")
    total_homes = int(st.session_state.homes["Units"].sum())
    m = CURRENT_MONTH
    total_actual = int(st.session_state.actual.query("Month == @m")["Actual"].sum())
    col1, col2 = st.columns(2)
    col1.metric("🏘️ Total Homes", f"{total_homes:,}")
    col2.metric(f"👥 Actual HC ({m})", f"{total_actual:,}")
    st.caption("Ratios use **Actuals** for the selected month.")

# ---------- Homes Under Management ----------
if page == "🏘️ Homes Under Management":
    st.title("🏘️ Homes Under Management")
    st.dataframe(st.session_state.homes, use_container_width=True)

    if not st.session_state.homes.empty:
        idx = st.number_input("Row index to delete", min_value=0, max_value=len(st.session_state.homes)-1, step=1)
        if st.button("Delete Home"):
            st.session_state.homes.drop(index=idx, inplace=True)
            st.session_state.homes.reset_index(drop=True, inplace=True)

    with st.expander("➕ Add Home"):
        ptype = st.selectbox("Property Type", ["Single-Family Rental","Short Term Rental"])
        units = st.number_input("Units", min_value=1, step=1)
        if st.button("Add"):
            st.session_state.homes = pd.concat(
                [st.session_state.homes, pd.DataFrame([{"Property Type": ptype, "Units": int(units)}])],
                ignore_index=True
            )

    up = st.file_uploader("📤 Upload CSV (Property Type, Units)", type=["csv"])
    if up:
        df = pd.read_csv(up)
        if set(["Property Type","Units"]).issubset(df.columns):
            st.session_state.homes = df[["Property Type","Units"]].copy()
        else:
            st.error("CSV must include Property Type, Units")

# ---------- Title Mapping ----------
if page == "🗺️ Title Mapping":
    st.title("🗺️ Title Mapping (Role → Department)")
    st.caption("Auto-loads official CSV if present.")

    st.dataframe(st.session_state.role_groups, use_container_width=True)

# ---------- Role Headcount ----------
if page == "👥 Role Headcount":
    st.title("👥 Role Headcount")
    sel_month = st.selectbox("Month", ["All"]+MONTHS, index=(MONTHS.index(CURRENT_MONTH)+1))
    sel_dept = st.selectbox("Department", DEPARTMENTS, index=0)

    # Merge mapping
    rg = st.session_state.role_groups.copy()
    plan_g = st.session_state.planned.merge(rg,on="Role",how="left")
    act_g  = st.session_state.actual.merge(rg,on="Role",how="left")

    # Warn on unmapped
    missing = sorted(set(plan_g[plan_g["Group"].isna()]["Role"]).union(set(act_g[act_g["Group"].isna()]["Role"])))
    if missing:
        st.error("⚠️ Unmapped roles: "+", ".join(missing[:10]))

    if sel_dept!="All":
        plan_g=plan_g.query("Group==@sel_dept"); act_g=act_g.query("Group==@sel_dept")

    def pivot(df,val):
        p=df.pivot_table(index=["Group","Role"],columns="Month",values=val,aggfunc="sum").reindex(columns=MONTHS).fillna(0).astype(int)
        return p.reset_index() if not df.empty else pd.DataFrame()

    wide_plan=pivot(plan_g,"Planned"); wide_act=pivot(act_g,"Actual")

    if sel_month!="All":
        wp=wide_plan[["Group","Role",sel_month]].rename(columns={sel_month:"Planned"})
        wa=wide_act [["Group","Role",sel_month]].rename(columns={sel_month:"Actual"})
        var=wp.merge(wa,on=["Group","Role"],how="outer").fillna(0)
        var["Variance"]=var["Planned"].astype(int)-var["Actual"].astype(int)
        st.dataframe(var,use_container_width=True)
    else:
        wide_var=wide_plan.copy()
        for m in MONTHS: wide_var[m]=wide_plan.get(m,0)-wide_act.get(m,0)
        st.dataframe(wide_var,use_container_width=True)

# ---------- Ratios ----------
if page == "📈 Ratios":
    st.title("📈 Ratios: Homes per HC (Actuals)")
    sel_month = st.selectbox("Month", MONTHS, index=MONTHS.index(CURRENT_MONTH))
    sel_dept = st.selectbox("Department", DEPARTMENTS, index=0)

    act = st.session_state.actual.merge(st.session_state.role_groups,on="Role",how="left")
    if sel_dept!="All": act=act.query("Group==@sel_dept")

    month_act = act.query("Month==@sel_month")
    role_sums = month_act.groupby(["Group","Role"],as_index=False)["Actual"].sum()

    total_homes = int(st.session_state.homes["Units"].sum())
    rows=[]
    for _,r in role_sums.iterrows():
        hc=int(r["Actual"]); ratio=round(total_homes/hc,2) if hc>0 else None
        rows.append({"Group":r["Group"],"Role":r["Role"],"Actual HC":hc,"Homes per HC":ratio or "⚠️"})
    df=pd.DataFrame(rows)
    st.dataframe(df,use_container_width=True)

    total_hc=int(role_sums["Actual"].sum())
    if total_hc>0:
        st.markdown(f"### 📊 Total: {total_homes:,} / {total_hc:,} = {total_homes/total_hc:.2f} Homes per HC")
