"""Portfolio overview page — cross-game view."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from games.roulette import european_roulette
from games.poker import texas_holdem_hand_rankings
from core.history import HistoryEngine
from core.extremum import ExtremumEngine
from core.value import ValueEngine
from core.portfolio import PortfolioEngine
from core.monte_carlo import MonteCarloEngine
from core.risk import RiskManager, RiskLimits


def show():
    st.title("📊 Portfolio Overview")

    bankroll = st.session_state.bankroll

    col1, col2, col3 = st.columns(3)
    col1.metric("Bankroll", f"{bankroll:,.0f} zł")
    col2.metric("Max Exposure (50%)", f"{bankroll * 0.5:,.0f} zł")
    col3.metric("Max Per Bet (10%)", f"{bankroll * 0.1:,.0f} zł")

    st.markdown("---")

    # Load both games
    roulette = european_roulette()
    poker = texas_holdem_hand_rankings()

    rh = HistoryEngine("data/roulette_history.db")
    ph = HistoryEngine("data/poker_history.db")

    re = ExtremumEngine(rh)
    pe = ExtremumEngine(ph)

    ve = ValueEngine()
    portfolio = PortfolioEngine(bankroll=bankroll)
    mc = MonteCarloEngine(seed=42)
    risk_mgr = RiskManager()

    # Analyze both
    r_ext = {r.bet_id: r for r in re.analyze_all(roulette)}
    p_ext = {r.bet_id: r for r in pe.analyze_all(poker)}

    r_val = ve.analyze_all(roulette, r_ext)
    p_val = ve.analyze_all(poker, p_ext)

    # Find top signals
    st.subheader("🔔 Active Signals")

    all_signals = []
    for vr in r_val:
        ext = r_ext.get(vr.bet_id)
        if ext and ext.signal_level != "none":
            all_signals.append({
                "Game": "Roulette",
                "Bet": vr.bet_name,
                "Signal": ext.signal_level,
                "Direction": ext.direction,
                "EI": f"{ext.extremum_index:+.3f}",
                "Rec. Stake": f"{vr.recommended_stake_pct:.2%}",
            })
    for vr in p_val:
        ext = p_ext.get(vr.bet_id)
        if ext and ext.signal_level != "none":
            all_signals.append({
                "Game": "Poker",
                "Bet": vr.bet_name,
                "Signal": ext.signal_level,
                "Direction": ext.direction,
                "EI": f"{ext.extremum_index:+.3f}",
                "Rec. Stake": f"{vr.recommended_stake_pct:.2%}",
            })

    if all_signals:
        st.dataframe(all_signals, use_container_width=True, hide_index=True)
    else:
        st.info("No active signals. Add some history data to detect patterns.")

    st.markdown("---")

    # Combined portfolio optimization
    st.subheader("📈 Combined Portfolio Optimization")

    if st.button("Optimize Combined Portfolio", type="primary"):
        # Combine all bets from both games
        from core.game import Game
        combined = Game(
            name="Combined Portfolio",
            bets=roulette.bets + poker.bets,
        )
        combined_val = r_val + p_val

        allocation = portfolio.optimize(combined, combined_val)

        # Show allocation
        st.write("### Recommended Allocation")
        alloc_rows = []
        for i, bid in enumerate(allocation.bet_ids):
            if allocation.stake_pcts[i] > 0.001:
                game_name = "Roulette" if bid in [b.id for b in roulette.bets] else "Poker"
                alloc_rows.append({
                    "Game": game_name,
                    "Bet": bid,
                    "Stake %": f"{allocation.stake_pcts[i]:.2%}",
                    "Stake zł": f"{allocation.stakes[i]:.2f}",
                })

        if alloc_rows:
            st.dataframe(alloc_rows, use_container_width=True, hide_index=True)
            st.metric("Total Exposure", f"{allocation.total_exposure:.2%}")
            st.metric("Expected Return", f"{allocation.expected_return:+.2f} zł")
        else:
            st.info("No positive-EV bets found. Optimal allocation is 0.")

        # Risk assessment
        risk_report = risk_mgr.assess(allocation, bankroll)
        if not risk_report.is_acceptable:
            st.warning("⚠️ Risk limits exceeded:")
            for v in risk_report.limits_exceeded:
                st.write(f"- {v}")
        else:
            st.success("✅ Risk limits OK")

    st.markdown("---")

    # Loss distribution summary
    st.subheader("📉 Loss Distribution (Roulette)")

    # Build win sets for roulette
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    win_sets = {}
    for b in roulette.bets:
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

    r_alloc = portfolio.optimize(roulette, r_val)
    outcome_probs = {str(i): 1 / 37 for i in range(37)}
    all_outcomes = [str(i) for i in range(37)]

    scenarios = portfolio.analyze_scenarios(roulette, r_alloc, win_sets, all_outcomes, outcome_probs)
    loss_dist = risk_mgr.compute_loss_distribution(scenarios)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Best Case", f"{loss_dist.best_case:+.0f} zł")
    col2.metric("Worst Case", f"{loss_dist.worst_case:+.0f} zł")
    col3.metric("Expected", f"{loss_dist.expected_case:+.0f} zł")
    col4.metric("P(Profit)", f"{loss_dist.profit_probability:.1%}")

    # Scenario chart
    profits = [s.profit for s in scenarios]
    probs = [s.probability for s in scenarios]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"Scenario {s.scenario_id}" for s in scenarios],
        y=profits,
        marker_color=["green" if p > 0 else "red" for p in profits],
    ))
    fig.update_layout(
        title="Profit by Scenario (Roulette)",
        xaxis_title="Scenario",
        yaxis_title="Profit (zł)",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)
