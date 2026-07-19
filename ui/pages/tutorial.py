"""Interactive Tutorial — step-by-step walkthrough of all features.

Guides the user through every action the system supports:
- Understanding the game model
- Recording draws
- Reading Z-scores and Extremum Index
- Value analysis and Kelly criterion
- Correlation analysis
- Portfolio optimization
- Monte Carlo simulation
- Risk management
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from core.game import Bet, Game
from core.history import HistoryEngine
from core.extremum import ExtremumEngine
from core.value import ValueEngine
from core.correlation import CorrelationEngine
from core.portfolio import PortfolioEngine
from core.monte_carlo import MonteCarloEngine
from core.risk import RiskManager, RiskLimits
from games.roulette import european_roulette
from games.poker import texas_holdem_hand_rankings


# Tutorial steps
STEPS = [
    "1. Welcome & Concepts",
    "2. Game Model (Roulette)",
    "3. Game Model (Poker)",
    "4. Recording Draws",
    "5. Rolling Windows & Z-Score",
    "6. Extremum Index (EI)",
    "7. Mean Reversion Factor (MRF)",
    "8. Value Engine (EV & Kelly)",
    "9. Correlation Engine",
    "10. Portfolio Optimization",
    "11. Monte Carlo Simulation",
    "12. Risk Management",
    "13. Loss Distribution",
    "14. Combined Portfolio",
    "15. Summary & Next Steps",
]


def show():
    st.title("🎓 Interactive Tutorial")
    st.caption("Step-by-step walkthrough of every feature in the Betting Portfolio System")

    # Progress
    if "tutorial_step" not in st.session_state:
        st.session_state.tutorial_step = 0

    step = st.session_state.tutorial_step

    # Sidebar navigation
    with st.sidebar:
        st.subheader("Tutorial Steps")
        for i, name in enumerate(STEPS):
            if i == step:
                st.markdown(f"**→ {name}**")
            elif i < step:
                st.markdown(f"✓ ~~{name}~~")
            else:
                st.caption(name)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous", disabled=(step == 0)):
                st.session_state.tutorial_step = max(0, step - 1)
                st.rerun()
        with col2:
            if st.button("Next →", disabled=(step == len(STEPS) - 1)):
                st.session_state.tutorial_step = min(len(STEPS) - 1, step + 1)
                st.rerun()

        st.progress((step + 1) / len(STEPS))

    st.markdown("---")

    # Render current step
    if step == 0:
        _step_welcome()
    elif step == 1:
        _step_roulette_model()
    elif step == 2:
        _step_poker_model()
    elif step == 3:
        _step_recording_draws()
    elif step == 4:
        _step_zscore()
    elif step == 5:
        _step_ei()
    elif step == 6:
        _step_mrf()
    elif step == 7:
        _step_value()
    elif step == 8:
        _step_correlation()
    elif step == 9:
        _step_portfolio()
    elif step == 10:
        _step_monte_carlo()
    elif step == 11:
        _step_risk()
    elif step == 12:
        _step_loss_distribution()
    elif step == 13:
        _step_combined()
    elif step == 14:
        _step_summary()


# ── Step implementations ──────────────────────────────────────────────

def _step_welcome():
    st.header("Welcome to the Betting Portfolio System")
    st.markdown("""
    ### What is this system?

    This is a **game-agnostic betting portfolio optimization engine**. It doesn't try to predict
    which bet will win. Instead, it answers a much harder question:

    > *"How should I distribute my capital across all available bets, considering local extremes,
    > mean reversion, correlations between bets, and the expected profit/risk profile of the
    > entire portfolio?"*

    ### Key concepts you'll learn:

    | Concept | What it does |
    |---------|-------------|
    | **Z-Score** | Measures how far actual results deviate from expected |
    | **Extremum Index** | Aggregates Z-scores across multiple time windows |
    | **MRF** | Learned parameter: how often extremes regress to the mean |
    | **Kelly Criterion** | Optimal bet sizing for maximum long-term growth |
    | **Correlation** | How bets depend on each other |
    | **Portfolio Optimization** | Best allocation across ALL bets simultaneously |
    | **Monte Carlo** | Simulates thousands of outcomes to estimate risk |
    | **Risk Management** | Enforces exposure limits and drawdown controls |

    ### Supported games:
    - 🎰 European Roulette (37 fields)
    - 🃏 Texas Hold'em Poker (hand rankings)
    - 🎲 Dice (extensible)
    - 🎟️ Lottery (extensible)

    **Click "Next →" to start exploring!**
    """)


def _step_roulette_model():
    st.header("Step 2: Game Model — Roulette")
    st.markdown("""
    Every game in the system is defined by a list of **bets**. Each bet has:
    - **ID**: unique identifier (e.g. `num_17`, `red`)
    - **Probability**: theoretical P(win)
    - **Odds**: payout multiplier

    **Key insight**: Bets are NOT mutually exclusive! In roulette, you can bet on
    "red" AND "num_17" — they overlap. The system handles this correctly.
    """)

    game = european_roulette()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Bets", game.n_bets)
    col2.metric("Straight-up Numbers", 37)
    col3.metric("House Edge", "-2.70%")

    st.subheader("Try it: inspect a bet")
    bet_id = st.selectbox("Select a bet to inspect:", [b.id for b in game.bets], key="tut_roul_bet")
    bet = game.get_bet(bet_id)
    ev = game.expected_value(bet_id)

    col1, col2, col3 = st.columns(3)
    col1.metric("Probability", f"{bet.probability*100:.2f}%")
    col2.metric("Odds", f"{bet.odds:.1f}:1")
    col3.metric("EV", f"{ev:+.4f}")

    st.info(f"💡 **Did you know?** Every roulette bet has EV = -1/37 ≈ -2.70%. "
            f"The house always has an edge. The system helps you find when deviations "
            f"from expected create temporary opportunities.")


def _step_poker_model():
    st.header("Step 3: Game Model — Poker")
    st.markdown("""
    Poker hand rankings are modeled as separate bets. Each bet represents
    "player achieves at least this hand rank."

    Probabilities are based on 7-card combinations (2 hole + 5 community).
    """)

    game = texas_holdem_hand_rankings()

    st.subheader("Hand Probability Distribution")
    probs = [b.probability for b in game.bets]
    names = [b.name for b in game.bets]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names, y=probs,
        marker_color="steelblue",
        text=[f"{p*100:.4f}%" for p in probs],
        textposition="outside",
    ))
    fig.update_layout(height=350, yaxis_title="Probability")
    st.plotly_chart(fig, use_container_width=True)

    st.info("💡 Unlike roulette, poker bets have different EVs because odds "
            "can be set independently. The system finds which hands are undervalued.")


def _step_recording_draws():
    st.header("Step 4: Recording Draws")
    st.markdown("""
    The system stores every draw outcome in a **SQLite database**. Each draw records:
    - The raw outcome (e.g. roulette number "17")
    - Which bets won on that outcome
    - Timestamp

    This history is the foundation for all statistical analysis.
    """)

    game = european_roulette()
    history = HistoryEngine("data/tutorial_history.db")

    st.subheader("Try it: record a roulette draw")
    number = st.number_input("Number drawn (0-36):", 0, 36, 17, key="tut_draw_num")

    # Compute winning bets
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    won = [f"num_{number}"]
    if number != 0:
        won.append("red" if number in red_numbers else "black")
        won.append("even" if number % 2 == 0 else "odd")
        won.append("low" if number <= 18 else "high")
        won.append(f"dozen_{(number - 1) // 12 + 1}")
        won.append(f"col_{(number - 1) % 3 + 1}")

    st.write(f"Winning bets: **{', '.join(won)}**")

    if st.button("Record This Draw", type="primary", key="tut_record"):
        draw_id = history.record_draw(game, str(number), won)
        st.success(f"✅ Draw #{draw_id} recorded!")

    st.metric("Total draws in tutorial DB", history.count_draws(game.name))

    st.subheader("Generate test data")
    n = st.slider("How many random draws?", 10, 500, 100, key="tut_gen")
    if st.button("Generate Random Draws", key="tut_gen_btn"):
        rng = np.random.default_rng(42)
        for _ in range(n):
            num = int(rng.integers(0, 37))
            w = [f"num_{num}"]
            if num != 0:
                w.append("red" if num in red_numbers else "black")
                w.append("even" if num % 2 == 0 else "odd")
                w.append("low" if num <= 18 else "high")
                w.append(f"dozen_{(num - 1) // 12 + 1}")
                w.append(f"col_{(num - 1) % 3 + 1}")
            history.record_draw(game, str(num), w)
        st.success(f"✅ Generated {n} random draws!")
        st.rerun()


def _step_zscore():
    st.header("Step 5: Rolling Windows & Z-Score")
    st.markdown(r"""
    ### How Z-Score works

    For each bet, over each time window:

    $$E = n \times p \quad \text{(expected hits)}$$
    $$\sigma = \sqrt{n \times p \times (1-p)} \quad \text{(standard deviation)}$$
    $$Z = \frac{X - E}{\sigma} \quad \text{(Z-score)}$$

    Where:
    - $n$ = number of draws in the window
    - $p$ = theoretical probability
    - $X$ = actual number of hits

    ### Signal thresholds:
    | Z-Score | Meaning |
    |---------|---------|
    | \|Z\| < 1 | Normal deviation |
    | \|Z\| > 2 | Observation |
    | \|Z\| > 2.5 | Strong deviation |
    | \|Z\| > 3 | Extremum |
    | \|Z\| > 4 | Very strong extremum |
    """)

    game = european_roulette()
    history = HistoryEngine("data/tutorial_history.db")

    if history.count_draws(game.name) < 10:
        st.warning("⚠️ Need at least 10 draws. Go back to Step 4 and generate some data!")
        return

    st.subheader("Live Z-Score Chart")
    bet_id = st.selectbox("Select bet:", ["red", "black", "even", "odd", "num_0", "num_17"], key="tut_zscore")

    stats = history.compute_all_windows(game, bet_id)
    windows = [ws.window_size for ws in stats if ws.n_draws > 0]
    z_scores = [ws.z_score for ws in stats if ws.n_draws > 0]

    if z_scores:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[str(w) for w in windows],
            y=z_scores,
            marker_color=["red" if z < 0 else "green" for z in z_scores],
            text=[f"{z:.2f}" for z in z_scores],
            textposition="outside",
        ))
        fig.add_hline(y=2, line_dash="dash", line_color="orange")
        fig.add_hline(y=-2, line_dash="dash", line_color="orange")
        fig.add_hline(y=3, line_dash="dash", line_color="red")
        fig.add_hline(y=-3, line_dash="dash", line_color="red")
        fig.update_layout(height=350, title=f"Z-Score by Window — {bet_id}")
        st.plotly_chart(fig, use_container_width=True)

        # Show raw data
        st.subheader("Raw Statistics")
        rows = []
        for ws in stats:
            if ws.n_draws > 0:
                rows.append({
                    "Window": ws.window_size,
                    "Draws": ws.n_draws,
                    "Hits": ws.hits,
                    "Expected": f"{ws.expected:.1f}",
                    "Std": f"{ws.std:.2f}",
                    "Z-Score": f"{ws.z_score:+.3f}",
                })
        st.dataframe(rows, use_container_width=True, hide_index=True)


def _step_ei():
    st.header("Step 6: Extremum Index (EI)")
    st.markdown(r"""
    ### What is the Extremum Index?

    The EI aggregates Z-scores from multiple time windows into a single signal:

    $$EI = 0.1 \times Z_{50} + 0.2 \times Z_{100} + 0.3 \times Z_{250} + 0.4 \times Z_{500}$$

    Longer windows get higher weight because they're more statistically significant.

    ### EI Signal Levels:
    | EI | Action |
    |----|--------|
    | < 1.0 | No signal |
    | < 2.0 | Observation only |
    | < 2.5 | Entry with small stake |
    | < 3.0 | Medium exposure |
    | ≥ 3.0 | Maximum exposure |
    """)

    game = european_roulette()
    history = HistoryEngine("data/tutorial_history.db")

    if history.count_draws(game.name) < 10:
        st.warning("⚠️ Need at least 10 draws. Go back to Step 4!")
        return

    extremum = ExtremumEngine(history)
    results = extremum.analyze_all(game)
    results.sort(key=lambda r: abs(r.extremum_index), reverse=True)

    st.subheader("Top Signals")
    rows = []
    for r in results[:10]:
        rows.append({
            "Bet": r.bet_id,
            "EI": f"{r.extremum_index:+.3f}",
            "Max Z": f"{r.max_z_score:+.2f}",
            "Direction": r.direction,
            "Signal": r.signal_level,
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    active = [r for r in results if r.signal_level != "none"]
    if active:
        st.success(f"🔔 {len(active)} bets with active signals detected!")
    else:
        st.info("No significant signals. Generate more data or try different patterns.")


def _step_mrf():
    st.header("Step 7: Mean Reversion Factor (MRF)")
    st.markdown("""
    ### What is MRF?

    The system does NOT assume mean reversion exists. Instead, it **learns** MRF from data.

    $$MRF = P(\\text{correction} \\mid \\text{extremum})$$

    - **MRF = 0**: Pure randomness — extremes don't predict anything
    - **MRF = 1**: Full mean reversion — extremes always correct
    - **Default = 0.35**: Moderate mean reversion (empirical starting point)

    ### How it's learned:
    For each extremum (|Z| > 2), the system checks whether the next period
    shows regression toward the mean. MRF is the fraction of extremes
    that were followed by correction.
    """)

    game = european_roulette()
    history = HistoryEngine("data/tutorial_history.db")

    if history.count_draws(game.name) < 100:
        st.warning("⚠️ Need at least 100 draws to learn MRF. Generate more data in Step 4!")
        st.metric("Default MRF", "0.35")
        return

    extremum = ExtremumEngine(history)
    bet_id = st.selectbox("Learn MRF for:", ["red", "black", "even", "odd"], key="tut_mrf")

    if st.button("Learn MRF from Data", type="primary", key="tut_mrf_btn"):
        mrf = extremum.learn_mrf(game, bet_id, lookback=min(1000, history.count_draws(game.name)))
        st.metric("Learned MRF", f"{mrf:.3f}")
        if mrf > 0.5:
            st.success("Strong mean reversion detected — extremes tend to correct.")
        elif mrf > 0.3:
            st.info("Moderate mean reversion — some correction after extremes.")
        else:
            st.warning("Weak mean reversion — extremes are mostly random noise.")


def _step_value():
    st.header("Step 8: Value Engine (EV & Kelly)")
    st.markdown(r"""
    ### Expected Value
    $$EV = p \times odds - 1$$

    - EV > 0: positive expected value (good bet)
    - EV < 0: negative expected value (house edge)

    ### Kelly Criterion
    $$f = \frac{p \times odds - 1}{odds - 1}$$

    The Kelly fraction $f$ is the optimal fraction of bankroll to bet for
    maximum long-term growth. In practice, we use **fractional Kelly**:
    - 1/4 Kelly: conservative
    - 1/2 Kelly: moderate
    - Full Kelly: aggressive (high risk of drawdown)
    """)

    game = european_roulette()
    history = HistoryEngine("data/tutorial_history.db")
    extremum = ExtremumEngine(history)
    ve = ValueEngine()

    st.subheader("Value Analysis with Signal Adjustment")

    extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
    value_results = ve.analyze_all(game, extremum_results)

    rows = []
    for vr in value_results[:15]:
        ext = extremum_results.get(vr.bet_id)
        rows.append({
            "Bet": vr.bet_name,
            "EV": f"{vr.ev:+.4f}",
            "Kelly Full": f"{vr.kelly_full:.4f}",
            "Kelly 1/4": f"{vr.kelly_quarter:.4f}",
            "Risk Score": f"{vr.risk_score:.3f}",
            "Exposure": f"{vr.exposure_score:.3f}",
            "Signal": ext.signal_level if ext else "none",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.info("💡 Notice: when a bet has a strong 'under' signal (below expected), "
            "the exposure score increases — the system bets on regression to the mean.")


def _step_correlation():
    st.header("Step 9: Correlation Engine")
    st.markdown("""
    ### Why correlation matters

    In roulette, bets overlap. If you bet on "red" AND "num_17", both win when 17 comes up.
    The correlation engine captures these structural dependencies.

    Two methods:
    1. **Structural**: based on overlapping win conditions (fast, exact)
    2. **Empirical**: based on historical co-occurrence (Pearson correlation)
    """)

    game = european_roulette()
    engine = CorrelationEngine()

    # Build win sets
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

    matrix = engine.compute_structural(game, win_sets)

    st.subheader("Try it: find correlated bets")
    bet_id = st.selectbox("Select a bet:", ["num_17", "red", "black", "even", "dozen_2"], key="tut_corr")

    correlated = matrix.get_correlated_bets(bet_id, threshold=0.1)
    if correlated:
        st.write(f"**{bet_id}** is correlated with:")
        for other_id, corr in correlated:
            st.write(f"- **{other_id}**: correlation = {corr:.3f}")
    else:
        st.write(f"No significant correlations found for **{bet_id}**")

    st.info("💡 High correlation means bets tend to win together. The portfolio engine "
            "uses this to avoid over-concentrating risk on correlated bets.")


def _step_portfolio():
    st.header("Step 10: Portfolio Optimization")
    st.markdown("""
    ### The key paradigm shift

    Instead of asking *"how much on this single bet?"*, the system asks:

    > *"What should the final profit distribution of the entire portfolio look like?"*

    The portfolio engine uses **constrained optimization (SLSQP)** to find stakes
    that maximize expected return while respecting:
    - Max 10% per bet
    - Max 30% per draw
    - Max 50% total exposure
    """)

    game = european_roulette()
    history = HistoryEngine("data/tutorial_history.db")
    extremum = ExtremumEngine(history)
    ve = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)

    extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
    value_results = ve.analyze_all(game, extremum_results)

    if st.button("Run Portfolio Optimization", type="primary", key="tut_portfolio"):
        allocation = portfolio.optimize(game, value_results)

        st.subheader("Optimal Allocation")
        rows = []
        for i, bid in enumerate(allocation.bet_ids):
            if allocation.stake_pcts[i] > 0.0001:
                rows.append({
                    "Bet": bid,
                    "Stake %": f"{allocation.stake_pcts[i]:.3%}",
                    "Stake zł": f"{allocation.stakes[i]:.2f}",
                })

        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No positive-EV bets found. Optimal allocation is 0 (don't bet).")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Exposure", f"{allocation.total_exposure:.2%}")
        col2.metric("Expected Return", f"{allocation.expected_return:+.2f} zł")
        col3.metric("Sharpe-like", f"{allocation.sharpe_like:.3f}")


def _step_monte_carlo():
    st.header("Step 11: Monte Carlo Simulation")
    st.markdown("""
    ### What Monte Carlo does

    Runs thousands of simulated outcomes to estimate:
    - **Expected Return**: average profit across all simulations
    - **Max Drawdown**: worst observed loss
    - **VaR (Value at Risk)**: loss threshold at 95% and 99% confidence
    - **CVaR (Conditional VaR)**: expected loss beyond VaR
    - **Ruin Probability**: chance of losing money
    - **Risk Score**: normalized risk metric (0-1)
    """)

    game = european_roulette()
    history = HistoryEngine("data/tutorial_history.db")
    extremum = ExtremumEngine(history)
    ve = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)
    mc = MonteCarloEngine(seed=42)

    extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
    value_results = ve.analyze_all(game, extremum_results)
    allocation = portfolio.optimize(game, value_results)

    n_sims = st.slider("Number of simulations", 1000, 50000, 10000, 1000, key="tut_mc")

    if st.button("Run Monte Carlo", type="primary", key="tut_mc_btn"):
        with st.spinner(f"Running {n_sims:,} simulations..."):
            # Build win sets
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

        # Histogram
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=result.profit_distribution, nbinsx=80,
            marker_color="steelblue", opacity=0.7,
        ))
        fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
        fig.add_vline(x=result.expected_return, line_dash="dash", line_color="green",
                     annotation_text=f"Mean: {result.expected_return:+.1f}")
        fig.update_layout(height=350, title=f"Profit Distribution ({n_sims:,} simulations)")
        st.plotly_chart(fig, use_container_width=True)


def _step_risk():
    st.header("Step 12: Risk Management")
    st.markdown("""
    ### Risk Limits

    The system enforces hard limits to prevent ruin:

    | Limit | Default | Meaning |
    |-------|---------|---------|
    | Max per bet | 10% | No single bet exceeds 10% of bankroll |
    | Max per hand | 20% | Correlated bets on same hand ≤ 20% |
    | Max per draw | 30% | Total exposure per round ≤ 30% |
    | Max total | 50% | All active positions ≤ 50% of bankroll |
    | Max drawdown | 25% | Stop if bankroll drops 25% from peak |
    """)

    game = european_roulette()
    history = HistoryEngine("data/tutorial_history.db")
    extremum = ExtremumEngine(history)
    ve = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)
    risk_mgr = RiskManager()

    extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
    value_results = ve.analyze_all(game, extremum_results)
    allocation = portfolio.optimize(game, value_results)

    st.subheader("Risk Assessment")

    report = risk_mgr.assess(allocation, st.session_state.bankroll)

    if report.is_acceptable:
        st.success("✅ All risk limits satisfied")
    else:
        st.error("⚠️ Risk limits exceeded!")
        for v in report.limits_exceeded:
            st.warning(f"- {v}")

    st.subheader("Current Limits")
    limits = RiskLimits()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Max per bet", f"{limits.max_per_bet:.0%}")
        st.metric("Max per hand", f"{limits.max_per_hand:.0%}")
        st.metric("Max per draw", f"{limits.max_per_draw:.0%}")
    with col2:
        st.metric("Max total", f"{limits.max_total:.0%}")
        st.metric("Max drawdown", f"{limits.max_drawdown:.0%}")
        st.metric("Min bankroll", f"{limits.min_bankroll:,.0f} zł")


def _step_loss_distribution():
    st.header("Step 13: Loss Distribution")
    st.markdown("""
    ### Understanding the full profit/loss picture

    The Loss Distribution Engine analyzes every possible outcome scenario:

    - **Best case**: maximum possible profit
    - **Worst case**: maximum possible loss
    - **Expected case**: probability-weighted average
    - **Median case**: 50th percentile outcome
    - **P(Profit)**: probability of positive return
    """)

    game = european_roulette()
    history = HistoryEngine("data/tutorial_history.db")
    extremum = ExtremumEngine(history)
    ve = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)
    risk_mgr = RiskManager()

    extremum_results = {r.bet_id: r for r in extremum.analyze_all(game)}
    value_results = ve.analyze_all(game, extremum_results)
    allocation = portfolio.optimize(game, value_results)

    # Build win sets
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
    all_outcomes = [str(i) for i in range(37)]
    scenarios = portfolio.analyze_scenarios(game, allocation, win_sets, all_outcomes, outcome_probs)
    loss_dist = risk_mgr.compute_loss_distribution(scenarios)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Best Case", f"{loss_dist.best_case:+.0f} zł")
    col2.metric("Worst Case", f"{loss_dist.worst_case:+.0f} zł")
    col3.metric("Expected", f"{loss_dist.expected_case:+.0f} zł")
    col4.metric("P(Profit)", f"{loss_dist.profit_probability:.1%}")

    # Scenario chart
    profits = [s.profit for s in scenarios]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"#{s.scenario_id}" for s in scenarios],
        y=profits,
        marker_color=["green" if p > 0 else "red" for p in profits],
    ))
    fig.add_hline(y=0, line_dash="solid", line_color="white")
    fig.update_layout(height=350, title="Profit by Scenario", xaxis_title="Scenario", yaxis_title="Profit (zł)")
    st.plotly_chart(fig, use_container_width=True)

    st.info(f"💡 {len(loss_dist.loss_scenarios)} scenarios lose money, "
            f"{len(loss_dist.profit_scenarios)} scenarios make money. "
            f"The system optimizes the portfolio to maximize expected return "
            f"while keeping worst-case losses within acceptable limits.")


def _step_combined():
    st.header("Step 14: Combined Portfolio")
    st.markdown("""
    ### Cross-game portfolio optimization

    The system can optimize across multiple games simultaneously.
    This is the ultimate expression of the portfolio approach:
    balancing roulette bets against poker bets in one unified allocation.
    """)

    roulette = european_roulette()
    poker = texas_holdem_hand_rankings()

    rh = HistoryEngine("data/tutorial_history.db")
    ph = HistoryEngine("data/poker_history.db")

    re = ExtremumEngine(rh)
    pe = ExtremumEngine(ph)
    ve = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)

    r_ext = {r.bet_id: r for r in re.analyze_all(roulette)}
    p_ext = {r.bet_id: r for r in pe.analyze_all(poker)}
    r_val = ve.analyze_all(roulette, r_ext)
    p_val = ve.analyze_all(poker, p_ext)

    combined = Game(name="Combined", bets=roulette.bets + poker.bets)
    combined_val = r_val + p_val

    if st.button("Optimize Combined Portfolio", type="primary", key="tut_combined"):
        allocation = portfolio.optimize(combined, combined_val)

        st.subheader("Cross-Game Allocation")
        rows = []
        for i, bid in enumerate(allocation.bet_ids):
            if allocation.stake_pcts[i] > 0.0001:
                game_name = "Roulette" if bid in [b.id for b in roulette.bets] else "Poker"
                rows.append({
                    "Game": game_name,
                    "Bet": bid,
                    "Stake %": f"{allocation.stake_pcts[i]:.3%}",
                    "Stake zł": f"{allocation.stakes[i]:.2f}",
                })

        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.metric("Total Exposure", f"{allocation.total_exposure:.2%}")
            st.metric("Expected Return", f"{allocation.expected_return:+.2f} zł")
        else:
            st.info("No positive-EV bets across either game. Optimal: don't bet.")


def _step_summary():
    st.header("🎉 Tutorial Complete!")
    st.markdown("""
    ### What you've learned:

    1. **Game Model** — abstract Bet/Game classes, game-agnostic design
    2. **History Engine** — SQLite storage, rolling windows (50-5000)
    3. **Z-Score** — statistical deviation from expected
    4. **Extremum Index** — multi-window signal aggregation
    5. **MRF** — learned mean reversion parameter
    6. **Value Engine** — EV, Kelly criterion, fractional Kelly
    7. **Correlation Engine** — structural and empirical dependencies
    8. **Portfolio Optimization** — constrained optimization across all bets
    9. **Monte Carlo** — VaR, CVaR, ruin probability, risk scoring
    10. **Risk Management** — exposure limits, drawdown controls
    11. **Loss Distribution** — full scenario analysis

    ### Where to go from here:

    - **Roulette page**: real-time recommendations with live data
    - **Poker page**: hand ranking analysis
    - **Portfolio page**: cross-game optimization
    - **History page**: record draws and watch signals evolve
    - **Settings page**: adjust risk limits and parameters

    ### Extending the system:

    Add new games by implementing the `Game` interface in `games/`.
    The entire pipeline (history → extremum → value → portfolio → MC → risk)
    works automatically for any game.
    """)

    st.balloons()

    if st.button("🔄 Restart Tutorial", key="tut_restart"):
        st.session_state.tutorial_step = 0
        st.rerun()
