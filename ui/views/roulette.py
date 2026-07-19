"""Roulette recommendations page."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from games.roulette import european_roulette
from core.history import HistoryEngine
from core.extremum import ExtremumEngine
from core.value import ValueEngine
from core.portfolio import PortfolioEngine
from core.monte_carlo import MonteCarloEngine


def show():
    if "bankroll" not in st.session_state:
        st.session_state.bankroll = 1000.0

    st.title("🎰 Roulette — European (37 fields)")

    game = european_roulette()
    history = HistoryEngine("data/roulette_history.db")
    extremum = ExtremumEngine(history)
    ve = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)
    mc = MonteCarloEngine(seed=42)

    tab1, tab2, tab3 = st.tabs(["📋 Recommendations", "📈 Signals", "🎯 Monte Carlo"])

    with tab1:
        st.subheader("Bet Recommendations")
        ext_map = {r.bet_id: r for r in extremum.analyze_all(game)}
        vals = ve.analyze_all(game, ext_map)

        rows = []
        for vr in vals:
            ext = ext_map.get(vr.bet_id)
            rows.append({
                "Bet": vr.bet_name, "ID": vr.bet_id,
                "Probability": f"{vr.probability*100:.2f}%",
                "Odds": f"{vr.odds:.1f}", "EV": f"{vr.ev:+.4f}",
                "Kelly 1/4": f"{vr.kelly_quarter:.4f}",
                "Signal": ext.signal_level if ext else "none",
                "Direction": ext.direction if ext else "neutral",
                "Rec. Stake %": f"{vr.recommended_stake_pct:.2%}",
                "Rec. Stake zł": f"{vr.recommended_stake_pct * st.session_state.bankroll:.2f}",
            })

        order = {"maximum": 0, "medium": 1, "entry_small": 2, "observation": 3, "none": 4}
        rows.sort(key=lambda r: order.get(r["Signal"], 5))
        st.dataframe(rows, width='stretch', hide_index=True)

        active = [r for r in rows if r["Signal"] != "none"]
        st.success(f"🔔 {len(active)} bets with active signals") if active else st.info("No significant signals detected")

    with tab2:
        st.subheader("Extremum Index by Bet")
        sel = st.selectbox("Select bet", [b.id for b in game.bets], index=0)
        if sel:
            r = extremum.analyze(game, sel)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("EI", f"{r.extremum_index:.3f}")
            c2.metric("Max Z", f"{r.max_z_score:.3f}")
            c3.metric("Direction", r.direction)
            c4.metric("Signal", r.signal_level)

            if r.window_stats:
                ws_list = [ws for ws in r.window_stats if ws.n_draws > 0]
                fig = go.Figure(go.Bar(
                    x=[str(ws.window_size) for ws in ws_list],
                    y=[ws.z_score for ws in ws_list],
                    marker_color=["red" if ws.z_score < 0 else "green" for ws in ws_list],
                    text=[f"{ws.z_score:.2f}" for ws in ws_list],
                    textposition="outside",
                ))
                for y in (2, -2, 3, -3):
                    fig.add_hline(y=y, line_dash="dash", line_color="orange" if abs(y) == 2 else "red")
                fig.update_layout(title=f"Z-Score by Window — {sel}", height=400)
                st.plotly_chart(fig, width='stretch')

    with tab3:
        st.subheader("Monte Carlo Simulation")
        n = st.slider("Simulations", 1000, 100000, 10000, step=1000)
        if st.button("Run Monte Carlo", type="primary"):
            with st.spinner(f"Running {n:,} simulations..."):
                ext_map = {r.bet_id: r for r in extremum.analyze_all(game)}
                vals = ve.analyze_all(game, ext_map)
                alloc = portfolio.optimize(game, vals)

                red = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
                ws = {}
                for b in game.bets:
                    if b.id.startswith("num_"):
                        ws[b.id] = {str(int(b.id.split("_")[1]))}
                    elif b.id == "red": ws[b.id] = {str(x) for x in red}
                    elif b.id == "black": ws[b.id] = {str(x) for x in range(1,37) if x not in red}
                    elif b.id == "even": ws[b.id] = {str(x) for x in range(2,37,2)}
                    elif b.id == "odd": ws[b.id] = {str(x) for x in range(1,37,2)}
                    elif b.id == "low": ws[b.id] = {str(x) for x in range(1,19)}
                    elif b.id == "high": ws[b.id] = {str(x) for x in range(19,37)}
                    elif b.id.startswith("dozen_"):
                        d = int(b.id.split("_")[1]); s = (d-1)*12+1
                        ws[b.id] = {str(x) for x in range(s, s+12)}
                    elif b.id.startswith("col_"):
                        c = int(b.id.split("_")[1])
                        ws[b.id] = {str(x) for x in range(1,37) if (x-1)%3 == c-1}

                res = mc.simulate_game_outcomes(game, alloc, {str(i):1/37 for i in range(37)}, ws, n_simulations=n)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Expected Return", f"{res.expected_return:+.2f} zł")
            c2.metric("Std Dev", f"{res.std_return:.2f} zł")
            c3.metric("Max Drawdown", f"{res.max_drawdown:.2f} zł")
            c4.metric("Ruin Prob", f"{res.ruin_probability:.2%}")
            c5, c6 = st.columns(2)
            c5.metric("VaR 95%", f"{res.var_95:.2f} zł")
            c6.metric("CVaR 95%", f"{res.cvar_95:.2f} zł")

            fig = go.Figure(go.Histogram(x=res.profit_distribution, nbinsx=100, marker_color="steelblue", opacity=0.7))
            fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
            fig.add_vline(x=res.expected_return, line_dash="dash", line_color="green", annotation_text=f"Mean: {res.expected_return:+.1f}")
            fig.update_layout(title=f"Profit Distribution ({n:,} simulations)", height=400)
            st.plotly_chart(fig, width='stretch')
