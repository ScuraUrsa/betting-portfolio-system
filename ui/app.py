"""Betting Portfolio System — Streamlit Dashboard.

Run with: streamlit run ui/app.py
"""

import streamlit as st
import traceback

from core.i18n import Translator
from core.session import SessionManager
from core.session_history_adapter import SessionHistoryAdapter

st.set_page_config(
    page_title="Betting Portfolio System",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ────────────────────────────────────────────────
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "session_mgr" not in st.session_state:
    st.session_state.session_mgr = SessionManager("data/sessions.db")
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "tutorial"

t = Translator()
t.set_lang(st.session_state.lang)
mgr: SessionManager = st.session_state.session_mgr

# ── Navigation key → translated label ─────────────────────────────────
NAV_KEYS = ["tutorial", "roulette", "poker", "portfolio", "history", "settings"]
NAV_LABELS = {
    "tutorial": t.t("nav_tutorial"),
    "roulette": t.t("nav_roulette"),
    "poker": t.t("nav_poker"),
    "portfolio": t.t("nav_portfolio"),
    "history": t.t("nav_history"),
    "settings": t.t("nav_settings"),
}

# ── Sidebar ───────────────────────────────────────────────────────────
st.sidebar.title("🎲 Betting Portfolio")
st.sidebar.markdown("---")

# Session selector
st.sidebar.subheader("🎯 Active Session")
sessions = mgr.list_all()

if sessions:
    session_names = [f"#{s.session_id}: {s.name} ({s.game_type})" for s in sessions]
    current_idx = 0
    if "active_session_id" in st.session_state:
        for i, s in enumerate(sessions):
            if s.session_id == st.session_state.active_session_id:
                current_idx = i
                break

    selected = st.sidebar.selectbox(
        "Select session",
        session_names,
        index=current_idx,
        label_visibility="collapsed",
    )
    selected_idx = session_names.index(selected)
    st.session_state.active_session_id = sessions[selected_idx].session_id
else:
    st.sidebar.caption("No sessions yet — create one below")
    if "active_session_id" in st.session_state:
        del st.session_state.active_session_id

# Create new session
with st.sidebar.expander("➕ New Session", expanded=not sessions):
    new_name = st.text_input("Session name", placeholder="e.g. Table 1, Casino Warsaw")
    new_game = st.selectbox("Game type", ["roulette", "poker"], format_func=lambda x: "🎰 Roulette" if x == "roulette" else "🃏 Poker")
    if st.button("Create Session", type="primary", disabled=not new_name.strip()):
        s = mgr.create(new_name.strip(), new_game)
        st.session_state.active_session_id = s.session_id
        st.rerun()

# Delete current session
if sessions and "active_session_id" in st.session_state:
    active = mgr.get(st.session_state.active_session_id)
    if active:
        with st.sidebar.expander("🗑️ Manage Session"):
            if st.button(f"Delete '{active.name}'", type="secondary"):
                mgr.delete(active.session_id)
                if "active_session_id" in st.session_state:
                    del st.session_state.active_session_id
                st.rerun()

st.sidebar.markdown("---")
st.sidebar.metric(t.t("bankroll_label"), f"{st.session_state.bankroll:,.0f} zł")

# Navigation — use selectbox with keys, not radio with translated strings
current_nav_label = NAV_LABELS.get(st.session_state.nav_page, NAV_LABELS["tutorial"])
selected_label = st.sidebar.selectbox(
    t.t("navigation_label"),
    [NAV_LABELS[k] for k in NAV_KEYS],
    index=NAV_KEYS.index(st.session_state.nav_page),
    label_visibility="visible",
)
# Map label back to key
for k, v in NAV_LABELS.items():
    if v == selected_label:
        st.session_state.nav_page = k
        break

st.sidebar.markdown("---")
st.sidebar.caption(t.t("app_tagline"))

# ── Page routing ──────────────────────────────────────────────────────
try:
    page_key = st.session_state.nav_page
    if page_key == "tutorial":
        from ui.views.tutorial import show
    elif page_key == "roulette":
        from ui.views.roulette import show
    elif page_key == "poker":
        from ui.views.poker import show
    elif page_key == "portfolio":
        from ui.views.portfolio import show
    elif page_key == "history":
        from ui.views.history import show
    elif page_key == "settings":
        from ui.views.settings import show
    show()
except Exception as e:
    st.error(t.t("page_crashed", error=str(e)))
    st.code(traceback.format_exc())
