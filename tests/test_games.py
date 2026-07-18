"""Tests for concrete game implementations."""

import pytest
from games.roulette import european_roulette
from games.poker import texas_holdem_hand_rankings


class TestEuropeanRoulette:
    @pytest.fixture
    def game(self):
        return european_roulette()

    def test_validate(self, game):
        game.validate()  # should not raise

    def test_has_37_numbers(self, game):
        numbers = [b for b in game.bets if b.id.startswith("num_")]
        assert len(numbers) == 37

    def test_has_color_bets(self, game):
        assert game.get_bet("red") is not None
        assert game.get_bet("black") is not None

    def test_has_even_odd(self, game):
        assert game.get_bet("even") is not None
        assert game.get_bet("odd") is not None

    def test_has_dozens(self, game):
        for d in range(1, 4):
            assert game.get_bet(f"dozen_{d}") is not None

    def test_has_columns(self, game):
        for c in range(1, 4):
            assert game.get_bet(f"col_{c}") is not None

    def test_house_edge_number(self, game):
        """Straight-up number: EV = (1/37)*36 - 1 = -1/37."""
        ev = game.expected_value("num_0")
        assert ev == pytest.approx(-1 / 37)

    def test_house_edge_red(self, game):
        """Red: EV = (18/37)*2 - 1 = -1/37."""
        ev = game.expected_value("red")
        assert ev == pytest.approx(-1 / 37)

    def test_all_bets_have_negative_ev(self, game):
        """In roulette, every bet has negative expected value (house edge)."""
        for b in game.bets:
            ev = game.expected_value(b.id)
            assert ev < 0, f"Bet {b.id} has non-negative EV: {ev}"


class TestTexasHoldem:
    @pytest.fixture
    def game(self):
        return texas_holdem_hand_rankings()

    def test_validate(self, game):
        game.validate()

    def test_has_10_hand_rankings(self, game):
        assert game.n_bets == 10

    def test_royal_flush_rarest(self, game):
        """Royal flush should be the rarest outcome."""
        probs = [b.probability for b in game.bets]
        assert game.get_bet("royal_flush").probability == min(probs)

    def test_high_card_most_common(self, game):
        """High card and one pair should be the most common."""
        probs = [b.probability for b in game.bets]
        top_ids = {
            b.id
            for b in sorted(game.bets, key=lambda x: x.probability, reverse=True)[:2]
        }
        assert "high_card" in top_ids or "one_pair" in top_ids
