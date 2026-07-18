"""Tests for core.risk — Risk Management."""

import pytest
import numpy as np
from core.game import Bet, Game
from core.portfolio import PortfolioAllocation, ScenarioResult
from core.risk import RiskManager, RiskLimits, LossDistribution, RiskReport


@pytest.fixture
def risk_manager():
    return RiskManager()


@pytest.fixture
def sample_allocation():
    return PortfolioAllocation(
        bet_ids=["a", "b"],
        stakes=np.array([50.0, 30.0]),
        stake_pcts=np.array([0.05, 0.03]),
        total_exposure=0.08,
        expected_return=10.0,
        max_loss=-80.0,
        max_profit=150.0,
        sharpe_like=0.125,
    )


class TestRiskManager:
    def test_validate_acceptable(self, risk_manager, sample_allocation):
        violations = risk_manager.validate(sample_allocation, bankroll=1000.0)
        assert len(violations) == 0

    def test_validate_exceeds_per_bet(self, risk_manager):
        allocation = PortfolioAllocation(
            bet_ids=["big"],
            stakes=np.array([200.0]),
            stake_pcts=np.array([0.20]),
            total_exposure=0.20,
            expected_return=0.0,
            max_loss=-200.0,
            max_profit=200.0,
            sharpe_like=0.0,
        )
        violations = risk_manager.validate(allocation, bankroll=1000.0)
        assert len(violations) > 0
        assert any("exceeds max" in v for v in violations)

    def test_validate_exceeds_total(self, risk_manager):
        allocation = PortfolioAllocation(
            bet_ids=["a", "b", "c", "d", "e", "f"],
            stakes=np.array([100.0] * 6),
            stake_pcts=np.array([0.10] * 6),
            total_exposure=0.60,
            expected_return=0.0,
            max_loss=-600.0,
            max_profit=600.0,
            sharpe_like=0.0,
        )
        violations = risk_manager.validate(allocation, bankroll=1000.0)
        assert any("Total exposure" in v for v in violations)

    def test_validate_low_bankroll(self, risk_manager, sample_allocation):
        violations = risk_manager.validate(sample_allocation, bankroll=50.0)
        assert any("below minimum" in v for v in violations)

    def test_compute_loss_distribution(self, risk_manager):
        scenarios = [
            ScenarioResult(0, ["a"], 350.0, 0.3),
            ScenarioResult(1, ["b"], 280.0, 0.3),
            ScenarioResult(2, [], -80.0, 0.4),
        ]
        dist = risk_manager.compute_loss_distribution(scenarios)
        assert dist.best_case == 350.0
        assert dist.worst_case == -80.0
        assert dist.expected_case > 0  # positive expected
        assert dist.profit_probability > 0.5
        assert len(dist.loss_scenarios) == 1
        assert len(dist.profit_scenarios) == 2

    def test_compute_loss_distribution_empty(self, risk_manager):
        dist = risk_manager.compute_loss_distribution([])
        assert dist.expected_case == 0.0
        assert dist.profit_probability == 0.0

    def test_assess_acceptable(self, risk_manager, sample_allocation):
        scenarios = [
            ScenarioResult(0, ["a"], 100.0, 0.5),
            ScenarioResult(1, [], -50.0, 0.5),
        ]
        report = risk_manager.assess(sample_allocation, bankroll=1000.0, scenarios=scenarios)
        assert report.is_acceptable
        assert report.loss_distribution is not None

    def test_assess_unacceptable(self, risk_manager):
        allocation = PortfolioAllocation(
            bet_ids=["big"],
            stakes=np.array([200.0]),
            stake_pcts=np.array([0.20]),
            total_exposure=0.20,
            expected_return=0.0,
            max_loss=-200.0,
            max_profit=200.0,
            sharpe_like=0.0,
        )
        report = risk_manager.assess(allocation, bankroll=1000.0)
        assert not report.is_acceptable

    def test_risk_limits_defaults(self):
        limits = RiskLimits()
        assert limits.max_per_bet == 0.10
        assert limits.max_per_hand == 0.20
        assert limits.max_per_draw == 0.30
        assert limits.max_total == 0.50
        assert limits.max_drawdown == 0.25
