"""History & Signals page — draw history and Z-score visualization."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from games.roulette import european_roulette
from core.history import HistoryEngine
from core.extremum import ExtremumEngine
from core.i18n import Translator


def show():
    t = Translator()
    t.set_lang(st.session_state.get("lang", "en"))

    st.title(t.t("history_title"))

    game = european_roulette()
    history = HistoryEngine("data/roulette_history.db")
    extremum = ExtremumEngine(history)

    tab1, tab2, tab3 = st.tabs([
        t.t("history_tab_record"),
        t.t("history_tab_heatmap"),
        t.t("history_tab_draws"),
    ])

    with tab1:
        st.subheader(t.t("history_record_title"))

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

        st.metric("Total draws recorded", history.count_draws(game.name))

        st.markdown("---")
        st.subheader("Generate Test Data")
        n_gen = st.slider("Number of random draws", 10, 1000, 100)
        if st.button("Generate Random Draws"):
            with st.spinner(f"Generating {n_gen} draws..."):
                rng = np.random.default_rng()
                for _ in range(n_gen):
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
