"""Tests for core.value — Value Engine (EV, Kelly)."""

import pytest
from core.game import Bet, Game
from core.value import ValueEngine, ValueResult


@pytest.fixture
def engine():
    return ValueEngine(max_stake_pct=0.10)


class TestValueEngine:
    def test_analyze_fair_coin(self, engine):
        bet = Bet(id="heads", name="Heads", probability=0.5, odds=2.0)
        result = engine.analyze(bet)
        assert result.ev == pytest.approx(0.0)
        assert result.kelly_full == pytest.approx(0.0)
        assert not result.has_value

    def test_analyze_positive_ev(self, engine):
        """55% win probability at odds 2.0 gives positive EV."""
        bet = Bet(id="biased", name="Biased", probability=0.55, odds=2.0)
        result = engine.analyze(bet)
        assert result.ev == pytest.approx(0.10)
        assert result.kelly_full == pytest.approx(0.10)
        assert result.has_value

    def test_analyze_negative_ev(self, engine):
        """Roulette number: negative EV."""
        bet = Bet(id="num_0", name="0", probability=1 / 37, odds=36.0)
        result = engine.analyze(bet)
        assert result.ev < 0
        assert result.kelly_full == 0.0  # Kelly is 0 for negative EV
        assert not result.has_value

    def test_kelly_fractions(self, engine):
        bet = Bet(id="good", name="Good", probability=0.6, odds=2.0)
        result = engine.analyze(bet)
        assert result.kelly_full > 0
        assert result.kelly_half == pytest.approx(result.kelly_full / 2)
        assert result.kelly_quarter == pytest.approx(result.kelly_full / 4)

    def test_recommended_stake_capped(self, engine):
        """1/4 Kelly should be capped at max_stake_pct."""
        bet = Bet(id="very_good", name="Very Good", probability=0.9, odds=2.0)
        result = engine.analyze(bet)
        # Kelly for p=0.9, odds=2: (0.9*2-1)/(2-1) = 0.8
        # 1/4 Kelly = 0.2, capped at 0.10
        assert result.recommended_stake_pct == 0.10

    def test_risk_score(self, engine):
        safe = Bet(id="safe", name="Safe", probability=0.9, odds=1.1)
        risky = Bet(id="risky", name="Risky", probability=0.01, odds=100.0)
        safe_result = engine.analyze(safe)
        risky_result = engine.analyze(risky)
        assert risky_result.risk_score > safe_result.risk_score

    def test_analyze_all(self, engine):
        game = Game(
            name="Test",
            bets=[
                Bet(id="a", name="A", probability=0.5, odds=2.0),
                Bet(id="b", name="B", probability=0.5, odds=2.0),
            ],
        )
        results = engine.analyze_all(game)
        assert len(results) == 2
        assert all(r.ev == pytest.approx(0.0) for r in results)
