"""Poker page — rankings, Monte Carlo, history, all per-session."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from games.poker import texas_holdem_hand_rankings
from core.extremum import ExtremumEngine
from core.value import ValueEngine
from core.portfolio import PortfolioEngine
from core.monte_carlo import MonteCarloEngine
from core.risk import RiskManager
from core.i18n import Translator
from core.session import SessionManager
from core.session_history_adapter import SessionHistoryAdapter


def _get_history():
    mgr: SessionManager = st.session_state.get("session_mgr")
    sid = st.session_state.get("active_session_id")
    if mgr is None or sid is None:
        return None
    return SessionHistoryAdapter(mgr, sid)


def show():
    t = Translator()
    t.set_lang(st.session_state.get("lang", "en"))

    st.title(t.t("poker_title"))

    history = _get_history()
    if history is None:
        st.warning("No active session. Create a poker session in the sidebar first.")
        return

    game = texas_holdem_hand_rankings()
    extremum = ExtremumEngine(history)
    value_engine = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)
    mc = MonteCarloEngine(seed=42)
    risk_mgr = RiskManager()

    tab1, tab2, tab3 = st.tabs([
        t.t("poker_tab_rankings"),
        t.t("poker_tab_monte_carlo"),
        "📋 History",
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

    with tab3:
        st.subheader("➕ Record Draw")
        hand_options = [(b.id, b.name) for b in game.bets]
        hand_id = st.selectbox(
            "Hand achieved",
            [h[0] for h in hand_options],
            format_func=lambda x: dict(hand_options)[x],
            key="poker_record_hand",
        )

        if st.button("Record Draw", type="primary", key="poker_record_btn"):
            draw_id = history.record_draw(game, hand_id, [hand_id])
            st.success(f"Draw #{draw_id} recorded: {dict(hand_options)[hand_id]}")
            st.rerun()

        # Quick batch
        st.markdown("---")
        c1, c2 = st.columns([1, 2])
        with c1:
            n_gen = st.slider("Generate random draws", 10, 1000, 100, key="poker_gen_slider")
        with c2:
            if st.button("Generate Random Draws", key="poker_gen_btn"):
                with st.spinner(f"Generating {n_gen} draws..."):
                    hand_ids = [b.id for b in game.bets]
                    probs = np.array([b.probability for b in game.bets])
                    probs = probs / probs.sum()
                    rng = np.random.default_rng()
                    for _ in range(n_gen):
                        hand = rng.choice(hand_ids, p=probs)
                        history.record_draw(game, hand, [hand])
                st.success(f"Generated {n_gen} random draws")
                st.rerun()

        st.markdown("---")
        st.subheader("📋 Draw History")
        total = history.count_draws(game.name)
        st.metric("Total draws", total)

        if total > 0:
            last_n = st.slider(
                "Show last N draws", min_value=5, max_value=max(10, total),
                value=min(50, total), key="poker_history_slider",
            )
            draws = history.get_draws(game.name, limit=last_n)
            if draws:
                rows = []
                for d in draws:
                    rows.append({
                        "#": d.draw_id,
                        "Time": d.timestamp[:19],
                        "Hand": d.raw_outcome,
                    })
                st.dataframe(rows, width='stretch', hide_index=True)
