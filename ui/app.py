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

# Navigation
pages = {
    "🎰 Roulette": "ui/pages/roulette.py",
    "🃏 Poker": "ui/pages/poker.py",
    "📊 Portfolio": "ui/pages/portfolio.py",
    "📈 History & Signals": "ui/pages/history.py",
    "⚙️ Settings": "ui/pages/settings.py",
}


def main():
    st.sidebar.title("🎲 Betting Portfolio")
    st.sidebar.markdown("---")

    # Bankroll display
    if "bankroll" not in st.session_state:
        st.session_state.bankroll = 1000.0

    st.sidebar.metric("Bankroll", f"{st.session_state.bankroll:,.0f} zł")

    # Navigation
    page = st.sidebar.radio("Navigation", list(pages.keys()))

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Game-agnostic portfolio optimization\n"
        "Z-score · Extremum Index · Kelly · Monte Carlo"
    )

    # Run the selected page
    page_path = pages[page]
    exec(open(page_path).read())


if __name__ == "__main__":
    main()
