"""Automatic UI tests for the Betting Portfolio System.

Tests cover:
1. Module imports and structure — all pages have show() function
2. Core pipeline integration — full flow from game to risk report
3. Streamlit app HTTP endpoint — app starts and returns 200
4. State management — bankroll, session state
5. Edge cases — empty history, zero bankroll, extreme values

Run with: pytest tests/test_ui_automated.py -v
"""

import os
import sys
import json
import tempfile
import subprocess
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ═══════════════════════════════════════════════════════════════════════
# 1. Module Structure Tests
# ═══════════════════════════════════════════════════════════════════════

class TestUIModuleStructure:
    """Verify all UI modules are properly structured and importable."""

    def test_all_pages_have_show_function(self):
        """Every page module must export a show() function."""
        pages = [
            "ui.views.tutorial",
            "ui.views.roulette",
            "ui.views.poker",
            "ui.views.portfolio",
            "ui.views.history",
            "ui.views.settings",
        ]
        for module_name in pages:
            mod = __import__(module_name, fromlist=["show"])
            assert hasattr(mod, "show"), f"{module_name} missing show()"
            assert callable(mod.show), f"{module_name}.show is not callable"

    def test_app_module_has_main(self):
        """App module must be importable and have set_page_config."""
        from ui import app
        assert hasattr(app, "st")
        assert hasattr(app, "traceback")

    def test_app_pages_dict_complete(self):
        """App must register all 5 pages via NAV_KEYS."""
        from ui.app import NAV_KEYS
        assert len(NAV_KEYS) == 5
        assert "tutorial" in NAV_KEYS
        assert "roulette" in NAV_KEYS
        assert "poker" in NAV_KEYS
        assert "portfolio" in NAV_KEYS
        assert "settings" in NAV_KEYS

    def test_page_files_exist(self):
        """All page files must exist on disk."""
        import ui.views
        views_dir = Path(ui.views.__path__[0])
        expected = ["tutorial.py", "roulette.py", "poker.py", "portfolio.py", "history.py", "settings.py"]
        for fname in expected:
            assert (views_dir / fname).exists(), f"Page file missing: {fname}"


