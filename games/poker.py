"""Texas Hold'em poker hand rankings — theoretical probabilities.

Probabilities based on 7-card combinations (2 hole + 5 community).
Source: standard poker combinatorics (C(52,7) = 133,784,560).

Note: these are NOT mutually exclusive in the traditional sense
(you can't have both a flush AND a full house in one hand),
but for betting purposes each is a separate bet.
"""

from core.game import Bet, Game


def texas_holdem_hand_rankings() -> Game:
    """Create a poker game where bets are hand ranking outcomes.

    Each bet represents "player gets at least this hand rank".
    Probabilities are for a single player with 2 random hole cards
    and 5 community cards (7 cards total).
    """
    bets = [
        Bet(id="royal_flush", name="Royal Flush", probability=0.000032, odds=800.0),
        Bet(
            id="straight_flush",
            name="Straight Flush",
            probability=0.000279,
            odds=500.0,
        ),
        Bet(
            id="four_of_a_kind",
            name="Four of a Kind",
            probability=0.001680,
            odds=100.0,
        ),
        Bet(id="full_house", name="Full House", probability=0.025961, odds=25.0),
        Bet(id="flush", name="Flush", probability=0.030255, odds=20.0),
        Bet(id="straight", name="Straight", probability=0.046194, odds=15.0),
        Bet(
            id="three_of_a_kind",
            name="Three of a Kind",
            probability=0.048299,
            odds=10.0,
        ),
        Bet(id="two_pair", name="Two Pair", probability=0.234955, odds=3.0),
        Bet(id="one_pair", name="One Pair", probability=0.438225, odds=1.5),
        Bet(id="high_card", name="High Card", probability=0.174119, odds=1.0),
    ]

    game = Game(name="Texas Hold'em Hand Rankings", bets=bets)
    game.validate()
    return game
