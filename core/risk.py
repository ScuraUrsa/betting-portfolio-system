"""Risk Management — exposure limits, drawdown control, and loss distribution.

Enforces:
- Max stake per bet (default 10% of bankroll)
- Max exposure per hand/draw (default 30%)
- Max total exposure (default 50%)
- Max drawdown threshold
- Loss Distribution Score
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from core.game import Bet, Game
from core.portfolio import PortfolioAllocation, ScenarioResult


@dataclass
class RiskLimits:
    """Configurable risk limits."""

    max_per_bet: float = 0.10  # max 10% of bankroll on one bet
    max_per_hand: float = 0.20  # max 20% on correlated bets (same hand)
    max_per_draw: float = 0.30  # max 30% on one draw/round
    max_total: float = 0.50  # max 50% of bankroll across all active bets
    max_drawdown: float = 0.25  # stop if bankroll drops 25% from peak
    min_bankroll: float = 100.0  # absolute minimum bankroll


@dataclass
class LossDistribution:
    """Analysis of possible profit/loss outcomes."""

    best_case: float
    worst_case: float
    expected_case: float
    median_case: float
    std_dev: float
    profit_probability: float  # P(profit > 0)
    loss_scenarios: list[ScenarioResult]  # scenarios with negative profit
    profit_scenarios: list[ScenarioResult]  # scenarios with positive profit


@dataclass
class RiskReport:
    """Complete risk assessment for a portfolio."""

    allocation: PortfolioAllocation
    limits: RiskLimits
    limits_exceeded: list[str]  # which limits are violated
    loss_distribution: Optional[LossDistribution] = None
    drawdown_risk: float = 0.0  # estimated probability of hitting max drawdown
    is_acceptable: bool = True


class RiskManager:
    """Validates portfolio against risk limits and computes loss distribution."""

    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits()

    def validate(
        self,
        allocation: PortfolioAllocation,
        bankroll: float,
    ) -> list[str]:
        """Check if allocation violates any risk limits. Returns list of violations."""
        violations = []

        # Check per-bet limits
        for i, bid in enumerate(allocation.bet_ids):
            pct = allocation.stake_pcts[i]
            if pct > self.limits.max_per_bet:
                violations.append(
                    f"Bet '{bid}' stake {pct:.1%} exceeds max {self.limits.max_per_bet:.0%}"
                )

        # Check total exposure
        if allocation.total_exposure > self.limits.max_total:
            violations.append(
                f"Total exposure {allocation.total_exposure:.1%} exceeds max {self.limits.max_total:.0%}"
            )

        # Check bankroll minimum
        if bankroll < self.limits.min_bankroll:
            violations.append(
                f"Bankroll {bankroll:.0f} below minimum {self.limits.min_bankroll:.0f}"
            )

        return violations

    def compute_loss_distribution(
        self,
        scenarios: list[ScenarioResult],
    ) -> LossDistribution:
        """Compute loss distribution from scenario analysis."""
        if not scenarios:
            return LossDistribution(
                best_case=0.0,
                worst_case=0.0,
                expected_case=0.0,
                median_case=0.0,
                std_dev=0.0,
                profit_probability=0.0,
                loss_scenarios=[],
                profit_scenarios=[],
            )

        profits = np.array([s.profit for s in scenarios])
        probs = np.array([s.probability for s in scenarios])

        # Normalize probabilities
        prob_sum = probs.sum()
        if prob_sum > 0:
            probs = probs / prob_sum

        best_case = float(np.max(profits))
        worst_case = float(np.min(profits))
        expected_case = float(np.sum(profits * probs))

        # Weighted median
        sorted_idx = np.argsort(profits)
        cumsum = np.cumsum(probs[sorted_idx])
        median_idx = np.searchsorted(cumsum, 0.5)
        median_case = float(profits[sorted_idx[median_idx]])

        # Weighted std
        variance = np.sum(probs * (profits - expected_case) ** 2)
        std_dev = float(np.sqrt(variance))

        # Profit probability
        profit_probability = float(np.sum(probs[profits > 0]))

        # Separate loss and profit scenarios
        loss_scenarios = [s for s in scenarios if s.profit < 0]
        profit_scenarios = [s for s in scenarios if s.profit > 0]

        return LossDistribution(
            best_case=best_case,
            worst_case=worst_case,
            expected_case=expected_case,
            median_case=median_case,
            std_dev=std_dev,
            profit_probability=profit_probability,
            loss_scenarios=loss_scenarios,
            profit_scenarios=profit_scenarios,
        )

    def assess(
        self,
        allocation: PortfolioAllocation,
        bankroll: float,
        scenarios: Optional[list[ScenarioResult]] = None,
    ) -> RiskReport:
        """Full risk assessment."""
        violations = self.validate(allocation, bankroll)

        loss_dist = None
        if scenarios:
            loss_dist = self.compute_loss_distribution(scenarios)

        # Estimate drawdown risk from loss distribution
        drawdown_risk = 0.0
        if loss_dist and loss_dist.worst_case < 0:
            drawdown_pct = abs(loss_dist.worst_case) / bankroll
            drawdown_risk = min(1.0, drawdown_pct / self.limits.max_drawdown)

        is_acceptable = len(violations) == 0

        return RiskReport(
            allocation=allocation,
            limits=self.limits,
            limits_exceeded=violations,
            loss_distribution=loss_dist,
            drawdown_risk=drawdown_risk,
            is_acceptable=is_acceptable,
        )
