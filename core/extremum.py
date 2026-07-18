"""Extremum Engine — Z-score aggregation, Extremum Index, and Mean Reversion Factor.

Detects local deviations from expected values across multiple time windows.
Does NOT assume mean reversion exists — MRF is a learned parameter (0-1).
"""

from dataclasses import dataclass
from typing import Optional

from core.history import HistoryEngine, WindowStats, DEFAULT_WINDOWS


# Default weights for Extremum Index (must sum to 1.0)
DEFAULT_EI_WEIGHTS = {
    50: 0.10,
    100: 0.20,
    250: 0.30,
    500: 0.40,
}


@dataclass
class ExtremumResult:
    """Aggregated extremum analysis for a single bet."""

    bet_id: str
    window_stats: list[WindowStats]
    extremum_index: float  # weighted sum of Z-scores
    mrf: float  # Mean Reversion Factor (0-1)
    signal_level: str  # "none", "observation", "entry_small", "medium", "maximum"

    @property
    def max_z_score(self) -> float:
        if not self.window_stats:
            return 0.0
        return max(abs(ws.z_score) for ws in self.window_stats)

    @property
    def direction(self) -> str:
        """'over' if above expected, 'under' if below, 'neutral' if near zero."""
        if self.extremum_index > 0.5:
            return "over"
        elif self.extremum_index < -0.5:
            return "under"
        return "neutral"


class ExtremumEngine:
    """Computes Extremum Index and Mean Reversion Factor for bets."""

    def __init__(
        self,
        history: HistoryEngine,
        ei_weights: Optional[dict[int, float]] = None,
        mrf: float = 0.35,
    ):
        self.history = history
        self.ei_weights = ei_weights or DEFAULT_EI_WEIGHTS
        self.mrf = mrf  # learned parameter, default 0.35

    def analyze(
        self,
        game,
        bet_id: str,
        windows: Optional[list[int]] = None,
    ) -> ExtremumResult:
        """Full extremum analysis for a single bet."""
        if windows is None:
            windows = sorted(self.ei_weights.keys())

        stats = self.history.compute_all_windows(game, bet_id, windows)

        # Compute Extremum Index: weighted sum of Z-scores
        ei = 0.0
        for ws in stats:
            weight = self.ei_weights.get(ws.window_size, 0.0)
            ei += weight * ws.z_score

        signal = self._classify_signal(abs(ei))

        return ExtremumResult(
            bet_id=bet_id,
            window_stats=stats,
            extremum_index=ei,
            mrf=self.mrf,
            signal_level=signal,
        )

    def analyze_all(
        self,
        game,
        windows: Optional[list[int]] = None,
    ) -> list[ExtremumResult]:
        """Analyze all bets in a game."""
        return [self.analyze(game, b.id, windows) for b in game.bets]

    @staticmethod
    def _classify_signal(abs_ei: float) -> str:
        """Classify signal strength from Extremum Index absolute value."""
        if abs_ei < 1.0:
            return "none"
        elif abs_ei < 2.0:
            return "observation"
        elif abs_ei < 2.5:
            return "entry_small"
        elif abs_ei < 3.0:
            return "medium"
        elif abs_ei < 4.0:
            return "maximum"
        else:
            return "maximum"

    def learn_mrf(
        self,
        game,
        bet_id: str,
        lookback: int = 1000,
    ) -> float:
        """Learn MRF from historical data.

        MRF = P(correction | extremum)
        i.e., how often a local extremum is followed by a partial correction
        towards the mean within the next window.

        Returns a value between 0 and 1.
        """
        draws = self.history.get_draws(game.name, limit=lookback)
        if len(draws) < 100:
            return 0.35  # default, not enough data

        bet = game.get_bet(bet_id)
        p = bet.probability

        # Use a sliding approach: for each position, check if the
        # trailing Z-score was extreme and whether the next period
        # showed regression toward the mean.
        corrections = 0
        extremes = 0
        window = 50  # detection window

        for i in range(window, len(draws) - window):
            # Compute Z-score for the trailing window
            trailing_hits = sum(
                1 for d in draws[i - window : i] if bet_id in d.won_bet_ids
            )
            expected = window * p
            std = (window * p * (1 - p)) ** 0.5
            if std < 1e-10:
                continue
            z_before = (trailing_hits - expected) / std

            # Check if this was an extremum
            if abs(z_before) < 2.0:
                continue
            extremes += 1

            # Compute Z-score for the forward window
            forward_hits = sum(
                1 for d in draws[i : i + window] if bet_id in d.won_bet_ids
            )
            z_after = (forward_hits - expected) / std

            # Correction: Z moved toward zero (regression to mean)
            if abs(z_after) < abs(z_before):
                corrections += 1

        if extremes == 0:
            return 0.35

        mrf = corrections / extremes
        self.mrf = mrf
        return mrf
