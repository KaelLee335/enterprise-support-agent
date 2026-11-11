"""Streamlit entry point. Run with `streamlit run ui/app.py`."""
import streamlit as st

from ui.pages.chat import render as render_chat
from ui.pages.evaluation import render as render_evaluation

st.set_page_config(page_title="Enterprise Support Agent", page_icon="🛟", layout="wide")
navigation = st.navigation([
    st.Page(render_chat, title="售后对话", icon="💬", url_path="chat", default=True),
    st.Page(render_evaluation, title="评估报告", icon="📊", url_path="evaluation"),
])
navigation.run()
