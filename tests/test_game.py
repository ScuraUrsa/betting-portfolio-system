"""Tests for core.game — the abstract Game and Bet classes."""

import pytest
from core.game import Bet, Game


class TestBet:
    def test_creation(self):
        b = Bet(id="test", name="Test", probability=0.5, odds=2.0)
        assert b.id == "test"
        assert b.name == "Test"
        assert b.probability == 0.5
        assert b.odds == 2.0

    def test_immutable(self):
        b = Bet(id="test", name="Test", probability=0.5, odds=2.0)
        with pytest.raises(Exception):
            b.probability = 0.6  # frozen dataclass


class TestGame:
    def test_empty_game(self):
        g = Game(name="Empty")
        assert g.name == "Empty"
        assert g.n_bets == 0

    def test_validate_success(self):
        g = Game(
            name="Fair Coin",
            bets=[
                Bet(id="heads", name="Heads", probability=0.5, odds=2.0),
                Bet(id="tails", name="Tails", probability=0.5, odds=2.0),
            ],
        )
        g.validate()  # should not raise

    def test_validate_duplicate_id(self):
        g = Game(
            name="Dupes",
            bets=[
                Bet(id="a", name="A", probability=0.5, odds=2.0),
                Bet(id="a", name="A again", probability=0.5, odds=2.0),
            ],
        )
        with pytest.raises(ValueError, match="Duplicate"):
            g.validate()

    def test_validate_invalid_probability(self):
        g = Game(
            name="Bad",
            bets=[
                Bet(id="a", name="A", probability=1.5, odds=2.0),
            ],
        )
        with pytest.raises(ValueError, match="invalid probability"):
            g.validate()

    def test_validate_non_positive_odds(self):
        g = Game(
            name="Bad",
            bets=[
                Bet(id="a", name="A", probability=0.5, odds=0),
            ],
        )
        with pytest.raises(ValueError, match="non-positive odds"):
            g.validate()

    def test_get_bet(self):
        g = Game(
            name="Test",
            bets=[
                Bet(id="a", name="A", probability=0.5, odds=2.0),
                Bet(id="b", name="B", probability=0.5, odds=2.0),
            ],
        )
        b = g.get_bet("a")
        assert b.id == "a"
        assert b.name == "A"

    def test_get_bet_missing(self):
        g = Game(
            name="Test",
            bets=[Bet(id="a", name="A", probability=1.0, odds=2.0)],
        )
        with pytest.raises(KeyError, match="'missing'"):
            g.get_bet("missing")

    def test_expected_value_fair_coin(self):
        """EV for a fair coin at odds 2:1 should be 0 (no edge)."""
        g = Game(
            name="Fair Coin",
            bets=[
                Bet(id="heads", name="Heads", probability=0.5, odds=2.0),
                Bet(id="tails", name="Tails", probability=0.5, odds=2.0),
            ],
        )
        assert g.expected_value("heads") == pytest.approx(0.0)

    def test_expected_value_negative(self):
        """EV for roulette number: (1/37)*36 - 1 = -1/37 ≈ -0.027."""
        g = Game(
            name="Roulette",
            bets=[Bet(id="num_0", name="0", probability=1 / 37, odds=36.0)],
        )
        assert g.expected_value("num_0") == pytest.approx(-1 / 37)

    def test_n_bets(self):
        g = Game(
            name="Test",
            bets=[
                Bet(id="a", name="A", probability=0.5, odds=2.0),
                Bet(id="b", name="B", probability=0.5, odds=2.0),
            ],
        )
        assert g.n_bets == 2
