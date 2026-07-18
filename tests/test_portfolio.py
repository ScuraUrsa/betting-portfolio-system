"""Tests for core.portfolio — Portfolio Engine."""

import pytest
import numpy as np
from core.game import Bet, Game
from core.value import ValueEngine, ValueResult
from core.portfolio import PortfolioEngine, PortfolioAllocation


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
def value_engine():
    return ValueEngine()


@pytest.fixture
def portfolio_engine():
    return PortfolioEngine(bankroll=1000.0)


class TestPortfolioEngine:
    def test_optimize_fair_coin(self, portfolio_engine, coin_game, value_engine):
        """For a fair coin, Kelly is 0, so optimal stakes should be 0."""
        value_results = value_engine.analyze_all(coin_game)
        allocation = portfolio_engine.optimize(coin_game, value_results)
        # All stakes should be 0 (no edge)
        assert np.allclose(allocation.stake_pcts, 0.0, atol=1e-6)
        assert allocation.total_exposure == pytest.approx(0.0)

    def test_optimize_positive_ev(self, portfolio_engine, value_engine):
        """With positive EV, should allocate some capital."""
        game = Game(
            name="Positive EV",
            bets=[
                Bet(id="good", name="Good", probability=0.55, odds=2.0),
            ],
        )
        value_results = value_engine.analyze_all(game)
        allocation = portfolio_engine.optimize(game, value_results)
        assert allocation.stake_pcts[0] > 0
        assert allocation.expected_return > 0

    def test_optimize_respects_max_per_bet(self, portfolio_engine, value_engine):
        """Should not exceed max_per_bet limit."""
        game = Game(
            name="Very Good",
            bets=[
                Bet(id="vg", name="Very Good", probability=0.9, odds=2.0),
            ],
        )
        value_results = value_engine.analyze_all(game)
        allocation = portfolio_engine.optimize(game, value_results)
        assert allocation.stake_pcts[0] <= portfolio_engine.max_per_bet

    def test_optimize_respects_max_total(self, portfolio_engine, value_engine):
        """Total exposure should not exceed max_total."""
        game = Game(
            name="Many Good",
            bets=[
                Bet(id=f"good_{i}", name=f"Good {i}", probability=0.55, odds=2.0)
                for i in range(10)
            ],
        )
        value_results = value_engine.analyze_all(game)
        allocation = portfolio_engine.optimize(game, value_results)
        assert allocation.total_exposure <= portfolio_engine.max_total + 1e-6

    def test_analyze_scenarios(self, portfolio_engine, coin_game, value_engine):
        """Scenario analysis for a simple game."""
        value_results = value_engine.analyze_all(coin_game)
        allocation = portfolio_engine.optimize(coin_game, value_results)

        win_sets = {"heads": {"H"}, "tails": {"T"}}
        outcomes = ["H", "T"]
        probs = {"H": 0.5, "T": 0.5}

        scenarios = portfolio_engine.analyze_scenarios(
            coin_game, allocation, win_sets, outcomes, probs
        )
        assert len(scenarios) == 2

    def test_allocation_metrics(self, portfolio_engine, value_engine):
        game = Game(
            name="Test",
            bets=[
                Bet(id="a", name="A", probability=0.6, odds=2.0),
            ],
        )
        value_results = value_engine.analyze_all(game)
        allocation = portfolio_engine.optimize(game, value_results)
        assert allocation.max_loss <= 0  # worst case is losing all stakes
        assert allocation.max_profit >= 0  # best case is winning
