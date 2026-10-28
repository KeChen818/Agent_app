# Risk Atlas

Streamlit app with a risk dashboard and an AI chat assistant.

## Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

It runs in **demo mode** out of the box: sample data and scripted AI answers built from that data.

## Make it real

| Step | Where |
|---|---|
| Use your data | Put `risk_inventory.xlsx` in `data/` with columns `ID, Risk, Category, Rating, Likelihood, Impact, Score, Owner, Status, Due, Mitigation` |
| Real trends | Put `history.csv` in `data/` with columns `Month, High, Medium, Low, Overdue, Mitigated, AvgScore` (one row per month) |
| Connect a model | `core/ai.py` → return your client from `get_client()` and set `MODEL` |
| API key | `.streamlit/secrets.toml` (never commit it) |
| Last month's KPIs | `core/data.py` → `previous_kpis()` |

## Structure

```
streamlit_app.py        Entry: page config, logo, shared sidebar filter, navigation
app_pages/
  dashboard.py          KPIs + sparklines, AI summary, three tabs:
                        Overview (ECharts heat map, rating mix, trend, status donut),
                        Risk profile (per-category metrics, AI commentary, analyst comments),
                        Risk register (top risks, overdue list)
  chat.py               AI chat
core/
  data.py               Loading (cached by file version), history, category profile
  charts.py             ECharts option builders in Risk Atlas colors
  comments.py           Analyst comments in SQLite (data/comments.db)
  ai.py                 Model calls, prompts, demo mode
  export.py             Word / Excel / Markdown export
  ui.py                 CSS, headers, AI summary box, avatars
assets/                 Logo files
.streamlit/config.toml  Theme
```

## Caching

| What | How |
|---|---|
| Inventory | `st.cache_data`, keyed by the file's modified time |
| Dashboard AI summary | `st.cache_data`, keyed by data version + selected categories (shared by all users) |
| Category AI commentary | `st.cache_data`, keyed by data version + category (shared by all users) |
| Analyst comments | SQLite file, shared and permanent (not a cache) |
| LLM client | `st.cache_resource` |
| Chat history | `st.session_state` (private per browser session) |
| Chat answers | Not cached |

## Notes

- Charts use `st.echarts_chart` (Streamlit 1.64+). Options are plain dicts in `core/charts.py`;
  JavaScript callbacks are not supported, so labels use ECharts string templates like `{@[2]}`.
- `data/comments.db` holds team comments. Back it up, and keep it on a company server.
- The Dashboard tabs sync to the URL (`?view=Risk+profile`), so a tab can be shared as a link.
