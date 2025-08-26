import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
import re

st.set_page_config(page_title="Roostock Property Ops Dashboard", layout="wide")

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CURRENT_MONTH = MONTHS[datetime.now().month-1]

# --- Title Mapping seed ---
def load_title_mapping():
    path = "Title Mapping.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        df = df.rename(columns={
            "Job Title in Bamboo": "HRIS Title",
            "Role": "Mapped Role"
        })
        return df[["HRIS Title","Mapped Role"]]
    else:
        return pd.DataFrame({
            "HRIS Title": ["Leasing Associate"],
            "Mapped Role": ["Leasing Associate"]
        })

SEED_MAPPING = load_title_mapping()
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

# --- Normalize wide/long format Planned/Actual uploads ---
def normalize_plan_actual_upload(df, type_col):
    month_cols = [c for c in df.columns if c in MONTHS]
    if month_cols:
        id_vars = [c for c in df.columns if c not in MONTHS]
        df_long = df.melt(id_vars=id_vars,
                          value_vars=month_cols,
                          var_name="Month",
                          value_name=type_col)
        keep_cols = ["Role","Month",type_col]
        if "Business Line" in df_long.columns:
            keep_cols.insert(0,"Business Line")
        df_long = df_long[keep_cols]
    else:
        df_long = df.copy()
    return df_long

# --- Session state init ---
if "title_mapping" not in st.session_state:
    st.session_state.title_mapping = load_mapping()
if "planned" not in st.session_state:
    st.session_state.planned = pd.DataFrame(columns=["Business Line","Role","Month","Planned"])
if "actual" not in st.session_state:
    st.session_state.actual = pd.DataFrame(columns=["Business Line","Role","Month","Actual"])
if "homes" not in st.session_state:
    st.session_state.homes = pd.DataFrame([
        {"Property Type":"Single-Family Rental","Units":15000},
        {"Property Type":"Short Term Rental","Units":4300},
    ])

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
    total_actual = int(st.session_state.actual.query("Month == @m")["Actual"].sum()) if not st.session_state.actual.empty else 0
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

# --- Role Headcount ---
if page == "👥 Role Headcount":
    st.title("👥 Role Headcount — Annual (Planned vs Actual)")
    sel_month = st.selectbox("Month", ["All"] + MONTHS, index=(MONTHS.index(CURRENT_MONTH)+1 if CURRENT_MONTH in MONTHS else 0))

    colu1, colu2 = st.columns(2)
    with colu1:
        up_plan = st.file_uploader("📤 Upload Planned (wide or long format)", type=["csv"], key="up_plan")
        if up_plan:
            df = pd.read_csv(up_plan)
            if "Role" in df.columns:
                st.session_state.planned = normalize_plan_actual_upload(df,"Planned")
                st.success("Planned loaded.")
            else:
                st.error("Planned CSV must include Role + months.")
    with colu2:
        up_act = st.file_uploader("📤 Upload Actual (wide or long format)", type=["csv"], key="up_act")
        if up_act:
            df = pd.read_csv(up_act)
            if "Role" in df.columns:
                st.session_state.actual = normalize_plan_actual_upload(df,"Actual")
                st.success("Actual loaded.")
            else:
                st.error("Actual CSV must include Role + months.")

    plan = st.session_state.planned
    act = st.session_state.actual

    if not plan.empty and not act.empty:
        wide_plan = plan.pivot_table(index=["Business Line","Role"], columns="Month", values="Planned", aggfunc="sum").reindex(columns=MONTHS).fillna(0).astype(int).reset_index()
        wide_act  = act.pivot_table(index=["Business Line","Role"], columns="Month", values="Actual", aggfunc="sum").reindex(columns=MONTHS).fillna(0).astype(int).reset_index()
        if sel_month != "All":
            month = sel_month
            p = wide_plan[["Business Line","Role",month]].rename(columns={month:"Planned"})
            a = wide_act[["Business Line","Role",month]].rename(columns={month:"Actual"})
            v = p.merge(a,on=["Business Line","Role"],how="outer").fillna(0)
            v["Variance"] = v["Planned"].astype(int) - v["Actual"].astype(int)
            st.dataframe(v,use_container_width=True)
        else:
            var = wide_plan.copy()
            for m in MONTHS:
                var[m] = wide_plan[m] - wide_act[m]
            st.dataframe(var,use_container_width=True)

# --- Ratios ---
if page == "📈 Ratios":
    st.title("📈 Ratios: Homes per Headcount (Actuals)")
    sel_month = st.selectbox("Month", MONTHS, index=(MONTHS.index(CURRENT_MONTH) if CURRENT_MONTH in MONTHS else 0))
    total_homes = int(st.session_state.homes["Units"].sum()) if not st.session_state.homes.empty else 0
    act = st.session_state.actual
    if not act.empty:
        month_actuals = act.query("Month == @sel_month").copy()
        role_sums = month_actuals.groupby(["Role"], as_index=False)["Actual"].sum()
        rows = []
        for _, r in role_sums.iterrows():
            role = r["Role"]; hc = int(r["Actual"])
            ratio = (total_homes / hc) if hc>0 else None
            rows.append({"Role": role,"Actual HC": hc,"Homes per HC": (round(ratio,2) if ratio else "⚠️ No coverage")})
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
