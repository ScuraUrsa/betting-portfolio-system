"""Tests for core.monte_carlo — Monte Carlo Engine."""

import pytest
import numpy as np
from core.game import Bet, Game
from core.value import ValueEngine
from core.portfolio import PortfolioEngine
from core.monte_carlo import MonteCarloEngine


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
def mc_engine():
    return MonteCarloEngine(seed=42)


class TestMonteCarloEngine:
    def test_simulate_independent_fair_coin(self, mc_engine, coin_game):
        """For a fair coin with 0 stakes, expected return should be 0."""
        from core.portfolio import PortfolioAllocation
        allocation = PortfolioAllocation(
            bet_ids=["heads", "tails"],
            stakes=np.array([0.0, 0.0]),
            stake_pcts=np.array([0.0, 0.0]),
            total_exposure=0.0,
            expected_return=0.0,
            max_loss=0.0,
            max_profit=0.0,
            sharpe_like=0.0,
        )
        result = mc_engine.simulate_independent(coin_game, allocation, n_simulations=1000)
        assert result.expected_return == pytest.approx(0.0, abs=1.0)
        assert result.n_simulations == 1000

    def test_simulate_independent_positive_ev(self, mc_engine):
        """With positive EV bets, expected return should be positive."""
        game = Game(
            name="Good",
            bets=[Bet(id="good", name="Good", probability=0.6, odds=2.0)],
        )
        from core.portfolio import PortfolioAllocation
        allocation = PortfolioAllocation(
            bet_ids=["good"],
            stakes=np.array([100.0]),
            stake_pcts=np.array([0.10]),
            total_exposure=0.10,
            expected_return=20.0,
            max_loss=-100.0,
            max_profit=100.0,
            sharpe_like=0.2,
        )
        result = mc_engine.simulate_independent(game, allocation, n_simulations=5000)
        # Expected profit = 100 * (0.6*2 - 1) = 20
        assert result.expected_return == pytest.approx(20.0, abs=5.0)

    def test_simulate_game_outcomes(self, mc_engine, coin_game):
        """Simulate actual coin flips."""
        from core.portfolio import PortfolioAllocation
        allocation = PortfolioAllocation(
            bet_ids=["heads", "tails"],
            stakes=np.array([0.0, 0.0]),
            stake_pcts=np.array([0.0, 0.0]),
            total_exposure=0.0,
            expected_return=0.0,
            max_loss=0.0,
            max_profit=0.0,
            sharpe_like=0.0,
        )
        win_sets = {"heads": {"H"}, "tails": {"T"}}
        probs = {"H": 0.5, "T": 0.5}
        result = mc_engine.simulate_game_outcomes(
            coin_game, allocation, probs, win_sets, n_simulations=1000
        )
        assert result.n_simulations == 1000
        assert result.expected_return == pytest.approx(0.0, abs=1.0)

    def test_metrics_computed(self, mc_engine, coin_game):
        """All metrics should be computed."""
        from core.portfolio import PortfolioAllocation
        allocation = PortfolioAllocation(
            bet_ids=["heads", "tails"],
            stakes=np.array([100.0, 100.0]),
            stake_pcts=np.array([0.10, 0.10]),
            total_exposure=0.20,
            expected_return=0.0,
            max_loss=-200.0,
            max_profit=200.0,
            sharpe_like=0.0,
        )
        result = mc_engine.simulate_independent(coin_game, allocation, n_simulations=1000)
        assert result.var_95 is not None
        assert result.var_99 is not None
        assert result.cvar_95 is not None
        assert 0.0 <= result.risk_score <= 1.0
        assert 0.0 <= result.ruin_probability <= 1.0
        assert len(result.profit_distribution) == 1000

    def test_reproducibility(self):
        """Same seed should produce same results."""
        engine1 = MonteCarloEngine(seed=42)
        engine2 = MonteCarloEngine(seed=42)
        game = Game(
            name="Test",
            bets=[Bet(id="a", name="A", probability=0.5, odds=2.0)],
        )
        from core.portfolio import PortfolioAllocation
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
        r1 = engine1.simulate_independent(game, allocation, n_simulations=1000)
        r2 = engine2.simulate_independent(game, allocation, n_simulations=1000)
        assert r1.expected_return == pytest.approx(r2.expected_return)
