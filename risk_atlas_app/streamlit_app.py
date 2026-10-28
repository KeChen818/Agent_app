"""Risk Atlas entry point: page setup, shared sidebar, navigation.

Run with:  streamlit run streamlit_app.py
"""
import streamlit as st

from core import data, ui

st.set_page_config(page_title="Risk Atlas", page_icon=str(ui.ICON), layout="wide")
st.logo(ui.LOGO, size="large", icon_image=ui.ICON)
ui.inject_css()

# Shared filter: defined here so it stays on every page
df = data.load_inventory(data.data_version())
all_cats = sorted(df["Category"].unique())
with st.sidebar:
    st.multiselect("Categories", all_cats, default=all_cats, key="categories")
    st.caption(f"Data as of {data.last_updated():%b %d, %Y · %H:%M}")

pages = {
    "Analyse": [st.Page("app_pages/dashboard.py", title="Dashboard",
                        icon=":material/space_dashboard:", default=True)],
    "Assistant": [st.Page("app_pages/chat.py", title="AI Chat", icon=":material/forum:")],
}
st.navigation(pages).run()
