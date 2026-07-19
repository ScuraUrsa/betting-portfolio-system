"""Betting Portfolio System — Streamlit Dashboard.

Run with: streamlit run ui/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Betting Portfolio System",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import all page modules
from ui.pages import tutorial, roulette, poker, portfolio, history, settings

# Navigation
PAGES = {
    "🎓 Tutorial": tutorial,
    "🎰 Roulette": roulette,
    "🃏 Poker": poker,
    "📊 Portfolio": portfolio,
    "📈 History & Signals": history,
    "⚙️ Settings": settings,
}


def main():
    st.sidebar.title("🎲 Betting Portfolio")
    st.sidebar.markdown("---")

    # Bankroll display
    if "bankroll" not in st.session_state:
        st.session_state.bankroll = 1000.0

    st.sidebar.metric("Bankroll", f"{st.session_state.bankroll:,.0f} zł")

    # Navigation
    page_name = st.sidebar.radio("Navigation", list(PAGES.keys()))

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Game-agnostic portfolio optimization\n"
        "Z-score · Extremum Index · Kelly · Monte Carlo"
    )

    # Run the selected page
    page_module = PAGES[page_name]
    page_module.show()


if __name__ == "__main__":
    main()