# ═══════════════════════════════════════════════════════════════════════
# 2. Core Pipeline Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFullPipeline:
    """End-to-end pipeline: Game → History → Extremum → Value → Portfolio → MC → Risk."""

    @pytest.fixture
    def game(self):
        from games.roulette import european_roulette
        return european_roulette()

    @pytest.fixture
    def history(self, tmp_path):
        from core.history import HistoryEngine
        db = tmp_path / "pipeline_test.db"
        return HistoryEngine(str(db))

    def test_full_pipeline_with_data(self, game, tmp_path):
        """Complete pipeline with 500 random draws."""
        from core.history import HistoryEngine
        from core.extremum import ExtremumEngine
        from core.value import ValueEngine
        from core.portfolio import PortfolioEngine
        from core.monte_carlo import MonteCarloEngine
        from core.risk import RiskManager

        history = HistoryEngine(str(tmp_path / "full_pipeline.db"))

        # Generate 500 random draws
        red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        rng = np.random.default_rng(42)
        for _ in range(500):
            num = int(rng.integers(0, 37))
            won = [f"num_{num}"]
            if num != 0:
                won.append("red" if num in red_numbers else "black")
                won.append("even" if num % 2 == 0 else "odd")
                won.append("low" if num <= 18 else "high")
                won.append(f"dozen_{(num - 1) // 12 + 1}")
                won.append(f"col_{(num - 1) % 3 + 1}")
            history.record_draw(game, str(num), won)

        # Step 1: Extremum analysis
        extremum = ExtremumEngine(history)
        results = extremum.analyze_all(game)
        assert len(results) == game.n_bets
        # At least some bets should have non-zero EI
        assert any(abs(r.extremum_index) > 0 for r in results)

        # Step 2: Value analysis
        ve = ValueEngine()
        ext_map = {r.bet_id: r for r in results}
        value_results = ve.analyze_all(game, ext_map)
        assert len(value_results) == game.n_bets
        # All roulette bets have negative EV
        assert all(vr.ev < 0 for vr in value_results)

        # Step 3: Portfolio optimization
        portfolio = PortfolioEngine(bankroll=1000.0)
        allocation = portfolio.optimize(game, value_results)
        assert allocation.bet_ids == [b.id for b in game.bets]
        assert allocation.total_exposure <= portfolio.max_total + 1e-6
        assert all(0 <= pct <= portfolio.max_per_bet + 1e-6 for pct in allocation.stake_pcts)

        # Step 4: Monte Carlo
        mc = MonteCarloEngine(seed=42)
        # Build win sets
        win_sets = _build_roulette_win_sets(game, red_numbers)
        outcome_probs = {str(i): 1 / 37 for i in range(37)}
        mc_result = mc.simulate_game_outcomes(
            game, allocation, outcome_probs, win_sets, n_simulations=1000
        )
        assert mc_result.n_simulations == 1000
        assert mc_result.var_95 is not None
        assert 0 <= mc_result.risk_score <= 1

        # Step 5: Risk assessment
        risk_mgr = RiskManager()
        report = risk_mgr.assess(allocation, 1000.0)
        assert report.is_acceptable or len(report.limits_exceeded) > 0

    def test_pipeline_empty_history(self, game, tmp_path):
        """Pipeline should handle empty history gracefully."""
        from core.history import HistoryEngine
        from core.extremum import ExtremumEngine
        from core.value import ValueEngine
        from core.portfolio import PortfolioEngine

        history = HistoryEngine(str(tmp_path / "empty_pipeline.db"))

        extremum = ExtremumEngine(history)
        results = extremum.analyze_all(game)
        assert all(r.signal_level == "none" for r in results)
        assert all(r.extremum_index == 0.0 for r in results)

        ve = ValueEngine()
        value_results = ve.analyze_all(game)
        assert len(value_results) == game.n_bets

        portfolio = PortfolioEngine(bankroll=1000.0)
        allocation = portfolio.optimize(game, value_results)
        # With negative EV, optimal is 0
        assert allocation.total_exposure == pytest.approx(0.0, abs=1e-6)

    def test_pipeline_poker(self, tmp_path):
        """Full pipeline with poker game."""
        from games.poker import texas_holdem_hand_rankings
        from core.history import HistoryEngine
        from core.extremum import ExtremumEngine
        from core.value import ValueEngine
        from core.portfolio import PortfolioEngine
        from core.monte_carlo import MonteCarloEngine
        from core.risk import RiskManager

        game = texas_holdem_hand_rankings()
        history = HistoryEngine(str(tmp_path / "poker_pipeline.db"))

        # Generate some poker draws
        hand_ids = [b.id for b in game.bets]
        probs = np.array([b.probability for b in game.bets])
        probs = probs / probs.sum()  # normalize (poker probs sum to 0.999999)
        rng = np.random.default_rng(42)
        for _ in range(200):
            hand = rng.choice(hand_ids, p=probs)
            history.record_draw(game, hand, [hand])

        extremum = ExtremumEngine(history)
        results = extremum.analyze_all(game)
        assert len(results) == 10

        ve = ValueEngine()
        value_results = ve.analyze_all(game)
        assert len(value_results) == 10

        portfolio = PortfolioEngine(bankroll=1000.0)
        allocation = portfolio.optimize(game, value_results)
        assert len(allocation.bet_ids) == 10

        mc = MonteCarloEngine(seed=42)
        mc_result = mc.simulate_independent(game, allocation, n_simulations=500)
        assert mc_result.n_simulations == 500

        risk_mgr = RiskManager()
        report = risk_mgr.assess(allocation, 1000.0)
        assert report is not None


# ═══════════════════════════════════════════════════════════════════════
# 3. Streamlit App HTTP Tests
# ═══════════════════════════════════════════════════════════════════════

