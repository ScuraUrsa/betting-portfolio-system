"""European Roulette — 37 fields (0-36).

Bets are NOT mutually exclusive — you can bet on "red" AND "num_17".
The Game is a catalog of available bets.
"""

from core.game import Bet, Game


def european_roulette() -> Game:
    """Create a European roulette game with standard bets.

    Bets include:
    - Straight-up numbers (0-36): p=1/37, odds=36
    - Red/Black: p=18/37, odds=2
    - Even/Odd: p=18/37, odds=2
    - Low(1-18)/High(19-36): p=18/37, odds=2
    - Dozens (1st12, 2nd12, 3rd12): p=12/37, odds=3
    - Columns (col1, col2, col3): p=12/37, odds=3
    """
    bets = []

    # Straight-up numbers
    for i in range(37):
        bets.append(Bet(id=f"num_{i}", name=str(i), probability=1 / 37, odds=36.0))

    # Red numbers (European roulette)
    red_numbers = {
        1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36,
    }

    bets.append(
        Bet(id="red", name="Red", probability=len(red_numbers) / 37, odds=2.0)
    )
    bets.append(
        Bet(
            id="black",
            name="Black",
            probability=(37 - 1 - len(red_numbers)) / 37,
            odds=2.0,
        )
    )

    # Even/Odd
    bets.append(Bet(id="even", name="Even", probability=18 / 37, odds=2.0))
    bets.append(Bet(id="odd", name="Odd", probability=18 / 37, odds=2.0))

    # Low/High
    bets.append(Bet(id="low", name="1-18", probability=18 / 37, odds=2.0))
    bets.append(Bet(id="high", name="19-36", probability=18 / 37, odds=2.0))

    # Dozens
    for d, name in enumerate(["1st12", "2nd12", "3rd12"], 1):
        bets.append(Bet(id=f"dozen_{d}", name=name, probability=12 / 37, odds=3.0))

    # Columns
    for c in range(1, 4):
        bets.append(Bet(id=f"col_{c}", name=f"Column {c}", probability=12 / 37, odds=3.0))

    game = Game(name="European Roulette", bets=bets)
    game.validate()
    return game
