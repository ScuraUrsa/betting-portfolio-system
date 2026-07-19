"""Betting Portfolio System — Streamlit Dashboard.

Run with: streamlit run ui/app.py
"""

import streamlit as st
import traceback

from core.i18n import Translator

st.set_page_config(
    page_title="Betting Portfolio System",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ────────────────────────────────────────────────
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0
if "lang" not in st.session_state:
    st.session_state.lang = "en"

t = Translator()
t.set_lang(st.session_state.lang)

# ── Sidebar ───────────────────────────────────────────────────────────
st.sidebar.title("🎲 Betting Portfolio")
st.sidebar.markdown("---")
st.sidebar.metric(t.t("bankroll_label"), f"{st.session_state.bankroll:,.0f} zł")

page = st.sidebar.radio(
    t.t("navigation_label"),
    [
        t.t("nav_tutorial"),
        t.t("nav_roulette"),
        t.t("nav_poker"),
        t.t("nav_portfolio"),
        t.t("nav_history"),
        t.t("nav_settings"),
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption(t.t("app_tagline"))

# ── Page routing ──────────────────────────────────────────────────────
try:
    if page == t.t("nav_tutorial"):
        from ui.views.tutorial import show
    elif page == t.t("nav_roulette"):
        from ui.views.roulette import show
    elif page == t.t("nav_poker"):
        from ui.views.poker import show
    elif page == t.t("nav_portfolio"):
        from ui.views.portfolio import show
    elif page == t.t("nav_history"):
        from ui.views.history import show
    elif page == t.t("nav_settings"):
        from ui.views.settings import show
    show()
except Exception as e:
    st.error(t.t("page_crashed", error=str(e)))
    st.code(traceback.format_exc())
