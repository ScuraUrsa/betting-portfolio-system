"""Roulette recommendations page with interactive wheel visualization."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from games.roulette import european_roulette
from games.roulette_wheel import (
    WHEEL_ORDER, RED_NUMBERS, BLACK_NUMBERS,
    JEU_0, VOISINS_DU_ZERO, TIERS_DU_CYLINDRE, ORPHELINS,
    get_color, get_parity, get_half, get_dozen, get_column, get_section,
    get_neighbors, get_opposite, get_opposite_zone,
    build_wheel_figure, build_wheel_figure_highlighted,
)
from core.extremum import ExtremumEngine
from core.value import ValueEngine
from core.portfolio import PortfolioEngine
from core.monte_carlo import MonteCarloEngine
from core.i18n import Translator
from core.session import SessionManager
from core.session_history_adapter import SessionHistoryAdapter


def _get_history():
    """Get session-aware history adapter for the active session."""
    mgr: SessionManager = st.session_state.get("session_mgr")
    sid = st.session_state.get("active_session_id")
    if mgr is None or sid is None:
        return None
    return SessionHistoryAdapter(mgr, sid)


def _build_bet_rows(game, extremum, ve, bankroll, t):
    """Build recommendation rows for a set of bets."""
    ext_map = {r.bet_id: r for r in extremum.analyze_all(game)}
    vals = ve.analyze_all(game, ext_map)

    rows = []
    for vr in vals:
        ext = ext_map.get(vr.bet_id)
        rows.append({
            t.t("rec_bet"): vr.bet_name,
            t.t("rec_id"): vr.bet_id,
            t.t("rec_probability"): f"{vr.probability*100:.2f}%",
            t.t("rec_odds"): f"{vr.odds:.1f}",
            t.t("rec_ev"): f"{vr.ev:+.4f}",
            t.t("rec_kelly"): f"{vr.kelly_quarter:.4f}",
            t.t("rec_signal"): ext.signal_level if ext else "none",
            t.t("rec_direction"): ext.direction if ext else "neutral",
            t.t("rec_stake_pct"): f"{vr.recommended_stake_pct:.2%}",
            t.t("rec_stake_pln"): f"{vr.recommended_stake_pct * bankroll:.2f}",
        })

    order = {"maximum": 0, "medium": 1, "entry_small": 2, "observation": 3, "none": 4}
    rows.sort(key=lambda r: order.get(r[t.t("rec_signal")], 5))
    return rows


def _render_recommendations_table(rows, t):
    """Render the recommendations dataframe with active signal count."""
    st.dataframe(rows, width='stretch', hide_index=True)
    active = [r for r in rows if r[t.t("rec_signal")] != "none"]
    if active:
        st.success(t.t("active_signals_count", count=len(active)))
    else:
        st.info(t.t("no_signals"))


def _render_signals_tab(game, extremum, t):
    """Render the Z-score / Extremum Index signals tab."""
    st.subheader(t.t("roulette_signal_title"))
    sel = st.selectbox(t.t("roulette_signal_select"), [b.id for b in game.bets], index=0)
    if sel:
        r = extremum.analyze(game, sel)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t.t("metric_ei"), f"{r.extremum_index:.3f}")
        c2.metric(t.t("metric_max_z"), f"{r.max_z_score:.3f}")
        c3.metric(t.t("metric_direction"), r.direction)
        c4.metric(t.t("metric_signal"), r.signal_level)

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
            fig.update_layout(title=t.t("zscore_chart_title", bet_id=sel), height=400)
            st.plotly_chart(fig, width='stretch')


def _render_monte_carlo_tab(game, extremum, ve, portfolio, mc, t):
    """Render the Monte Carlo simulation tab."""
    st.subheader(t.t("roulette_monte_carlo_title"))
    n = st.slider(t.t("roulette_monte_carlo_slider"), 1000, 100000, 10000, step=1000)
    if st.button(t.t("roulette_monte_carlo_button"), type="primary"):
        with st.spinner(t.t("roulette_monte_carlo_running", n=n)):
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
        c1.metric(t.t("metric_expected_return"), f"{res.expected_return:+.2f} zł")
        c2.metric(t.t("metric_std_dev"), f"{res.std_return:.2f} zł")
        c3.metric(t.t("metric_max_drawdown"), f"{res.max_drawdown:.2f} zł")
        c4.metric(t.t("metric_ruin_prob"), f"{res.ruin_probability:.2%}")
        c5, c6 = st.columns(2)
        c5.metric(t.t("metric_var_95"), f"{res.var_95:.2f} zł")
        c6.metric(t.t("metric_cvar_95"), f"{res.cvar_95:.2f} zł")

        fig = go.Figure(go.Histogram(
            x=res.profit_distribution, nbinsx=100,
            marker_color="steelblue", opacity=0.7,
        ))
        fig.add_vline(x=0, line_dash="dash", line_color="red",
                      annotation_text=t.t("mc_break_even"))
        fig.add_vline(
            x=res.expected_return, line_dash="dash", line_color="green",
            annotation_text=t.t("mc_mean", value=res.expected_return),
        )
        fig.update_layout(title=t.t("mc_profit_distribution", n=n), height=400)
        st.plotly_chart(fig, width='stretch')


def _render_wheel_tab(t):
    """Render the interactive wheel visualization tab with highlighting."""
    st.subheader(t.t("roulette_wheel_title"))
    st.caption(t.t("roulette_wheel_hint"))

    # ── Controls ──────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        lookup = st.number_input(
            t.t("roulette_lookup_label"),
            min_value=0, max_value=36, value=17, step=1,
            key="wheel_lookup",
        )
    with c2:
        neighbor_count = st.slider(
            "Neighbors each side",
            min_value=1, max_value=5, value=2, step=1,
            key="wheel_neighbors",
        )
    with c3:
        opposite_spread = st.slider(
            "Opposite zone spread",
            min_value=0, max_value=3, value=1, step=1,
            help="0 = just the 2 opposite numbers, 1-3 = +N neighbors around each",
            key="wheel_opposite_spread",
        )

    n = int(lookup)

    # ── Highlighted wheel ─────────────────────────────────────────────
    fig = build_wheel_figure_highlighted(
        selected_number=n,
        neighbor_count=neighbor_count,
        opposite_spread=opposite_spread,
        height=550,
    )
    st.plotly_chart(fig, width='stretch')

    # ── Legend ────────────────────────────────────────────────────────
    st.caption(
        "⬜ **White border** = selected number  |  "
        "🟡 **Gold border** = neighbors  |  "
        "🔵 **Cyan border** = opposite zone"
    )

    # ── Number detail lookup ─────────────────────────────────────────
    st.markdown("---")
    st.subheader(t.t("roulette_lookup_title"))

    c = get_color(n)
    neighbors = get_neighbors(n, neighbor_count)
    opp = get_opposite(n)
    opp_zone = get_opposite_zone(n, opposite_spread)

    color_map = {"green": t.t("prop_green"), "red": t.t("prop_red"), "black": t.t("prop_black")}
    parity_map = {"even": t.t("prop_even"), "odd": t.t("prop_odd"), "—": t.t("prop_na")}
    half_map = {"low (1-18)": t.t("prop_low"), "high (19-36)": t.t("prop_high"), "—": t.t("prop_na")}
    dozen_map = {"1st 12": t.t("prop_dozen_1"), "2nd 12": t.t("prop_dozen_2"), "3rd 12": t.t("prop_dozen_3"), "—": t.t("prop_na")}
    col_map = {"Column 1": t.t("prop_col_1"), "Column 2": t.t("prop_col_2"), "Column 3": t.t("prop_col_3"), "—": t.t("prop_na")}
    section_map = {"Jeu 0": t.t("prop_jeu0"), "Voisins du Zéro": t.t("prop_voisins"), "Tiers du Cylindre": t.t("prop_tiers"), "Orphelins": t.t("prop_orphelins"), "—": t.t("prop_na")}

    cols = st.columns(4)
    cols[0].metric(t.t("metric_color"), color_map.get(c, c))
    cols[1].metric(t.t("metric_parity"), parity_map.get(get_parity(n), get_parity(n)))
    cols[2].metric(t.t("metric_half"), half_map.get(get_half(n), get_half(n)))
    cols[3].metric(t.t("metric_dozen"), dozen_map.get(get_dozen(n), get_dozen(n)))

    cols2 = st.columns(3)
    cols2[0].metric(t.t("metric_column"), col_map.get(get_column(n), get_column(n)))
    cols2[1].metric(t.t("metric_section"), section_map.get(get_section(n), get_section(n)))
    cols2[2].metric(t.t("metric_wheel_pos"), f"#{WHEEL_ORDER.index(n) + 1}/37")

    # ── Neighbors display ─────────────────────────────────────────────
    st.markdown(f"**{t.t('neighbors_label')} ({neighbor_count} each side)**")
    left_nbs = neighbors[:neighbor_count]
    right_nbs = neighbors[neighbor_count:]
    st.markdown(
        " ".join(f"`{x}`" for x in left_nbs)
        + f" **← `{n}` →** "
        + " ".join(f"`{x}`" for x in right_nbs)
    )

    # ── Opposite zone display ────────────────────────────────────────
    st.markdown(f"**{t.t('opposite_label')}:** `{opp[0]}`, `{opp[1]}`")
    if opposite_spread > 0:
        opp_sorted = sorted(opp_zone - {opp[0], opp[1]})
        st.caption(
            f"Opposite zone (+{opposite_spread} neighbors): "
            + ", ".join(f"`{x}`" for x in opp_sorted)
        )


def _render_french_bets_tab(t):
    """Render the French announced bets tab."""
    st.subheader(t.t("roulette_french_title"))
    st.caption(t.t("roulette_french_hint"))

    sections = {
        t.t("roulette_french_jeu0"): JEU_0,
        t.t("roulette_french_voisins"): VOISINS_DU_ZERO,
        t.t("roulette_french_tiers"): TIERS_DU_CYLINDRE,
        t.t("roulette_french_orphelins"): ORPHELINS,
    }

    for name, numbers in sections.items():
        with st.expander(f"{name} — {t.t('french_numbers_count', count=len(numbers))}", expanded=False):
            sorted_nums = sorted(numbers)
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

            st.caption(t.t("roulette_french_coverage", covered=len(numbers), total=37, pct=len(numbers)/37*100))


def show():
    if "bankroll" not in st.session_state:
        st.session_state.bankroll = 1000.0

    t = Translator()
    t.set_lang(st.session_state.get("lang", "en"))

    st.title(t.t("roulette_title"))

    history = _get_history()
    if history is None:
        st.warning("No active session. Create a roulette session in the sidebar first.")
        return

    game = european_roulette()
    extremum = ExtremumEngine(history)
    ve = ValueEngine()
    portfolio = PortfolioEngine(bankroll=st.session_state.bankroll)
    mc = MonteCarloEngine(seed=42)

    tab_wheel, tab_numbers, tab_bets, tab_french, tab_signals, tab_mc = st.tabs([
        t.t("roulette_tab_wheel"),
        t.t("roulette_tab_numbers"),
        t.t("roulette_tab_other"),
        t.t("roulette_tab_french"),
        t.t("roulette_tab_signals"),
        t.t("roulette_tab_monte_carlo"),
    ])

    with tab_wheel:
        _render_wheel_tab(t)

    with tab_numbers:
        st.subheader(t.t("roulette_numbers_title"))
        st.caption(t.t("roulette_numbers_hint"))

        num_game = type(game)("Roulette Numbers", [b for b in game.bets if b.id.startswith("num_")])
        rows = _build_bet_rows(num_game, extremum, ve, st.session_state.bankroll, t)
        _render_recommendations_table(rows, t)

    with tab_bets:
        st.subheader(t.t("roulette_other_title"))
        st.caption(t.t("roulette_other_hint"))

        other_bets = [b for b in game.bets if not b.id.startswith("num_")]
        other_game = type(game)("Roulette Other Bets", other_bets)
        rows = _build_bet_rows(other_game, extremum, ve, st.session_state.bankroll, t)
        _render_recommendations_table(rows, t)

    with tab_french:
        _render_french_bets_tab(t)

    with tab_signals:
        _render_signals_tab(game, extremum, t)

    with tab_mc:
        _render_monte_carlo_tab(game, extremum, ve, portfolio, mc, t)
