"""Poker recommendations page."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from games.poker import texas_holdem_hand_rankings
from core.history import HistoryEngine
from core.extremum import ExtremumEngine
from core.value import ValueEngine
from core.portfolio import PortfolioEngine
from core.monte_carlo import MonteCarloEngine
from core.risk import RiskManager


def show():
    st.title("🃏 Poker — Texas Hold'em Hand Rankings")

    game = texas_holdem_hand_rankings()
    history = HistoryEngine("data/poker_history.db")
    extremum = ExtremumEngine(history)
    value_engine = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)
    mc = MonteCarloEngine(seed=42)
    risk_mgr = RiskManager()

    tab1, tab2 = st.tabs(["📋 Recommendations", "🎯 Monte Carlo"])

    with tab1:
        st.subheader("Hand Ranking Bets")

        extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
        value_results = value_engine.analyze_all(game, extremum_results)

        rows = []
        for vr in value_results:
            ext = extremum_results.get(vr.bet_id)
            rows.append({
                "Hand": vr.bet_name,
                "Probability": f"{vr.probability*100:.4f}%",
                "Odds": f"{vr.odds:.1f}",
                "EV": f"{vr.ev:+.4f}",
                "Kelly 1/4": f"{vr.kelly_quarter:.4f}",
                "Signal": ext.signal_level if ext else "none",
                "Rec. Stake %": f"{vr.recommended_stake_pct:.2%}",
                "Rec. Stake zł": f"{vr.recommended_stake_pct * st.session_state.bankroll:.2f}",
            })

        st.dataframe(rows, width='stretch', hide_index=True)

        # Probability distribution chart
        fig = go.Figure()
        probs = [b.probability for b in game.bets]
        names = [b.name for b in game.bets]
        fig.add_trace(go.Bar(
            x=names, y=probs,
            marker_color="steelblue",
            text=[f"{p*100:.4f}%" for p in probs],
            textposition="outside",
        ))
        fig.update_layout(
            title="Hand Probability Distribution",
            yaxis_title="Probability",
            height=400,
        )
        st.plotly_chart(fig, width='stretch')

    with tab2:
        st.subheader("Monte Carlo Simulation")

        n_sims = st.slider("Simulations", 1000, 100000, 10000, step=1000, key="poker_mc")

        if st.button("Run Monte Carlo", type="primary", key="poker_mc_btn"):
            with st.spinner(f"Running {n_sims:,} simulations..."):
                extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
                value_results = value_engine.analyze_all(game, extremum_results)
                allocation = portfolio.optimize(game, value_results)

                result = mc.simulate_independent(game, allocation, n_simulations=n_sims)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Expected Return", f"{result.expected_return:+.2f} zł")
            col2.metric("Std Dev", f"{result.std_return:.2f} zł")
            col3.metric("Max Drawdown", f"{result.max_drawdown:.2f} zł")
            col4.metric("Ruin Probability", f"{result.ruin_probability:.2%}")

            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=result.profit_distribution, nbinsx=100,
                marker_color="steelblue", opacity=0.7,
            ))
            fig.add_vline(x=0, line_dash="dash", line_color="red")
            fig.add_vline(x=result.expected_return, line_dash="dash", line_color="green")
            fig.update_layout(
                title=f"Profit Distribution ({n_sims:,} simulations)",
                xaxis_title="Profit (zł)", yaxis_title="Frequency", height=400,
            )
            st.plotly_chart(fig, width='stretch')


