"""Value Engine — Expected Value, Kelly Criterion, and bet scoring.

Computes the fundamental value metrics for each bet:
- EV (Expected Value): p * odds - 1
- Kelly fraction: (p * odds - 1) / (odds - 1)
- Fractional Kelly: 1/4, 1/2 Kelly
- Risk Score, Exposure Score
"""

from dataclasses import dataclass
from typing import Optional

from core.game import Bet, Game
from core.extremum import ExtremumResult


@dataclass
class ValueResult:
    """Value analysis for a single bet."""

    bet_id: str
    bet_name: str
    probability: float
    odds: float
    ev: float  # Expected Value
    kelly_full: float  # Full Kelly fraction
    kelly_half: float  # 1/2 Kelly
    kelly_quarter: float  # 1/4 Kelly
    risk_score: float  # 0-1, higher = riskier
    exposure_score: float  # 0-1, how much of bankroll to allocate

    @property
    def has_value(self) -> bool:
        """True if EV > 0 (positive expected value)."""
        return self.ev > 0

    @property
    def recommended_stake_pct(self) -> float:
        """Recommended stake as percentage of bankroll (1/4 Kelly, capped at 10%)."""
        return min(self.kelly_quarter, 0.10)


class ValueEngine:
    """Computes value metrics for bets, optionally incorporating extremum signals."""

    def __init__(self, max_stake_pct: float = 0.10):
        self.max_stake_pct = max_stake_pct

    def analyze(
        self,
        bet: Bet,
        extremum: Optional[ExtremumResult] = None,
    ) -> ValueResult:
        """Compute value metrics for a single bet.

        Args:
            bet: The bet to analyze
            extremum: Optional extremum analysis for signal-adjusted scoring
        """
        p = bet.probability
        odds = bet.odds

        # Expected Value
        ev = p * odds - 1.0

        # Kelly Criterion
        if odds > 1.0:
            kelly_full = max(0.0, (p * odds - 1.0) / (odds - 1.0))
        else:
            kelly_full = 0.0

        kelly_half = kelly_full / 2.0
        kelly_quarter = kelly_full / 4.0

        # Risk Score: higher probability = lower risk, higher odds = higher risk
        risk_score = (1.0 - p) * min(odds / 36.0, 1.0)

        # Exposure Score: adjusted by extremum signal if available
        base_exposure = min(kelly_quarter, self.max_stake_pct)
        if extremum is not None and extremum.signal_level != "none":
            # Amplify exposure based on signal strength
            signal_mult = {
                "observation": 1.0,
                "entry_small": 1.5,
                "medium": 2.0,
                "maximum": 2.5,
            }.get(extremum.signal_level, 1.0)
            # If extremum is "under" (below expected), bet on regression to mean
            if extremum.direction == "under":
                base_exposure *= signal_mult
            elif extremum.direction == "over":
                # Over expected — might regress down, reduce exposure
                base_exposure *= 0.5

        exposure_score = min(base_exposure, self.max_stake_pct)

        return ValueResult(
            bet_id=bet.id,
            bet_name=bet.name,
            probability=p,
            odds=odds,
            ev=ev,
            kelly_full=kelly_full,
            kelly_half=kelly_half,
            kelly_quarter=kelly_quarter,
            risk_score=risk_score,
            exposure_score=exposure_score,
        )

    def analyze_all(
        self,
        game: Game,
        extremum_results: Optional[dict[str, ExtremumResult]] = None,
    ) -> list[ValueResult]:
        """Analyze all bets in a game."""
        results = []
        for bet in game.bets:
            ext = None
            if extremum_results:
                ext = extremum_results.get(bet.id)
            results.append(self.analyze(bet, ext))
        return results
