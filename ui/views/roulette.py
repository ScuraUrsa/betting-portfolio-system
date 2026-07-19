"""Roulette recommendations page with interactive wheel visualization."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from games.roulette import european_roulette
from games.roulette_wheel import (
    WHEEL_ORDER, RED_NUMBERS, BLACK_NUMBERS,
    JEU_0, VOISINS_DU_ZERO, TIERS_DU_CYLINDRE, ORPHELINS,
    get_color, get_parity, get_half, get_dozen, get_column, get_section,
    get_neighbors, get_opposite, build_wheel_figure,
)
from core.history import HistoryEngine
from core.extremum import ExtremumEngine
from core.value import ValueEngine
from core.portfolio import PortfolioEngine
from core.monte_carlo import MonteCarloEngine


def _build_bet_rows(game, extremum, ve, bankroll):
    """Build recommendation rows for a set of bets."""
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
            "Rec. Stake zł": f"{vr.recommended_stake_pct * bankroll:.2f}",
        })

    order = {"maximum": 0, "medium": 1, "entry_small": 2, "observation": 3, "none": 4}
    rows.sort(key=lambda r: order.get(r["Signal"], 5))
    return rows


def _render_recommendations_table(rows):
    """Render the recommendations dataframe with active signal count."""
    st.dataframe(rows, width='stretch', hide_index=True)
    active = [r for r in rows if r["Signal"] != "none"]
    if active:
        st.success(f"🔔 {len(active)} bets with active signals")
    else:
        st.info("No significant signals detected")


def _render_signals_tab(game, extremum):
    """Render the Z-score / Extremum Index signals tab."""
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


def _render_monte_carlo_tab(game, extremum, ve, portfolio, mc):
    """Render the Monte Carlo simulation tab."""
    st.subheader("Monte Carlo Simulation")
    n = st.slider("Simulations", 1000, 100000, 10000, step=1000)
    if st.button("Run Monte Carlo", type="primary"):
        with st.spinner(f"Running {n:,} simulations..."):
            ext_map = {r.bet_id: r for r in extremum.analyze_all(game)}
            vals = ve.analyze_all(game, ext_map)
            alloc = portfolio.optimize(game, vals)

            red = RED_NUMBERS
            ws = {}
            for b in game.bets:
                if b.id.startswith("num_"):
                    ws[b.id] = {str(int(b.id.split("_")[1]))}
                elif b.id == "red":
                    ws[b.id] = {str(x) for x in red}
                elif b.id == "black":
                    ws[b.id] = {str(x) for x in range(1, 37) if x not in red}
                elif b.id == "even":
                    ws[b.id] = {str(x) for x in range(2, 37, 2)}
                elif b.id == "odd":
                    ws[b.id] = {str(x) for x in range(1, 37, 2)}
                elif b.id == "low":
                    ws[b.id] = {str(x) for x in range(1, 19)}
                elif b.id == "high":
                    ws[b.id] = {str(x) for x in range(19, 37)}
                elif b.id.startswith("dozen_"):
                    d = int(b.id.split("_")[1])
                    s = (d - 1) * 12 + 1
                    ws[b.id] = {str(x) for x in range(s, s + 12)}
                elif b.id.startswith("col_"):
                    c = int(b.id.split("_")[1])
                    ws[b.id] = {str(x) for x in range(1, 37) if (x - 1) % 3 == c - 1}

            res = mc.simulate_game_outcomes(
                game, alloc, {str(i): 1 / 37 for i in range(37)}, ws, n_simulations=n
            )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Expected Return", f"{res.expected_return:+.2f} zł")
        c2.metric("Std Dev", f"{res.std_return:.2f} zł")
        c3.metric("Max Drawdown", f"{res.max_drawdown:.2f} zł")
        c4.metric("Ruin Prob", f"{res.ruin_probability:.2%}")
        c5, c6 = st.columns(2)
        c5.metric("VaR 95%", f"{res.var_95:.2f} zł")
        c6.metric("CVaR 95%", f"{res.cvar_95:.2f} zł")

        fig = go.Figure(go.Histogram(
            x=res.profit_distribution, nbinsx=100,
            marker_color="steelblue", opacity=0.7,
        ))
        fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
        fig.add_vline(
            x=res.expected_return, line_dash="dash", line_color="green",
            annotation_text=f"Mean: {res.expected_return:+.1f}",
        )
        fig.update_layout(title=f"Profit Distribution ({n:,} simulations)", height=400)
        st.plotly_chart(fig, width='stretch')


def _render_wheel_tab():
    """Render the interactive wheel visualization tab."""
    st.subheader("🎡 European Roulette Wheel")
    st.caption("Hover over any number to see all properties, neighbors, and opposite numbers")

    fig = build_wheel_figure(height=550)
    st.plotly_chart(fig, width='stretch')

    # ── Number detail lookup ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔍 Number Lookup")
    lookup = st.number_input("Enter a number (0-36)", min_value=0, max_value=36, value=17, step=1)

    if lookup is not None:
        n = int(lookup)
        c = get_color(n)
        neighbors = get_neighbors(n, 2)
        opp = get_opposite(n)

        cols = st.columns(4)
        cols[0].metric("Color", c.title())
        cols[1].metric("Parity", get_parity(n).title())
        cols[2].metric("Half", get_half(n))
        cols[3].metric("Dozen", get_dozen(n))

        cols2 = st.columns(3)
        cols2[0].metric("Column", get_column(n))
        cols2[1].metric("Section", get_section(n))
        cols2[2].metric("Wheel Position", f"#{WHEEL_ORDER.index(n) + 1}/37")

        st.markdown("**← Neighbors (2 each side) →**")
        st.markdown(
            f"`{neighbors[0]}` `{neighbors[1]}` "
            f"**← `{n}` →** "
            f"`{neighbors[2]}` `{neighbors[3]}`"
        )

        st.markdown(f"**Opposite (positions +18/+19):** `{opp[0]}`, `{opp[1]}`")


def _render_french_bets_tab():
    """Render the French announced bets tab."""
    st.subheader("🇫🇷 French Announced Bets (Les Annonces)")
    st.caption("Traditional French roulette call bets covering specific wheel sectors")

    sections = {
        "🎯 Jeu 0 (Zero Game)": JEU_0,
        "🟢 Voisins du Zéro (Neighbors of Zero)": VOISINS_DU_ZERO,
        "🔵 Tiers du Cylindre (Thirds of the Wheel)": TIERS_DU_CYLINDRE,
        "🟠 Orphelins (Orphans)": ORPHELINS,
    }

    for name, numbers in sections.items():
        with st.expander(f"{name} — {len(numbers)} numbers", expanded=False):
            sorted_nums = sorted(numbers)
            # Show as colored chips
            chips_html = ""
            for n in sorted_nums:
                c = get_color(n)
                bg = "#1a6b1a" if c == "green" else "#c41e3a" if c == "red" else "#1a1a2e"
                chips_html += (
                    f'<span style="display:inline-block;width:42px;height:42px;'
                    f'line-height:42px;text-align:center;border-radius:50%;'
                    f'background:{bg};color:white;font-weight:bold;margin:3px;'
                    f'font-size:13px;border:2px solid #555;">{n}</span>'
                )
            st.markdown(f'<div style="line-height:2.5">{chips_html}</div>', unsafe_allow_html=True)

            # Show wheel position context
            st.caption(
                f"These numbers are adjacent on the wheel. "
                f"Bet covers {len(numbers)}/{37} = {len(numbers)/37*100:.1f}% of the wheel."
            )


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

    # ── Main tabs ─────────────────────────────────────────────────────
    tab_wheel, tab_numbers, tab_bets, tab_french, tab_signals, tab_mc = st.tabs([
        "🎡 Wheel", "🔢 Numbers", "🎯 Other Bets", "🇫🇷 French Bets",
        "📈 Signals", "🎲 Monte Carlo",
    ])

    with tab_wheel:
        _render_wheel_tab()

    with tab_numbers:
        st.subheader("🔢 Straight-Up Numbers (0-36)")
        st.caption("Bet on individual numbers — each pays 36:1")

        # Filter game to only straight-up bets
        num_game = type(game)("Roulette Numbers", [b for b in game.bets if b.id.startswith("num_")])
        rows = _build_bet_rows(num_game, extremum, ve, st.session_state.bankroll)
        _render_recommendations_table(rows)

    with tab_bets:
        st.subheader("🎯 Outside & Group Bets")
        st.caption("Red/Black, Even/Odd, Low/High, Dozens, Columns")

        other_bets = [b for b in game.bets if not b.id.startswith("num_")]
        other_game = type(game)("Roulette Other Bets", other_bets)
        rows = _build_bet_rows(other_game, extremum, ve, st.session_state.bankroll)
        _render_recommendations_table(rows)

    with tab_french:
        _render_french_bets_tab()

    with tab_signals:
        _render_signals_tab(game, extremum)

    with tab_mc:
        _render_monte_carlo_tab(game, extremum, ve, portfolio, mc)
