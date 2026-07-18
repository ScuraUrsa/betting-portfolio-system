"""Roulette recommendations page."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from games.roulette import european_roulette
from core.history import HistoryEngine
from core.extremum import ExtremumEngine
from core.value import ValueEngine
from core.correlation import CorrelationEngine
from core.portfolio import PortfolioEngine
from core.monte_carlo import MonteCarloEngine
from core.risk import RiskManager


def show():
    st.title("🎰 Roulette — European (37 fields)")

    game = european_roulette()
    history = HistoryEngine("data/roulette_history.db")
    extremum = ExtremumEngine(history)
    value_engine = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)
    mc = MonteCarloEngine(seed=42)
    risk_mgr = RiskManager()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Recommendations", "📈 Signals", "🎯 Monte Carlo"])

    with tab1:
        st.subheader("Bet Recommendations")

        # Analyze all bets
        extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
        value_results = value_engine.analyze_all(game, extremum_results)

        # Build table
        rows = []
        for vr in value_results:
            ext = extremum_results.get(vr.bet_id)
            signal = ext.signal_level if ext else "none"
            direction = ext.direction if ext else "neutral"
            rows.append({
                "Bet": vr.bet_name,
                "ID": vr.bet_id,
                "Probability": f"{vr.probability:.4f}",
                "Odds": f"{vr.odds:.1f}",
                "EV": f"{vr.ev:+.4f}",
                "Kelly 1/4": f"{vr.kelly_quarter:.4f}",
                "Signal": signal,
                "Direction": direction,
                "Rec. Stake %": f"{vr.recommended_stake_pct:.2%}",
                "Rec. Stake zł": f"{vr.recommended_stake_pct * st.session_state.bankroll:.2f}",
            })

        # Sort by signal strength
        signal_order = {"maximum": 0, "medium": 1, "entry_small": 2, "observation": 3, "none": 4}
        rows.sort(key=lambda r: signal_order.get(r["Signal"], 5))

        st.dataframe(rows, use_container_width=True, hide_index=True)

        # Highlight bets with signals
        active_signals = [r for r in rows if r["Signal"] != "none"]
        if active_signals:
            st.success(f"🔔 {len(active_signals)} bets with active signals")
        else:
            st.info("No significant signals detected")

    with tab2:
        st.subheader("Extremum Index by Bet")

        # Select bet to inspect
        bet_options = [b.id for b in game.bets]
        selected = st.selectbox("Select bet", bet_options, index=0)

        if selected:
            result = extremum.analyze(game, selected)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Extremum Index", f"{result.extremum_index:.3f}")
            col2.metric("Max Z-Score", f"{result.max_z_score:.3f}")
            col3.metric("Direction", result.direction)
            col4.metric("Signal", result.signal_level)

            # Z-score by window chart
            if result.window_stats:
                windows = [ws.window_size for ws in result.window_stats if ws.n_draws > 0]
                z_scores = [ws.z_score for ws in result.window_stats if ws.n_draws > 0]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[str(w) for w in windows],
                    y=z_scores,
                    marker_color=["red" if z < 0 else "green" for z in z_scores],
                    text=[f"{z:.2f}" for z in z_scores],
                    textposition="outside",
                ))
                fig.add_hline(y=2, line_dash="dash", line_color="orange", annotation_text="Z=2")
                fig.add_hline(y=-2, line_dash="dash", line_color="orange")
                fig.add_hline(y=3, line_dash="dash", line_color="red", annotation_text="Z=3")
                fig.add_hline(y=-3, line_dash="dash", line_color="red")
                fig.update_layout(
                    title=f"Z-Score by Window — {selected}",
                    xaxis_title="Window Size",
                    yaxis_title="Z-Score",
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Monte Carlo Simulation")

        n_sims = st.slider("Simulations", 1000, 100000, 10000, step=1000)

        if st.button("Run Monte Carlo", type="primary"):
            with st.spinner(f"Running {n_sims:,} simulations..."):
                # Get current allocation
                extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
                value_results = value_engine.analyze_all(game, extremum_results)
                allocation = portfolio.optimize(game, value_results)

                # Build win sets for roulette
                red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
                win_sets = {}
                for b in game.bets:
                    if b.id.startswith("num_"):
                        num = int(b.id.split("_")[1])
                        win_sets[b.id] = {str(num)}
                    elif b.id == "red":
                        win_sets[b.id] = {str(n) for n in red_numbers}
                    elif b.id == "black":
                        win_sets[b.id] = {str(n) for n in range(1, 37) if n not in red_numbers}
                    elif b.id == "even":
                        win_sets[b.id] = {str(n) for n in range(2, 37, 2)}
                    elif b.id == "odd":
                        win_sets[b.id] = {str(n) for n in range(1, 37, 2)}
                    elif b.id == "low":
                        win_sets[b.id] = {str(n) for n in range(1, 19)}
                    elif b.id == "high":
                        win_sets[b.id] = {str(n) for n in range(19, 37)}
                    elif b.id.startswith("dozen_"):
                        d = int(b.id.split("_")[1])
                        start = (d - 1) * 12 + 1
                        win_sets[b.id] = {str(n) for n in range(start, start + 12)}
                    elif b.id.startswith("col_"):
                        c = int(b.id.split("_")[1])
                        win_sets[b.id] = {str(n) for n in range(1, 37) if (n - 1) % 3 == c - 1}

                outcome_probs = {str(i): 1 / 37 for i in range(37)}

                result = mc.simulate_game_outcomes(
                    game, allocation, outcome_probs, win_sets, n_simulations=n_sims
                )

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Expected Return", f"{result.expected_return:+.2f} zł")
            col2.metric("Std Dev", f"{result.std_return:.2f} zł")
            col3.metric("Max Drawdown", f"{result.max_drawdown:.2f} zł")
            col4.metric("Ruin Probability", f"{result.ruin_probability:.2%}")

            col5, col6 = st.columns(2)
            col5.metric("VaR 95%", f"{result.var_95:.2f} zł")
            col6.metric("CVaR 95%", f"{result.cvar_95:.2f} zł")

            # Profit distribution histogram
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=result.profit_distribution,
                nbinsx=100,
                marker_color="steelblue",
                opacity=0.7,
            ))
            fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
            fig.add_vline(x=result.expected_return, line_dash="dash", line_color="green",
                         annotation_text=f"Mean: {result.expected_return:+.1f}")
            fig.update_layout(
                title=f"Profit Distribution ({n_sims:,} simulations)",
                xaxis_title="Profit (zł)",
                yaxis_title="Frequency",
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)
