"""Tests for core.extremum — Extremum Index and Mean Reversion Factor."""

import pytest
from core.game import Bet, Game
from core.history import HistoryEngine
from core.extremum import ExtremumEngine, ExtremumResult


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
    db = tmp_path / "test_extremum.db"
    return HistoryEngine(str(db))


class TestExtremumEngine:
    def test_analyze_empty_history(self, engine, coin_game):
        ee = ExtremumEngine(engine)
        result = ee.analyze(coin_game, "heads")
        assert result.bet_id == "heads"
        assert result.extremum_index == 0.0
        assert result.signal_level == "none"

    def test_analyze_with_data(self, engine, coin_game):
        """60% heads over 200 draws should produce a positive EI.
        
        Heads are in the RECENT draws (get_draws returns newest first).
        """
        # First 80 draws: tails, last 120 draws: heads
        for i in range(200):
            outcome = "heads" if i >= 80 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        ee = ExtremumEngine(engine)
        result = ee.analyze(coin_game, "heads")
        assert result.extremum_index > 0
        assert result.direction == "over"
        assert result.signal_level != "none"

    def test_analyze_all(self, engine, coin_game):
        # Heads in recent draws (get_draws returns newest first)
        for i in range(200):
            outcome = "heads" if i >= 80 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        ee = ExtremumEngine(engine)
        results = ee.analyze_all(coin_game)
        assert len(results) == 2
        heads_result = next(r for r in results if r.bet_id == "heads")
        tails_result = next(r for r in results if r.bet_id == "tails")
        assert heads_result.extremum_index > 0
        assert tails_result.extremum_index < 0

    def test_signal_classification(self):
        assert ExtremumEngine._classify_signal(0.5) == "none"
        assert ExtremumEngine._classify_signal(1.5) == "observation"
        assert ExtremumEngine._classify_signal(2.2) == "entry_small"
        assert ExtremumEngine._classify_signal(2.7) == "medium"
        assert ExtremumEngine._classify_signal(3.5) == "maximum"
        assert ExtremumEngine._classify_signal(5.0) == "maximum"

    def test_max_z_score(self, engine, coin_game):
        for i in range(200):
            outcome = "heads" if i >= 80 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        ee = ExtremumEngine(engine)
        result = ee.analyze(coin_game, "heads")
        assert result.max_z_score > 0

    def test_direction(self, engine, coin_game):
        for i in range(200):
            outcome = "heads" if i >= 80 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        ee = ExtremumEngine(engine)
        heads = ee.analyze(coin_game, "heads")
        tails = ee.analyze(coin_game, "tails")
        assert heads.direction == "over"
        assert tails.direction == "under"

    def test_learn_mrf_not_enough_data(self, engine, coin_game):
        ee = ExtremumEngine(engine)
        mrf = ee.learn_mrf(coin_game, "heads")
        assert mrf == 0.35  # default

    def test_learn_mrf_with_data(self, engine, coin_game):
        """Generate data with mean-reverting pattern and learn MRF."""
        import random
        random.seed(42)

        # Generate 500 draws with a mean-reverting pattern:
        # after a streak of heads, increase probability of tails
        for i in range(500):
            # Simple mean-reverting: alternate more than pure random
            if i > 0 and i % 10 == 0:
                # Every 10th draw, force the opposite of recent trend
                recent = engine.get_draws("Fair Coin", limit=5)
                heads_count = sum(1 for d in recent if "heads" in d.won_bet_ids)
                outcome = "tails" if heads_count >= 3 else "heads"
            else:
                outcome = "heads" if random.random() < 0.5 else "tails"
            engine.record_draw(coin_game, outcome, [outcome])

        ee = ExtremumEngine(engine)
        mrf = ee.learn_mrf(coin_game, "heads", lookback=500)
        # MRF should be learnable (between 0 and 1)
        assert 0.0 <= mrf <= 1.0
