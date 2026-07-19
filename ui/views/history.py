"""History & Signals page — session-aware draw history and Z-score visualization."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from games.roulette import european_roulette
from games.poker import texas_holdem_hand_rankings
from core.extremum import ExtremumEngine
from core.i18n import Translator
from core.session import SessionManager
from core.session_history_adapter import SessionHistoryAdapter


def _get_active_session():
    """Get the active session or return None with a warning."""
    mgr: SessionManager = st.session_state.get("session_mgr")
    if mgr is None:
        st.warning("Session manager not initialized")
        return None, None, None

    sid = st.session_state.get("active_session_id")
    if sid is None:
        st.info("No active session. Create one in the sidebar.")
        return None, None, None

    session = mgr.get(sid)
    if session is None:
        st.warning("Session not found. Create a new one.")
        return None, None, None

    history = SessionHistoryAdapter(mgr, sid)
    return session, history, mgr


def show():
    t = Translator()
    t.set_lang(st.session_state.get("lang", "en"))

    st.title(t.t("history_title"))

    session, history, mgr = _get_active_session()
    if session is None:
        return

    # Show session info
    game_type_label = "🎰 Roulette" if session.game_type == "roulette" else "🃏 Poker"
    st.caption(f"Session: **{session.name}** (#{session.session_id}) — {game_type_label}")

    # Load the right game
    if session.game_type == "roulette":
        game = european_roulette()
    else:
        game = texas_holdem_hand_rankings()

    extremum = ExtremumEngine(history)

    tab1, tab2, tab3 = st.tabs([
        t.t("history_tab_record"),
        t.t("history_tab_heatmap"),
        t.t("history_tab_draws"),
    ])

    with tab1:
        st.subheader(t.t("history_record_title"))

        if session.game_type == "roulette":
            _record_roulette_draw(game, history, session)
        else:
            _record_poker_draw(game, history, session)

        st.metric("Total draws recorded", history.count_draws(game.name))

        # Quick batch generation
        st.markdown("---")
        st.subheader("Generate Test Data")
        n_gen = st.slider("Number of random draws", 10, 1000, 100)
        if st.button("Generate Random Draws"):
            with st.spinner(f"Generating {n_gen} draws..."):
                if session.game_type == "roulette":
                    _generate_roulette_draws(game, history, n_gen)
                else:
                    _generate_poker_draws(game, history, n_gen)
            st.success(f"Generated {n_gen} random draws")
            st.rerun()

    with tab2:
        st.subheader(t.t("history_heatmap_title"))

        if history.count_draws(game.name) < 10:
            st.info("Need at least 10 draws. Record some data first.")
        else:
            results = extremum.analyze_all(game)
            results.sort(key=lambda r: abs(r.extremum_index), reverse=True)

            rows = []
            for r in results[:20]:
                rows.append({
                    t.t("rec_bet"): r.bet_id,
                    t.t("metric_ei"): f"{r.extremum_index:+.3f}",
                    t.t("metric_max_z"): f"{r.max_z_score:+.2f}",
                    t.t("metric_direction"): r.direction,
                    t.t("metric_signal"): r.signal_level,
                })

            st.dataframe(rows, width='stretch', hide_index=True)

            st.subheader("Z-Score Heatmap")
            selected_bets = [r.bet_id for r in results[:15]]

            z_data = []
            for bid in selected_bets:
                stats = history.compute_all_windows(game, bid)
                z_data.append([ws.z_score for ws in stats if ws.n_draws > 0])

            if z_data:
                windows = [50, 100, 250, 500, 1000, 5000]
                fig = go.Figure(data=go.Heatmap(
                    z=z_data,
                    x=[str(w) for w in windows],
                    y=selected_bets,
                    colorscale="RdBu_r",
                    zmid=0,
                    text=[[f"{v:.2f}" for v in row] for row in z_data],
                    texttemplate="%{text}",
                ))
                fig.update_layout(
                    title="Z-Score by Bet × Window",
                    height=500,
                )
                st.plotly_chart(fig, width='stretch')

    with tab3:
        st.subheader(t.t("history_draws_title"))

        limit = st.slider("Show last N draws", 10, 500, 50, key="history_limit")
        draws = history.get_draws(game.name, limit=limit)

        if draws:
            rows = []
            for d in draws:
                rows.append({
                    "ID": d.draw_id,
                    "Time": d.timestamp[:19],
                    "Outcome": d.raw_outcome,
                    "Won Bets": ", ".join(d.won_bet_ids[:5]) + ("..." if len(d.won_bet_ids) > 5 else ""),
                })
            st.dataframe(rows, width='stretch', hide_index=True)
        else:
            st.info("No draws recorded yet")


def _record_roulette_draw(game, history, session):
    """Record a roulette draw for the active session."""
    col1, col2 = st.columns([1, 2])
    with col1:
        number = st.number_input("Number drawn", 0, 36, 0)

    with col2:
        red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        won = [f"num_{number}"]

        if number != 0:
            if number in red_numbers:
                won.append("red")
            else:
                won.append("black")
            if number % 2 == 0:
                won.append("even")
            else:
                won.append("odd")
            if number <= 18:
                won.append("low")
            else:
                won.append("high")
            dozen = (number - 1) // 12 + 1
            won.append(f"dozen_{dozen}")
            col = (number - 1) % 3 + 1
            won.append(f"col_{col}")

        st.write(f"Winning bets: **{', '.join(won)}**")

    if st.button("Record Draw", type="primary"):
        draw_id = history.record_draw(game, str(number), won)
        st.success(f"Draw #{draw_id} recorded: {number} → {len(won)} bets won")


def _record_poker_draw(game, history, session):
    """Record a poker draw for the active session."""
    hand_options = [(b.id, b.name) for b in game.bets]
    hand_id = st.selectbox(
        "Hand achieved",
        [h[0] for h in hand_options],
        format_func=lambda x: dict(hand_options)[x],
    )

    if st.button("Record Draw", type="primary"):
        draw_id = history.record_draw(game, hand_id, [hand_id])
        st.success(f"Draw #{draw_id} recorded: {dict(hand_options)[hand_id]}")


def _generate_roulette_draws(game, history, n):
    """Generate random roulette draws."""
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    rng = np.random.default_rng()
    for _ in range(n):
        num = int(rng.integers(0, 37))
        w = [f"num_{num}"]
        if num != 0:
            if num in red_numbers:
                w.append("red")
            else:
                w.append("black")
            if num % 2 == 0:
                w.append("even")
            else:
                w.append("odd")
            if num <= 18:
                w.append("low")
            else:
                w.append("high")
            w.append(f"dozen_{(num - 1) // 12 + 1}")
            w.append(f"col_{(num - 1) % 3 + 1}")
        history.record_draw(game, str(num), w)


def _generate_poker_draws(game, history, n):
    """Generate random poker draws."""
    hand_ids = [b.id for b in game.bets]
    probs = np.array([b.probability for b in game.bets])
    probs = probs / probs.sum()
    rng = np.random.default_rng()
    for _ in range(n):
        hand = rng.choice(hand_ids, p=probs)
        history.record_draw(game, hand, [hand])
