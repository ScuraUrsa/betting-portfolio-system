"""Tests for core.history — HistoryEngine with SQLite storage."""

import pytest
from core.game import Bet, Game
from core.history import HistoryEngine, DrawRecord, WindowStats, DEFAULT_WINDOWS


@pytest.fixture
def coin_game():
    return Game(
        name="Fair Coin",
        bets=[
            Bet(id="heads", name="Heads", probability=0.5, odds=2.0),
            Bet(id="tails", name="Tails", probability=0.5, odds=2.0),
        ],
    )


@pytest.fixture
def engine(tmp_path):
    db = tmp_path / "test_history.db"
    return HistoryEngine(str(db))


class TestHistoryEngine:
    def test_record_and_retrieve(self, engine, coin_game):
        draw_id = engine.record_draw(coin_game, "heads", ["heads"])
        assert draw_id == 1

        draws = engine.get_draws("Fair Coin")
        assert len(draws) == 1
        assert draws[0].raw_outcome == "heads"
        assert draws[0].won_bet_ids == ["heads"]

    def test_multiple_draws(self, engine, coin_game):
        for i in range(10):
            outcome = "heads" if i % 2 == 0 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        assert engine.count_draws("Fair Coin") == 10

    def test_count_draws_empty(self, engine):
        assert engine.count_draws("Nonexistent") == 0

    def test_get_draws_limit(self, engine, coin_game):
        for i in range(100):
            outcome = "heads" if i % 2 == 0 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        draws = engine.get_draws("Fair Coin", limit=10)
        assert len(draws) == 10

    def test_window_stats_empty(self, engine, coin_game):
        stats = engine.compute_window_stats(coin_game, "heads", 50)
        assert stats.n_draws == 0
        assert stats.z_score == 0.0

    def test_window_stats_fair_coin(self, engine, coin_game):
        """With exactly 50% heads over many draws, Z should be near 0."""
        for i in range(1000):
            outcome = "heads" if i % 2 == 0 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        stats = engine.compute_window_stats(coin_game, "heads", 1000)
        assert stats.n_draws == 1000
        assert stats.hits == 500
        assert stats.expected == pytest.approx(500.0)
        # Z should be near 0 for a fair distribution
        assert abs(stats.z_score) < 0.5

    def test_window_stats_biased(self, engine, coin_game):
        """If heads hits 60% over 100 draws, Z should be positive."""
        for i in range(100):
            outcome = "heads" if i < 60 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        stats = engine.compute_window_stats(coin_game, "heads", 100)
        assert stats.hits == 60
        assert stats.expected == pytest.approx(50.0)
        assert stats.z_score > 1.5  # 60 vs 50 expected, std=5

    def test_compute_all_windows(self, engine, coin_game):
        # Heads in recent draws (get_draws returns newest first)
        for i in range(200):
            outcome = "heads" if i >= 80 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        stats_list = engine.compute_all_windows(coin_game, "heads")
        assert len(stats_list) == len(DEFAULT_WINDOWS)
        # All windows should show positive Z (heads overrepresented)
        for ws in stats_list:
            if ws.n_draws > 0:
                assert ws.z_score > 0

    def test_clear_history(self, engine, coin_game):
        engine.record_draw(coin_game, "heads", ["heads"])
        assert engine.count_draws("Fair Coin") == 1
        engine.clear_history("Fair Coin")
        assert engine.count_draws("Fair Coin") == 0
