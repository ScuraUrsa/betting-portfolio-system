"""Tests for core.correlation — Correlation Engine."""

import pytest
import numpy as np
from core.game import Bet, Game
from core.correlation import CorrelationEngine, CorrelationMatrix


@pytest.fixture
def engine():
    return CorrelationEngine()


@pytest.fixture
def roulette_game():
    """Simplified roulette with just a few bets for testing."""
    return Game(
        name="Mini Roulette",
        bets=[
            Bet(id="num_1", name="1", probability=1 / 37, odds=36.0),
            Bet(id="num_2", name="2", probability=1 / 37, odds=36.0),
            Bet(id="red", name="Red", probability=18 / 37, odds=2.0),
            Bet(id="black", name="Black", probability=18 / 37, odds=2.0),
        ],
    )


class TestCorrelationEngine:
    def test_structural_identity(self, engine, roulette_game):
        win_sets = {
            "num_1": {"1"},
            "num_2": {"2"},
            "red": {"1", "3", "5", "7", "9", "12", "14", "16", "18", "19", "21", "23", "25", "27", "30", "32", "34", "36"},
            "black": {"2", "4", "6", "8", "10", "11", "13", "15", "17", "20", "22", "24", "26", "28", "29", "31", "33", "35"},
        }
        matrix = engine.compute_structural(roulette_game, win_sets)
        # Diagonal should be 1.0
        for i, bid in enumerate(matrix.bet_ids):
            assert matrix.matrix[i, i] == pytest.approx(1.0)

    def test_structural_correlation(self, engine, roulette_game):
        win_sets = {
            "num_1": {"1"},
            "num_2": {"2"},
            "red": {"1", "3", "5", "7", "9", "12", "14", "16", "18", "19", "21", "23", "25", "27", "30", "32", "34", "36"},
            "black": {"2", "4", "6", "8", "10", "11", "13", "15", "17", "20", "22", "24", "26", "28", "29", "31", "33", "35"},
        }
        matrix = engine.compute_structural(roulette_game, win_sets)

        # num_1 and red are correlated (1 is red)
        corr = matrix.get_correlation("num_1", "red")
        assert corr > 0

        # num_1 and num_2 are uncorrelated (disjoint)
        corr = matrix.get_correlation("num_1", "num_2")
        assert corr == pytest.approx(0.0)

        # red and black are anti-correlated (disjoint)
        corr = matrix.get_correlation("red", "black")
        assert corr == pytest.approx(0.0)

    def test_get_correlated_bets(self, engine, roulette_game):
        win_sets = {
            "num_1": {"1"},
            "num_2": {"2"},
            "red": {"1", "3", "5", "7", "9", "12", "14", "16", "18", "19", "21", "23", "25", "27", "30", "32", "34", "36"},
            "black": {"2", "4", "6", "8", "10", "11", "13", "15", "17", "20", "22", "24", "26", "28", "29", "31", "33", "35"},
        }
        matrix = engine.compute_structural(roulette_game, win_sets)
        correlated = matrix.get_correlated_bets("num_1", threshold=0.1)
        # num_1 should be correlated with red
        assert any(bid == "red" for bid, _ in correlated)

    def test_empirical_empty(self, engine, roulette_game):
        """Empirical correlation with no data should return identity matrix."""
        from core.history import HistoryEngine
        import tempfile, os
        db = os.path.join(tempfile.mkdtemp(), "test.db")
        history = HistoryEngine(db)
        matrix = engine.compute_empirical(roulette_game, history)
        assert matrix.matrix.shape == (4, 4)
        # Should be identity (no data)
        assert np.allclose(matrix.matrix, np.eye(4))
