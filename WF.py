
# --- Summary Section ---
shortage_summary = []
for allocation in df_status["Allocation"]:
    total_short = 0
    for quarter in ["Q1 Status", "Q2 Status", "Q3 Status", "Q4 Status"]:
        val = df_status.loc[df_status["Allocation"] == allocation, quarter].values[0]
        if "❌" in val:
            try:
                num = float(val.split("+")[1])
                total_short += num
            except:
                continue
    if total_short > 0:
        shortage_summary.append(f"❌ {allocation}: need {round(total_short, 1)} more recruiters")

if shortage_summary:
    st.markdown(f"### 🔴 You are **under-resourced** in {len(shortage_summary)} department(s):")
    for item in shortage_summary:
        st.markdown(f"- {item}")
else:
    st.markdown("### ✅ All departments are fully staffed for their quarterly targets.")
