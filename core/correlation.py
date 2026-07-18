"""Correlation Engine — computes dependencies between bets.

For each bet, calculates:
- Positive correlation with other bets
- Negative correlation with other bets
- Impact on portfolio

In games like roulette, bets overlap (e.g., "red" and "num_17" both win on 17).
The correlation matrix captures these structural dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from core.game import Bet, Game


@dataclass
class CorrelationMatrix:
    """Square matrix of pairwise bet correlations."""

    bet_ids: list[str]
    matrix: np.ndarray  # shape (n_bets, n_bets), values in [-1, 1]

    def get_correlation(self, bet_id_a: str, bet_id_b: str) -> float:
        i = self.bet_ids.index(bet_id_a)
        j = self.bet_ids.index(bet_id_b)
        return float(self.matrix[i, j])

    def get_correlated_bets(
        self, bet_id: str, threshold: float = 0.3
    ) -> list[tuple[str, float]]:
        """Return bets correlated with bet_id above threshold."""
        i = self.bet_ids.index(bet_id)
        correlated = []
        for j, other_id in enumerate(self.bet_ids):
            if other_id == bet_id:
                continue
            corr = float(self.matrix[i, j])
            if abs(corr) >= threshold:
                correlated.append((other_id, corr))
        return sorted(correlated, key=lambda x: abs(x[1]), reverse=True)


class CorrelationEngine:
    """Computes correlation between bets.

    Two approaches:
    1. Structural: based on overlapping win conditions (roulette)
    2. Empirical: based on historical co-occurrence (any game)
    """

    def compute_structural(
        self,
        game: Game,
        win_sets: dict[str, set[str]],
    ) -> CorrelationMatrix:
        """Compute correlation from overlapping win conditions.

        Args:
            game: The game definition
            win_sets: Mapping from bet_id to set of raw outcomes that win that bet.
                      e.g., {"red": {"1","3","5",...}, "num_17": {"17"}}

        For roulette, win_sets can be derived from the bet definitions.
        """
        n = game.n_bets
        bet_ids = [b.id for b in game.bets]
        matrix = np.zeros((n, n))

        for i, bid_i in enumerate(bet_ids):
            set_i = win_sets.get(bid_i, set())
            if not set_i:
                continue
            for j, bid_j in enumerate(bet_ids):
                if i == j:
                    matrix[i, j] = 1.0
                    continue
                set_j = win_sets.get(bid_j, set())
                if not set_j:
                    continue

                # Jaccard-like correlation: |intersection| / sqrt(|A| * |B|)
                intersection = len(set_i & set_j)
                if intersection == 0:
                    matrix[i, j] = 0.0
                else:
                    denom = np.sqrt(len(set_i) * len(set_j))
                    matrix[i, j] = intersection / denom

        return CorrelationMatrix(bet_ids=bet_ids, matrix=matrix)

    def compute_empirical(
        self,
        game: Game,
        history,
        lookback: int = 1000,
    ) -> CorrelationMatrix:
        """Compute correlation from historical co-occurrence data.

        Uses Pearson correlation on binary win/loss vectors.
        """
        draws = history.get_draws(game.name, limit=lookback)
        if len(draws) < 10:
            n = game.n_bets
            return CorrelationMatrix(
                bet_ids=[b.id for b in game.bets],
                matrix=np.eye(n),
            )

        n = game.n_bets
        bet_ids = [b.id for b in game.bets]
        m = len(draws)

        # Build binary matrix: rows = draws, cols = bets
        data = np.zeros((m, n))
        for row, draw in enumerate(draws):
            for col, bid in enumerate(bet_ids):
                if bid in draw.won_bet_ids:
                    data[row, col] = 1.0

        # Pearson correlation
        matrix = np.corrcoef(data, rowvar=False)
        # Handle NaN (constant columns)
        matrix = np.nan_to_num(matrix, nan=0.0)

        return CorrelationMatrix(bet_ids=bet_ids, matrix=matrix)
