

# ----------------- Page 1: Headcount Adjustments -----------------
if page == "Headcount Adjustments":
    st.title("📊 Headcount Adjustments")
    st.markdown("Adjust headcount inputs across departments. Totals update in real time.")

    edited_df = st.data_editor(df_headcount, num_rows="dynamic")
    edited_df["Total Headcount"] = edited_df[
        ["Employees in seat", "Future Starts", "FY26 Planned + Open", "FY26 Planned - not yet opened"]
    ].sum(axis=1)
    st.session_state.headcount_data = edited_df

    df_allocation_summary = edited_df.groupby("Allocation").sum(numeric_only=True).reset_index()
    df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
        lambda row: row["Total Headcount"] * default_attrition_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

    st.subheader("📌 Summary by Allocation")
    st.dataframe(df_allocation_summary)

    st.subheader("📈 Hiring Goals by Quarter (Line Chart)")
    chart_data = df_allocation_summary.copy()
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        chart_data[q] = chart_data["Final_Hiring_Target"] * 0.25
    df_long = chart_data.melt(id_vars="Allocation", value_vars=["Q1", "Q2", "Q3", "Q4"], var_name="Quarter", value_name="Hires")
    fig = px.line(df_long, x="Quarter", y="Hires", color="Allocation", markers=True, title="Quarterly Hiring Goals by Allocation")
    st.plotly_chart(fig, use_container_width=True)


# ----------------- Page 2: Adjusted Hiring Goals -----------------
if page == "Adjusted Hiring Goals":
    st.title("📈 Adjusted Hiring Goals")
    st.sidebar.subheader("Adjust Attrition Rate for Selected Allocation")
    selected_allocation = st.sidebar.selectbox("Choose Allocation", df_allocation_summary["Allocation"].unique())
    new_rate = st.sidebar.slider("Attrition Rate (%)", 0, 50, int(default_attrition_rates[selected_allocation] * 100), 1)
    default_attrition_rates[selected_allocation] = new_rate / 100

    df_allocation_summary["Attrition Impact"] = df_allocation_summary.apply(
        lambda row: row["Total Headcount"] * default_attrition_rates[row["Allocation"]],
        axis=1
    )
    df_allocation_summary["Final_Hiring_Target"] = df_allocation_summary["Total Headcount"] + df_allocation_summary["Attrition Impact"]

    st.subheader("📌 Final Hiring Targets After Attrition")
    st.dataframe(df_allocation_summary)

    st.subheader("📉 Final Hiring Targets by Quarter (Line Chart)")
    chart_data = df_allocation_summary.copy()
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        chart_data[q] = chart_data["Final_Hiring_Target"] * 0.25
    df_long = chart_data.melt(id_vars="Allocation", value_vars=["Q1", "Q2", "Q3", "Q4"], var_name="Quarter", value_name="Hires")
    fig = px.line(df_long, x="Quarter", y="Hires", color="Allocation", markers=True, title="Final Hiring Targets by Quarter")
    st.plotly_chart(fig, use_container_width=True)


# ----------------- Page 3: Recruiter Capacity Model -----------------
if page == "Recruiter Capacity Model":
    st.title("🧮 Recruiter Capacity by Quarter")
    st.markdown("Track quarterly hiring needs and recruiter sufficiency by role level.")

    quarters = ["Q1", "Q2", "Q3", "Q4"]
    level_productivity = {1: 15, 2: 12, 3: 10, 4: 8, 5: 6, 6: 4, 7: 3, 8: 2}

    summary_rows = []
    for alloc in df_allocation_summary["Allocation"].unique():
        col1, col2 = st.columns(2)
        with col1:
            avg_level = st.slider(f"{alloc} - Avg Role Level", 1, 8, 4, key=f"level_{alloc}")
        with col2:
            assigned = st.number_input(f"{alloc} - Recruiters Assigned", min_value=0, value=1, key=f"recruiters_{alloc}")

        hires_per_recruiter = level_productivity[avg_level]
        total_roles = df_allocation_summary[df_allocation_summary["Allocation"] == alloc]["Final_Hiring_Target"].values[0]
        for i, q in enumerate(quarters):
            q_roles = total_roles * 0.25
            needed = round(q_roles / hires_per_recruiter, 2)
            gap = assigned - needed
            status = "✅" if gap >= 0 else f"❌ +{abs(round(gap, 1))}"
            summary_rows.append((alloc, q, q_roles, avg_level, hires_per_recruiter, needed, assigned, status))

    df_summary = pd.DataFrame(summary_rows, columns=[
        "Allocation", "Quarter", "Open Roles", "Avg Level", "Hires/Recruiter", "Recruiters Needed", "Assigned", "Status"
    ])

    st.dataframe(df_summary, use_container_width=True)


# ----------------- Page 4: Success Metrics -----------------
if page == "Success Metrics":
    st.title("📊 Success Metrics & TA Benchmarks")

    metrics_data = {
        "Metric": [
            "Avg Hires per Recruiter per Quarter",
            "Sourcer-to-Recruiter Ratio",
            "Coordinator Load (Reqs per Coordinator)",
            "Avg Time-to-Fill (days)",
            "Offer Acceptance Rate (%)"
        ],
        "Current Value": ["9.3", "1.2:1", "18", "34", "86%"],
        "Benchmark": [">= 8", "1.5:1", "< 20", "< 40", ">= 85%"]
    }

    df_metrics = pd.DataFrame(metrics_data)
    st.dataframe(df_metrics)
    st.info("Benchmarks are general estimates. Customize to your organization as needed.")
