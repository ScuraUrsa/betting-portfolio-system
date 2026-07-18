"""Settings page — configure risk limits, MRF, and bankroll."""

import streamlit as st
from core.risk import RiskLimits


def show():
    st.title("⚙️ Settings")

    tab1, tab2 = st.tabs(["💰 Bankroll & Limits", "📊 Model Parameters"])

    with tab1:
        st.subheader("Bankroll")

        new_bankroll = st.number_input(
            "Current Bankroll (zł)",
            min_value=0.0,
            value=st.session_state.bankroll,
            step=100.0,
        )
        if new_bankroll != st.session_state.bankroll:
            st.session_state.bankroll = new_bankroll
            st.success(f"Bankroll updated to {new_bankroll:,.0f} zł")

        st.markdown("---")
        st.subheader("Risk Limits")

        limits = RiskLimits()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Max per bet", f"{limits.max_per_bet:.0%}")
            st.metric("Max per hand", f"{limits.max_per_hand:.0%}")
            st.metric("Max per draw", f"{limits.max_per_draw:.0%}")
        with col2:
            st.metric("Max total exposure", f"{limits.max_total:.0%}")
            st.metric("Max drawdown", f"{limits.max_drawdown:.0%}")
            st.metric("Min bankroll", f"{limits.min_bankroll:,.0f} zł")

        st.caption("Edit these in core/risk.py → RiskLimits")

    with tab2:
        st.subheader("Extremum Index Weights")

        st.write("Default weights for Z-score aggregation:")
        weights = {
            "50": "0.10",
            "100": "0.20",
            "250": "0.30",
            "500": "0.40",
        }
        for window, weight in weights.items():
            st.write(f"- Window {window}: **{weight}**")

        st.caption("Edit in core/extremum.py → DEFAULT_EI_WEIGHTS")

        st.markdown("---")
        st.subheader("Mean Reversion Factor (MRF)")

        st.metric("Default MRF", "0.35")
        st.write("MRF is learned from historical data. Range: 0 (pure random) to 1 (full mean reversion).")
        st.caption("Edit in core/extremum.py → ExtremumEngine.__init__")

        st.markdown("---")
        st.subheader("Signal Thresholds")

        thresholds = [
            ("EI < 1.0", "No signal"),
            ("EI < 2.0", "Observation"),
            ("EI < 2.5", "Entry (small stake)"),
            ("EI < 3.0", "Medium exposure"),
            ("EI ≥ 3.0", "Maximum exposure"),
        ]
        for threshold, label in thresholds:
            st.write(f"- **{threshold}**: {label}")

        st.caption("Edit in core/extremum.py → _classify_signal")

    st.markdown("---")
    st.subheader("🧹 Data Management")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Roulette History", type="secondary"):
            from core.history import HistoryEngine
            h = HistoryEngine("data/roulette_history.db")
            h.clear_history("European Roulette")
            st.success("Roulette history cleared")
            st.rerun()

    with col2:
        if st.button("Clear Poker History", type="secondary"):
            from core.history import HistoryEngine
            h = HistoryEngine("data/poker_history.db")
            h.clear_history("Texas Hold'em Hand Rankings")
            st.success("Poker history cleared")
            st.rerun()
