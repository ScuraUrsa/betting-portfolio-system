"""Betting Portfolio System — Streamlit Dashboard.

Run with: streamlit run ui/app.py
"""

import streamlit as st
import traceback

st.set_page_config(
    page_title="Betting Portfolio System",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0

st.sidebar.title("🎲 Betting Portfolio")
st.sidebar.markdown("---")
st.sidebar.metric("Bankroll", f"{st.session_state.bankroll:,.0f} zł")

page = st.sidebar.radio(
    "Navigation",
    ["🎓 Tutorial", "🎰 Roulette", "🃏 Poker", "📊 Portfolio", "📈 History & Signals", "⚙️ Settings"],
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Game-agnostic portfolio optimization\n"
    "Z-score · Extremum Index · Kelly · Monte Carlo"
)

try:
    if page == "🎓 Tutorial":
        from ui.views.tutorial import show
    elif page == "🎰 Roulette":
        from ui.views.roulette import show
    elif page == "🃏 Poker":
        from ui.views.poker import show
    elif page == "📊 Portfolio":
        from ui.views.portfolio import show
    elif page == "📈 History & Signals":
        from ui.views.history import show
    elif page == "⚙️ Settings":
        from ui.views.settings import show
    show()
except Exception as e:
    st.error(f"Page crashed: {e}")
    st.code(traceback.format_exc())
