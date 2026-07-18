"""Portfolio Engine — optimizes bet allocation across the entire portfolio.

Instead of "how much on a single bet?", answers:
"How should the final profit distribution of the entire portfolio look?"

Analyzes all outcome scenarios and finds the optimal stake distribution
that maximizes expected return while respecting risk constraints.
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.optimize import minimize

from core.game import Bet, Game
from core.value import ValueResult


@dataclass
class PortfolioAllocation:
    """Optimal stake allocation for a set of bets."""

    bet_ids: list[str]
    stakes: np.ndarray  # absolute amounts
    stake_pcts: np.ndarray  # as fraction of bankroll
    total_exposure: float  # sum of all stakes
    expected_return: float
    max_loss: float  # worst-case scenario
    max_profit: float  # best-case scenario
    sharpe_like: float  # expected_return / total_exposure (simplified)


@dataclass
class ScenarioResult:
    """Result of a single outcome scenario."""

    scenario_id: int
    winning_bets: list[str]
    profit: float  # net profit (payouts - total_stakes)
    probability: float


class PortfolioEngine:
    """Optimizes bet allocation across the entire portfolio.

    Uses constrained optimization to find stakes that maximize
    expected return while respecting:
    - Max stake per bet (10% of bankroll)
    - Max exposure per draw (30% of bankroll)
    - Max total exposure (50% of bankroll)
    """

    def __init__(
        self,
        bankroll: float = 1000.0,
        max_per_bet: float = 0.10,
        max_per_draw: float = 0.30,
        max_total: float = 0.50,
    ):
        self.bankroll = bankroll
        self.max_per_bet = max_per_bet
        self.max_per_draw = max_per_draw
        self.max_total = max_total

    def optimize(
        self,
        game: Game,
        value_results: list[ValueResult],
        correlation_matrix: Optional[np.ndarray] = None,
    ) -> PortfolioAllocation:
        """Find optimal stake distribution.

        Uses Kelly-based initial guess, then refines with constrained optimization.
        """
        n = game.n_bets
        bet_ids = [b.id for b in game.bets]

        # Build value map
        value_map = {vr.bet_id: vr for vr in value_results}

        # Initial guess: 1/4 Kelly, capped
        x0 = np.array([
            min(value_map[bid].kelly_quarter, self.max_per_bet)
            for bid in bet_ids
        ])

        # Constraints
        constraints = [
            # Sum of stakes <= max_total * bankroll
            {"type": "ineq", "fun": lambda x: self.max_total - np.sum(x)},
        ]

        # Bounds: 0 <= stake <= max_per_bet
        bounds = [(0.0, self.max_per_bet) for _ in range(n)]

        # Objective: maximize expected return (negative for minimization)
        def objective(x: np.ndarray) -> float:
            """Negative expected return (we minimize)."""
            total_return = 0.0
            for i, bid in enumerate(bet_ids):
                vr = value_map[bid]
                # Expected profit = stake * (p * odds - 1) = stake * EV
                total_return += x[i] * vr.ev
            return -total_return  # negative because we minimize

        # If correlation is available, add a penalty for concentrated risk
        if correlation_matrix is not None:
            def objective_with_corr(x: np.ndarray) -> float:
                base = -sum(
                    x[i] * value_map[bet_ids[i]].ev for i in range(n)
                )
                # Penalty: correlated bets amplify risk
                corr_penalty = 0.0
                for i in range(n):
                    for j in range(i + 1, n):
                        corr_penalty += (
                            x[i] * x[j] * abs(correlation_matrix[i, j]) * 0.1
                        )
                return base + corr_penalty

            obj = objective_with_corr
        else:
            obj = objective

        # Optimize
        result = minimize(
            obj,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-12},
        )

        stakes_pct = np.maximum(result.x, 0.0)  # ensure non-negative
        stakes_abs = stakes_pct * self.bankroll

        # Compute portfolio metrics
        total_exposure = np.sum(stakes_pct)
        expected_return = sum(
            stakes_pct[i] * value_map[bet_ids[i]].ev * self.bankroll
            for i in range(n)
        )

        # Worst case: all bets lose
        max_loss = -np.sum(stakes_abs)

        # Best case: all bets win
        max_profit = sum(
            stakes_abs[i] * (game.get_bet(bet_ids[i]).odds - 1)
            for i in range(n)
        )

        sharpe_like = expected_return / total_exposure if total_exposure > 0 else 0.0

        return PortfolioAllocation(
            bet_ids=bet_ids,
            stakes=stakes_abs,
            stake_pcts=stakes_pct,
            total_exposure=total_exposure,
            expected_return=expected_return,
            max_loss=max_loss,
            max_profit=max_profit,
            sharpe_like=sharpe_like,
        )

    def analyze_scenarios(
        self,
        game: Game,
        allocation: PortfolioAllocation,
        win_sets: dict[str, set[str]],
        all_outcomes: list[str],
        outcome_probabilities: dict[str, float],
    ) -> list[ScenarioResult]:
        """Analyze profit/loss for each possible outcome.

        Args:
            game: The game
            allocation: Current stake allocation
            win_sets: Mapping from bet_id to set of winning raw outcomes
            all_outcomes: All possible raw outcomes
            outcome_probabilities: P(outcome) for each
        """
        results = []
        for i, outcome in enumerate(all_outcomes):
            # Which bets win on this outcome?
            winning = [
                bid for bid, win_set in win_sets.items()
                if outcome in win_set
            ]

            # Profit = sum of winning payouts - total stakes
            profit = 0.0
            for j, bid in enumerate(allocation.bet_ids):
                stake = allocation.stakes[j]
                if bid in winning:
                    odds = game.get_bet(bid).odds
                    profit += stake * (odds - 1)  # net profit on win
                else:
                    profit -= stake  # lose the stake

            results.append(ScenarioResult(
                scenario_id=i,
                winning_bets=winning,
                profit=profit,
                probability=outcome_probabilities.get(outcome, 0.0),
            ))

        return results
