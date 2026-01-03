"""Tests for side pot calculation."""
import pytest

from core.poker.betting import PlayerInHand
from core.poker.side_pots import SidePot, SidePotCalculator


def create_player(
    wallet: str,
    stack: int,
    current_bet: int = 0,
    is_active: bool = True,
    is_all_in: bool = False,
) -> PlayerInHand:
    """Helper to create a PlayerInHand."""
    return PlayerInHand(
        wallet=wallet,
        stack=stack,
        current_bet=current_bet,
        is_active=is_active,
        is_all_in=is_all_in,
    )


class TestSidePotCalculation:
    """Tests for SidePotCalculator.calculate."""

    def test_no_side_pots_no_all_in(self):
        """No side pots when no one is all-in."""
        players = [
            create_player("player1", 900, current_bet=100),
            create_player("player2", 900, current_bet=100),
            create_player("player3", 900, current_bet=100),
        ]
        calculator = SidePotCalculator()

        pots = calculator.calculate(players)

        assert len(pots) == 1
        assert pots[0].amount == 300
        assert len(pots[0].eligible_players) == 3

    def test_single_all_in_creates_side_pot(self):
        """Single all-in creates main pot and side pot."""
        players = [
            create_player("player1", 0, current_bet=500, is_all_in=True),  # All-in for 500
            create_player("player2", 500, current_bet=1000),  # Calls 1000
            create_player("player3", 500, current_bet=1000),  # Calls 1000
        ]
        calculator = SidePotCalculator()

        pots = calculator.calculate(players)

        assert len(pots) == 2
        # Main pot: 500 * 3 = 1500
        assert pots[0].amount == 1500
        assert len(pots[0].eligible_players) == 3
        # Side pot: 500 * 2 = 1000
        assert pots[1].amount == 1000
        assert len(pots[1].eligible_players) == 2
        assert "player1" not in pots[1].eligible_players

    def test_multiple_all_ins_different_amounts(self):
        """Multiple all-ins at different amounts create multiple pots.

        Player A: 1000 all-in
        Player B: 2000 all-in
        Player C: 5000 calls (or 2000 matched in this case)

        Results:
        - Main pot: 3000 (A, B, C eligible) - 1000 * 3
        - Side pot 1: 2000 (B, C eligible) - 1000 * 2
        """
        players = [
            create_player("player_a", 0, current_bet=1000, is_all_in=True),
            create_player("player_b", 0, current_bet=2000, is_all_in=True),
            create_player("player_c", 3000, current_bet=2000),
        ]
        calculator = SidePotCalculator()

        pots = calculator.calculate(players)

        assert len(pots) == 2
        # Main pot: 1000 * 3 = 3000
        assert pots[0].amount == 3000
        assert "player_a" in pots[0].eligible_players
        assert "player_b" in pots[0].eligible_players
        assert "player_c" in pots[0].eligible_players

        # Side pot: 1000 * 2 = 2000
        assert pots[1].amount == 2000
        assert "player_a" not in pots[1].eligible_players
        assert "player_b" in pots[1].eligible_players
        assert "player_c" in pots[1].eligible_players

    def test_folded_player_not_eligible(self):
        """Folded players contribute to pots but aren't eligible."""
        players = [
            create_player("player1", 900, current_bet=100, is_active=False),  # Folded
            create_player("player2", 900, current_bet=100),
            create_player("player3", 900, current_bet=100),
        ]
        calculator = SidePotCalculator()

        pots = calculator.calculate(players)

        assert len(pots) == 1
        assert pots[0].amount == 300
        assert len(pots[0].eligible_players) == 2
        assert "player1" not in pots[0].eligible_players


class TestSidePotDistribution:
    """Tests for SidePotCalculator.distribute."""

    def test_distribute_single_winner(self):
        """Single winner takes the whole pot."""
        pots = [
            SidePot(amount=1000, eligible_players=["player1", "player2", "player3"])
        ]
        hand_rankings = {
            "player1": 1,  # Best hand (lowest rank)
            "player2": 5,
            "player3": 10,
        }
        calculator = SidePotCalculator()

        winnings = calculator.distribute(pots, hand_rankings)

        assert winnings == {"player1": 1000}

    def test_distribute_split_pot_tie(self):
        """Tied players split the pot equally."""
        pots = [
            SidePot(amount=1000, eligible_players=["player1", "player2", "player3"])
        ]
        hand_rankings = {
            "player1": 1,  # Tied for best
            "player2": 1,  # Tied for best
            "player3": 10,
        }
        calculator = SidePotCalculator()

        winnings = calculator.distribute(pots, hand_rankings)

        assert winnings["player1"] == 500
        assert winnings["player2"] == 500

    def test_distribute_side_pot_winner_different_from_main(self):
        """Different players can win main pot and side pot."""
        pots = [
            SidePot(amount=3000, eligible_players=["player_a", "player_b", "player_c"]),
            SidePot(amount=2000, eligible_players=["player_b", "player_c"]),
        ]
        hand_rankings = {
            "player_a": 1,   # Best overall, but only eligible for main pot
            "player_b": 5,
            "player_c": 10,
        }
        calculator = SidePotCalculator()

        winnings = calculator.distribute(pots, hand_rankings)

        # Player A wins main pot
        assert winnings["player_a"] == 3000
        # Player B wins side pot (best among eligible)
        assert winnings["player_b"] == 2000

    def test_distribute_odd_chip_split(self):
        """Odd chips go to first winner in ties."""
        pots = [
            SidePot(amount=101, eligible_players=["player1", "player2"])
        ]
        hand_rankings = {
            "player1": 1,
            "player2": 1,
        }
        calculator = SidePotCalculator()

        winnings = calculator.distribute(pots, hand_rankings)

        # 101 / 2 = 50 each, with 1 remainder
        total = winnings["player1"] + winnings["player2"]
        assert total == 101
        assert winnings["player1"] in [50, 51]
        assert winnings["player2"] in [50, 51]


class TestSidePotRepr:
    """Tests for SidePot representation."""

    def test_repr(self):
        """SidePot has a readable repr."""
        pot = SidePot(amount=1000, eligible_players=["a", "b", "c"])
        assert repr(pot) == "SidePot(1000, eligible=3)"