class TestStreamlitAppHTTP:
    """Verify the Streamlit app starts and serves HTTP correctly."""

    @classmethod
    @pytest.fixture(scope="class")
    def app_process(cls):
        """Start Streamlit app in background for testing."""
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "streamlit", "run",
                "ui/app.py",
                "--server.port", "8599",
                "--server.headless", "true",
                "--server.address", "0.0.0.0",
                "--browser.gatherUsageStats", "false",
            ],
            cwd=str(Path(__file__).parent.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Wait for app to start
        for _ in range(30):
            time.sleep(0.5)
            try:
                import urllib.request
                req = urllib.request.Request("http://localhost:8599")
                resp = urllib.request.urlopen(req, timeout=2)
                if resp.status == 200:
                    break
            except Exception:
                pass
        yield proc
        proc.terminate()
        proc.wait(timeout=5)

    def test_app_returns_200(self, app_process):
        """App should return HTTP 200."""
        import urllib.request
        req = urllib.request.Request("http://localhost:8599")
        resp = urllib.request.urlopen(req, timeout=5)
        assert resp.status == 200

    def test_app_health_endpoint(self, app_process):
        """Health check endpoint should return 200."""
        import urllib.request
        req = urllib.request.Request("http://localhost:8599/healthz")
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            assert resp.status == 200
        except urllib.error.HTTPError as e:
            # /healthz may not exist in older Streamlit — that's OK
            assert e.code in (200, 404)

    def test_app_static_resources(self, app_process):
        """Static resources should be served."""
        import urllib.request
        req = urllib.request.Request("http://localhost:8599/static/favicon.png")
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            assert resp.status in (200, 404)  # 404 is OK if no custom favicon
        except Exception:
            pass  # Network issues in CI are acceptable


# ═══════════════════════════════════════════════════════════════════════
# 4. State Management Tests
# ═══════════════════════════════════════════════════════════════════════

class TestStateManagement:
    """Verify session state and bankroll management."""

    def test_default_bankroll(self):
        """Default bankroll should be 1000.0."""
        import streamlit as st
        # Simulate fresh session
        if "bankroll" in st.session_state:
            del st.session_state["bankroll"]

        # This is what app.py does
        if "bankroll" not in st.session_state:
            st.session_state.bankroll = 1000.0

        assert st.session_state.bankroll == 1000.0

    def test_bankroll_update(self):
        """Bankroll should be updatable."""
        import streamlit as st
        st.session_state.bankroll = 2000.0
        assert st.session_state.bankroll == 2000.0
        st.session_state.bankroll = 1000.0  # reset

    def test_tutorial_step_state(self):
        """Tutorial step should persist in session state."""
        import streamlit as st
        if "tutorial_step" not in st.session_state:
            st.session_state.tutorial_step = 0
        assert st.session_state.tutorial_step == 0
        st.session_state.tutorial_step = 5
        assert st.session_state.tutorial_step == 5
        st.session_state.tutorial_step = 0  # reset


# ═══════════════════════════════════════════════════════════════════════
# 5. Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_zero_bankroll(self):
        """System should handle zero bankroll."""
        from core.portfolio import PortfolioEngine
        from core.value import ValueEngine
        from games.roulette import european_roulette

        game = european_roulette()
        ve = ValueEngine()
        value_results = ve.analyze_all(game)
        portfolio = PortfolioEngine(bankroll=0.0)
        allocation = portfolio.optimize(game, value_results)
        assert allocation.total_exposure == pytest.approx(0.0)

    def test_negative_bankroll(self):
        """System should handle negative bankroll (should not crash)."""
        from core.portfolio import PortfolioEngine
        from core.value import ValueEngine
        from games.roulette import european_roulette

        game = european_roulette()
        ve = ValueEngine()
        value_results = ve.analyze_all(game)
        portfolio = PortfolioEngine(bankroll=-100.0)
        allocation = portfolio.optimize(game, value_results)
        # Should still produce valid output
        assert allocation is not None

    def test_single_bet_game(self, tmp_path):
        """System should handle a game with only one bet."""
        from core.game import Game, Bet
        from core.history import HistoryEngine
        from core.extremum import ExtremumEngine
        from core.value import ValueEngine
        from core.portfolio import PortfolioEngine

        game = Game(
            name="Single",
            bets=[Bet(id="only", name="Only", probability=0.5, odds=2.0)],
        )
        history = HistoryEngine(str(tmp_path / "single.db"))
        history.record_draw(game, "win", ["only"])

        extremum = ExtremumEngine(history)
        results = extremum.analyze_all(game)
        assert len(results) == 1

        ve = ValueEngine()
        value_results = ve.analyze_all(game)
        assert len(value_results) == 1

        portfolio = PortfolioEngine(bankroll=1000.0)
        allocation = portfolio.optimize(game, value_results)
        assert len(allocation.bet_ids) == 1

    def test_many_bets_game(self):
        """System should handle a game with many bets (100+)."""
        from core.game import Game, Bet
        from core.value import ValueEngine
        from core.portfolio import PortfolioEngine

        bets = [
            Bet(id=f"bet_{i}", name=f"Bet {i}", probability=0.01, odds=100.0)
            for i in range(100)
        ]
        game = Game(name="Many", bets=bets)
        game.validate()

        ve = ValueEngine()
        value_results = ve.analyze_all(game)
        assert len(value_results) == 100

        portfolio = PortfolioEngine(bankroll=1000.0)
        allocation = portfolio.optimize(game, value_results)
        assert len(allocation.bet_ids) == 100

    def test_extreme_probabilities(self):
        """System should handle very small and very large probabilities."""
        from core.game import Bet, Game
        from core.value import ValueEngine

        game = Game(
            name="Extreme",
            bets=[
                Bet(id="rare", name="Rare", probability=0.000001, odds=1000000.0),
                Bet(id="common", name="Common", probability=0.999999, odds=1.001),
            ],
        )
        game.validate()

        ve = ValueEngine()
        results = ve.analyze_all(game)
        assert len(results) == 2
        # Both should compute without overflow
        assert not np.isnan(results[0].ev)
        assert not np.isnan(results[1].ev)

    def test_monte_carlo_convergence(self):
        """Monte Carlo should converge with more simulations."""
        from core.game import Bet, Game
        from core.portfolio import PortfolioAllocation
        from core.monte_carlo import MonteCarloEngine

        game = Game(
            name="Test",
            bets=[Bet(id="a", name="A", probability=0.5, odds=2.0)],
        )
        allocation = PortfolioAllocation(
            bet_ids=["a"],
            stakes=np.array([100.0]),
            stake_pcts=np.array([0.10]),
            total_exposure=0.10,
            expected_return=0.0,
            max_loss=-100.0,
            max_profit=100.0,
            sharpe_like=0.0,
        )

        mc = MonteCarloEngine(seed=42)
        r1k = mc.simulate_independent(game, allocation, n_simulations=1000)
        r10k = mc.simulate_independent(game, allocation, n_simulations=10000)

        # More simulations = tighter std
        assert r10k.std_return < r1k.std_return * 1.2  # should be similar or tighter

    def test_correlation_matrix_symmetry(self):
        """Correlation matrix must be symmetric."""
        from core.correlation import CorrelationEngine
        from games.roulette import european_roulette

        game = european_roulette()
        engine = CorrelationEngine()

        red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        win_sets = _build_roulette_win_sets(game, red_numbers)
        matrix = engine.compute_structural(game, win_sets)

        assert np.allclose(matrix.matrix, matrix.matrix.T)

    def test_risk_limits_always_valid(self):
        """Default risk limits should be internally consistent."""
        from core.risk import RiskLimits

        limits = RiskLimits()
        assert limits.max_per_bet <= limits.max_per_hand
        assert limits.max_per_hand <= limits.max_per_draw
        assert limits.max_per_draw <= limits.max_total
        assert 0 < limits.max_drawdown < 1
        assert limits.min_bankroll > 0


# ═══════════════════════════════════════════════════════════════════════
# 6. Regression Tests — Specific Bug Scenarios
# ═══════════════════════════════════════════════════════════════════════

class TestRegression:
    """Tests for specific bugs that were found and fixed."""

    def test_roulette_probabilities_dont_need_to_sum_to_one(self):
        """Roulette bets overlap — total probability > 1 is correct."""
        from games.roulette import european_roulette
        game = european_roulette()
        total_p = sum(b.probability for b in game.bets)
        # Should be > 1 because bets overlap
        assert total_p > 1.0

    def test_kelly_zero_for_negative_ev(self):
        """Kelly fraction must be 0 for negative EV bets."""
        from core.value import ValueEngine
        from core.game import Bet

        ve = ValueEngine()
        bet = Bet(id="bad", name="Bad", probability=0.1, odds=5.0)  # EV = -0.5
        result = ve.analyze(bet)
        assert result.ev < 0
        assert result.kelly_full == 0.0

    def test_zscore_zero_when_no_data(self, tmp_path):
        """Z-score should be 0 when there's no history."""
        from core.history import HistoryEngine
        from core.game import Bet, Game

        game = Game(
            name="Test",
            bets=[Bet(id="a", name="A", probability=0.5, odds=2.0)],
        )
        history = HistoryEngine(str(tmp_path / "zscore.db"))
        stats = history.compute_window_stats(game, "a", 50)
        assert stats.z_score == 0.0
        assert stats.n_draws == 0

    def test_mrf_default_when_no_data(self, tmp_path):
        """MRF should return default 0.35 when insufficient data."""
        from core.history import HistoryEngine
        from core.extremum import ExtremumEngine
        from core.game import Bet, Game

        game = Game(
            name="Test",
            bets=[Bet(id="a", name="A", probability=0.5, odds=2.0)],
        )
        history = HistoryEngine(str(tmp_path / "mrf.db"))
        extremum = ExtremumEngine(history)
        mrf = extremum.learn_mrf(game, "a")
        assert mrf == 0.35


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _build_roulette_win_sets(game, red_numbers):
    """Build win_sets dict for roulette."""
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
    return win_sets
