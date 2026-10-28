import streamlit as st

from core import ai, charts, comments, data, ui

v = data.data_version()
df_all = data.load_inventory(v)
df = data.filtered(df_all)
hist = data.history(v)

ui.page_header("Dashboard", "Risk Overview")
st.caption(f":material/schedule: Updated {data.last_updated():%b %d, %Y · %H:%M}"
           f"  ·  {len(df)} risks across {df['Category'].nunique()} categories")

# ---------- KPIs with 6-month sparklines ----------
now, prev = data.kpis(df), data.previous_kpis(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("High risks", now["high"], now["high"] - prev["high"], delta_color="inverse",
          delta_description="vs last month", border=True,
          chart_data=list(hist["High"]), chart_type="area")  # more high risks = bad = red
c2.metric("Mitigated", now["mitigated"], now["mitigated"] - prev["mitigated"],
          delta_description="vs last month", border=True,
          chart_data=list(hist["Mitigated"]), chart_type="area")
c3.metric("Overdue actions", now["overdue"], now["overdue"] - prev["overdue"],
          delta_color="inverse", delta_description="vs last month", border=True,
          chart_data=list(hist["Overdue"]), chart_type="area")
c4.metric("Average score", f"{df['Score'].mean():.1f}",
          f"{df['Score'].mean() - hist['AvgScore'].iat[-2]:+.1f}", delta_color="inverse",
          delta_description="vs last month", help="Likelihood × impact, 1–25", border=True,
          chart_data=list(hist["AvgScore"]), chart_type="area")

ui.ai_summary(ai.dashboard_summary(v, tuple(sorted(df["Category"].unique())), ai.MODEL))

tab_overview, tab_profile, tab_register = st.tabs(
    ["Overview", "Risk profile", "Risk register"], key="view", bind="query-params")

# ======================= Overview =======================
with tab_overview:
    left, right = st.columns([1, 1.25], gap="medium")
    with left, st.container(border=True):
        ui.section("Risk heat map")
        st.caption("Likelihood × impact · number of risks in each cell")
        st.echarts_chart(charts.heatmap(df), height=370, key="heatmap",
                         alt="Heat map of risks by likelihood and impact")
    with right, st.container(border=True):
        ui.section("Rating mix by category")
        st.caption("Sorted by number of High risks")
        st.echarts_chart(charts.rating_mix(df), height=370, key="mix",
                         alt="Stacked bars of High, Medium and Low risks per category")

    left, right = st.columns([1.6, 1], gap="medium")
    with left, st.container(border=True):
        ui.section("Six-month trend")
        st.echarts_chart(charts.trend(hist), height=280, key="trend",
                         alt="High risks and overdue actions over six months")
    with right, st.container(border=True):
        ui.section("Mitigation status")
        st.echarts_chart(charts.status_donut(df), height=280, key="status",
                         alt="Share of risks by mitigation status")

# ======================= Risk profile =======================
with tab_profile:
    order = list(data.high_by_category(df).index) or sorted(df["Category"].unique())
    cat = st.segmented_control("Category", order, default=order[0], required=True,
                               key="profile_cat", label_visibility="collapsed")
    p = data.category_profile(df_all, cat)

    ui.section(f"{cat} risk profile")
    # Each card compares the category with the whole portfolio
    def pts(diff: float) -> str:
        v = round(diff * 100)
        return f"{v:+d} pts" if v else "0 pts"

    pf_over = len(data.overdue(df_all)) / len(df_all)
    cat_over = p["overdue"] / max(p["total"], 1)
    pf_mit = (df_all["Status"] == "Mitigated").mean()
    pf_score = df_all["Score"].mean()
    m = st.columns(5)
    m[0].metric("Risks", p["total"], f"{p['total'] / len(df_all):.0%} of portfolio",
                delta_color="off", delta_arrow="off", border=True)
    m[1].metric("High", p["high"], pts(p["high_share"] - p["portfolio_high_share"]),
                delta_color="inverse", delta_description="vs portfolio", border=True,
                help="This category's High share minus the portfolio's")
    m[2].metric("Overdue", p["overdue"], pts(cat_over - pf_over),
                delta_color="inverse", delta_description="vs portfolio", border=True,
                help="Overdue share of risks, compared with the portfolio")
    m[3].metric("Mitigated", f"{p['mitigated_share']:.0%}",
                pts(p["mitigated_share"] - pf_mit),
                delta_description="vs portfolio", border=True)
    m[4].metric("Average score", f"{p['avg_score']:.1f}", f"{p['avg_score'] - pf_score:+.1f}",
                delta_color="inverse", delta_description="vs portfolio", border=True)

    left, right = st.columns([1.35, 1], gap="medium")
    with left:
        ui.ai_summary(ai.category_commentary(v, cat, ai.MODEL),
                      label="AI risk commentary", key="commentary")
        with st.container(border=True):
            ui.section("Top risks")
            st.dataframe(
                p["top_risks"][["ID", "Risk", "Rating", "Owner", "Score", "Status"]]
                  .style.map(lambda r: ui.RATING_CELL.get(r, ""), subset=["Rating"]),
                hide_index=True, width="stretch")
    with right, st.container(border=True):
        ui.section("Heat map")
        st.echarts_chart(charts.heatmap(df_all[df_all["Category"] == cat]), height=330,
                         key="profile_heatmap", alt=f"Heat map of {cat} risks")

    # ---------- Analyst comments (shared, saved in SQLite) ----------
    with st.container(border=True):
        ui.section("Analyst comments")
        # Name comes from st.login when configured; otherwise ask once (kept for the session)
        name = ui.current_name() or st.text_input(
            "Your name", key="author", placeholder="Name shown with your comment")
        with st.form(f"comment_form_{cat}", clear_on_submit=True, border=False):
            body = st.text_area("Comment", placeholder=f"Add a comment on {cat} risks…",
                                height=80, label_visibility="collapsed")
            col_tag, col_btn = st.columns([3, 1], vertical_alignment="center")
            tag = col_tag.pills("Tag", ["Observation", "Action", "Escalation"],
                                default="Observation", label_visibility="collapsed")
            posted = col_btn.form_submit_button("Post comment", icon=":material/send:",
                                                width="stretch")
        if posted:
            if not body.strip() or not (name or "").strip():
                st.warning("Add your name and a comment first.")
            else:
                comments.add(cat, name, body, tag)
                st.toast("Comment posted", icon=":material/check:")

        thread = comments.list_for(cat)
        if thread.empty:
            st.caption("No comments yet. Notes posted here are visible to the whole team.")
        for c in thread.itertuples():
            st.html(ui.comment_html(c.author, c.body, c.tag, c.created))

# ======================= Risk register =======================
with tab_register:
    with st.container(border=True):
        ui.section("Top risks")
        top = (df.sort_values("Score", ascending=False)
                 .head(15)[["ID", "Risk", "Category", "Rating", "Likelihood", "Impact",
                            "Owner", "Score"]])
        st.dataframe(
            top.style.map(lambda r: ui.RATING_CELL.get(r, ""), subset=["Rating"]),
            hide_index=True, width="stretch",
            column_config={"Score": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=25, format="%d", color="#8E8D83")})

    with st.container(border=True):
        ui.section("Overdue mitigations", dot=True)
        od = data.overdue(df)[["ID", "Risk", "Category", "Owner", "Due", "Days overdue"]]
        st.dataframe(
            od.style.map(lambda d: "color:#BD000C;font-weight:600" if d >= 10 else "",
                         subset=["Days overdue"]),
            hide_index=True, width="stretch",
            column_config={"Due": st.column_config.DateColumn("Due", format="MMM DD")})
