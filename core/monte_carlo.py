"""Monte Carlo Engine — simulates thousands of possible outcomes.

Runs simulations to estimate:
- Expected Return
- Max Drawdown
- Variance
- Profit Distribution
- Risk Score

Uses numpy for fast vectorized simulation.
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from core.game import Bet, Game
from core.portfolio import PortfolioAllocation


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""

    n_simulations: int
    expected_return: float  # mean profit
    expected_return_pct: float  # as % of bankroll
    std_return: float  # standard deviation of profit
    max_drawdown: float  # worst observed loss
    max_profit: float  # best observed profit
    var_95: float  # Value at Risk (95% confidence)
    var_99: float  # Value at Risk (99% confidence)
    cvar_95: float  # Conditional VaR (expected loss beyond VaR)
    profit_distribution: np.ndarray  # all simulated profits
    risk_score: float  # 0-1, higher = riskier
    ruin_probability: float  # P(bankroll < 0 after simulation)


class MonteCarloEngine:
    """Runs Monte Carlo simulations for a portfolio of bets.

    Supports:
    - Independent bets (each bet resolved independently)
    - Correlated bets (using a correlation matrix)
    - Game-specific outcome simulation (e.g., roulette spin)
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)

    def simulate_independent(
        self,
        game: Game,
        allocation: PortfolioAllocation,
        n_simulations: int = 10000,
    ) -> MonteCarloResult:
        """Simulate each bet independently (bets resolved separately).

        Each bet wins with probability p, independently of others.
        This is a simplification — in reality, roulette bets are correlated
        (they all depend on the same spin).
        """
        n_bets = len(allocation.bet_ids)
        stakes = allocation.stakes

        # Generate random outcomes: shape (n_simulations, n_bets)
        probs = np.array([game.get_bet(bid).probability for bid in allocation.bet_ids])
        odds = np.array([game.get_bet(bid).odds for bid in allocation.bet_ids])

        # Each bet wins independently
        wins = self.rng.random((n_simulations, n_bets)) < probs

        # Profit per simulation: sum over bets of (win ? stake*(odds-1) : -stake)
        payouts = np.where(wins, stakes * (odds - 1), -stakes)
        profits = payouts.sum(axis=1)

        return self._compute_metrics(profits, n_simulations)

    def simulate_game_outcomes(
        self,
        game: Game,
        allocation: PortfolioAllocation,
        outcome_probabilities: dict[str, float],
        win_sets: dict[str, set[str]],
        n_simulations: int = 10000,
    ) -> MonteCarloResult:
        """Simulate actual game outcomes (e.g., roulette spins).

        Each simulation picks one raw outcome, then determines which bets win.
        This correctly captures the correlation structure of the game.
        """
        outcomes = list(outcome_probabilities.keys())
        probs = np.array([outcome_probabilities[o] for o in outcomes])

        # Precompute which bets win for each outcome
        outcome_wins = {}
        for outcome in outcomes:
            outcome_wins[outcome] = [
                bid for bid, ws in win_sets.items() if outcome in ws
            ]

        # Sample outcomes
        sampled = self.rng.choice(len(outcomes), size=n_simulations, p=probs)

        # Compute profit for each simulation
        profits = np.zeros(n_simulations)
        for i, outcome_idx in enumerate(sampled):
            outcome = outcomes[outcome_idx]
            winning = outcome_wins[outcome]
            profit = 0.0
            for j, bid in enumerate(allocation.bet_ids):
                stake = allocation.stakes[j]
                if bid in winning:
                    odds = game.get_bet(bid).odds
                    profit += stake * (odds - 1)
                else:
                    profit -= stake
            profits[i] = profit

        return self._compute_metrics(profits, n_simulations)

    def _compute_metrics(
        self, profits: np.ndarray, n_simulations: int
    ) -> MonteCarloResult:
        """Compute standard metrics from profit array."""
        expected_return = float(np.mean(profits))
        std_return = float(np.std(profits))
        max_drawdown = float(np.min(profits))
        max_profit = float(np.max(profits))

        # Value at Risk
        var_95 = float(np.percentile(profits, 5))
        var_99 = float(np.percentile(profits, 1))

        # Conditional VaR: mean of losses below VaR
        cvar_95 = float(np.mean(profits[profits <= var_95])) if np.any(profits <= var_95) else var_95

        # Risk Score: normalized by standard deviation relative to mean
        if std_return > 0:
            risk_score = min(1.0, std_return / (abs(expected_return) + std_return + 1e-10))
        else:
            risk_score = 0.0

        # Ruin probability
        ruin_probability = float(np.mean(profits < 0))

        return MonteCarloResult(
            n_simulations=n_simulations,
            expected_return=expected_return,
            expected_return_pct=expected_return / np.sum(np.abs(profits)) * 100 if np.sum(np.abs(profits)) > 0 else 0.0,
            std_return=std_return,
            max_drawdown=max_drawdown,
            max_profit=max_profit,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            profit_distribution=profits,
            risk_score=risk_score,
            ruin_probability=ruin_probability,
        )
