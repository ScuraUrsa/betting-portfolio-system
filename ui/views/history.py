"""History & Signals page — draw history and Z-score visualization."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from games.roulette import european_roulette
from core.history import HistoryEngine
from core.extremum import ExtremumEngine


def show():
    st.title("📈 History & Signals")

    game = european_roulette()
    history = HistoryEngine("data/roulette_history.db")
    extremum = ExtremumEngine(history)

    tab1, tab2, tab3 = st.tabs(["📝 Record Draw", "📊 Z-Score Dashboard", "📋 Draw History"])

    with tab1:
        st.subheader("Record a Roulette Draw")

        col1, col2 = st.columns([1, 2])
        with col1:
            number = st.number_input("Number drawn", 0, 36, 0)

        with col2:
            # Determine which bets win
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

        # Quick batch generation
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
        st.subheader("Z-Score Dashboard")

        if history.count_draws(game.name) < 10:
            st.info("Need at least 10 draws. Record some data first.")
        else:
            # Show Z-scores for all bets
            results = extremum.analyze_all(game)

            # Sort by absolute EI
            results.sort(key=lambda r: abs(r.extremum_index), reverse=True)

            rows = []
            for r in results[:20]:  # top 20
                rows.append({
                    "Bet": r.bet_id,
                    "EI": f"{r.extremum_index:+.3f}",
                    "Max Z": f"{r.max_z_score:+.2f}",
                    "Direction": r.direction,
                    "Signal": r.signal_level,
                })

            st.dataframe(rows, use_container_width=True, hide_index=True)

            # Heatmap of Z-scores
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
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Draw History")

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
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No draws recorded yet")


