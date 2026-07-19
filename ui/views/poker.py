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
from core.i18n import Translator


def show():
    t = Translator()
    t.set_lang(st.session_state.get("lang", "en"))

    st.title(t.t("poker_title"))

    game = texas_holdem_hand_rankings()
    history = HistoryEngine("data/poker_history.db")
    extremum = ExtremumEngine(history)
    value_engine = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)
    mc = MonteCarloEngine(seed=42)
    risk_mgr = RiskManager()

    tab1, tab2 = st.tabs([
        t.t("poker_tab_rankings"),
        t.t("poker_tab_monte_carlo"),
    ])

    with tab1:
        st.subheader(t.t("poker_rankings_title"))

        extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
        value_results = value_engine.analyze_all(game, extremum_results)

        rows = []
        for vr in value_results:
            ext = extremum_results.get(vr.bet_id)
            rows.append({
                t.t("rec_bet"): vr.bet_name,
                t.t("rec_probability"): f"{vr.probability*100:.4f}%",
                t.t("rec_odds"): f"{vr.odds:.1f}",
                t.t("rec_ev"): f"{vr.ev:+.4f}",
                t.t("rec_kelly"): f"{vr.kelly_quarter:.4f}",
                t.t("rec_signal"): ext.signal_level if ext else "none",
                t.t("rec_stake_pct"): f"{vr.recommended_stake_pct:.2%}",
                t.t("rec_stake_pln"): f"{vr.recommended_stake_pct * st.session_state.bankroll:.2f}",
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
            title=t.t("poker_distribution_title"),
            yaxis_title=t.t("rec_probability"),
            height=400,
        )
        st.plotly_chart(fig, width='stretch')

    with tab2:
        st.subheader(t.t("poker_monte_carlo_title"))

        n_sims = st.slider(t.t("roulette_monte_carlo_slider"), 1000, 100000, 10000, step=1000, key="poker_mc")

        if st.button(t.t("roulette_monte_carlo_button"), type="primary", key="poker_mc_btn"):
            with st.spinner(t.t("roulette_monte_carlo_running", n=n_sims)):
                extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
                value_results = value_engine.analyze_all(game, extremum_results)
                allocation = portfolio.optimize(game, value_results)

                result = mc.simulate_independent(game, allocation, n_simulations=n_sims)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t.t("metric_expected_return"), f"{result.expected_return:+.2f} zł")
            col2.metric(t.t("metric_std_dev"), f"{result.std_return:.2f} zł")
            col3.metric(t.t("metric_max_drawdown"), f"{result.max_drawdown:.2f} zł")
            col4.metric(t.t("metric_ruin_prob"), f"{result.ruin_probability:.2%}")

            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=result.profit_distribution, nbinsx=100,
                marker_color="steelblue", opacity=0.7,
            ))
            fig.add_vline(x=0, line_dash="dash", line_color="red")
            fig.add_vline(x=result.expected_return, line_dash="dash", line_color="green")
            fig.update_layout(
                title=t.t("mc_profit_distribution", n=n_sims),
                xaxis_title="Profit (zł)", yaxis_title="Frequency", height=400,
            )
            st.plotly_chart(fig, width='stretch')
