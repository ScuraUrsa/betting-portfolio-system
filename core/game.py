"""Abstract game definition — the foundation of the entire system.

Every game (roulette, poker, dice, lottery) implements this interface.
The system is completely game-agnostic: it only needs a list of available bets.

Key insight: bets are NOT mutually exclusive outcomes. In roulette, you can
bet on "red" AND "num_17" — they overlap. The Game is a catalog of available
bets, each with its own theoretical probability and payout odds.
"""

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class Bet:
    """A single available bet in a game.

    Attributes:
        id: Unique identifier within the game (e.g. "red", "num_17")
        name: Human-readable name
        probability: Theoretical P(win), 0 < p < 1
        odds: Payout multiplier (e.g. 36.0 means "pays 36:1")
    """

    id: str
    name: str
    probability: float
    odds: float


@dataclass
class Game:
    """Abstract game — a catalog of available bets.

    Subclass or use factory functions for concrete games.
    The system only interacts with the .bets list.
    """

    name: str
    bets: list[Bet] = field(default_factory=list)

    @property
    def n_bets(self) -> int:
        return len(self.bets)

    def validate(self) -> None:
        """Ensure all bets have valid probabilities and odds."""
        seen_ids: set[str] = set()
        for b in self.bets:
            if b.id in seen_ids:
                raise ValueError(f"Duplicate bet ID '{b.id}' in game '{self.name}'")
            seen_ids.add(b.id)
            if not (0 < b.probability < 1):
                raise ValueError(
                    f"Bet '{b.id}' has invalid probability {b.probability} "
                    f"(must be 0 < p < 1)"
                )
            if b.odds <= 0:
                raise ValueError(f"Bet '{b.id}' has non-positive odds {b.odds}")

    def get_bet(self, bet_id: str) -> Bet:
        for b in self.bets:
            if b.id == bet_id:
                return b
        raise KeyError(f"Bet '{bet_id}' not found in game '{self.name}'")

    def expected_value(self, bet_id: str) -> float:
        """EV = p * odds - 1. Negative means house edge."""
        b = self.get_bet(bet_id)
        return b.probability * b.odds - 1.0
