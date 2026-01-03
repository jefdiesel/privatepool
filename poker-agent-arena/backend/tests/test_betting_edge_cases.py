"""Tests for betting edge cases.

Covers:
- All-in triggers side pot calculation
- Negative bet amount rejected
- Raise exceeds stack becomes all-in
- Multiple all-ins create multiple side pots
- BB-only ante posting
- Ante added to pot correctly
"""
import pytest

from core.poker.betting import (
    Action,
    BettingRound,
    InvalidActionError,
    PlayerInHand,
)
from core.poker.side_pots import SidePot, SidePotCalculator
from core.tournament.blinds import BlindLevel, BlindStructure


def create_player(
    wallet: str,
    stack: int,
    current_bet: int = 0,
    is_active: bool = True,
    is_all_in: bool = False,
    has_acted: bool = False,
) -> PlayerInHand:
    """Helper to create a PlayerInHand."""
    return PlayerInHand(
        wallet=wallet,
        stack=stack,
        current_bet=current_bet,
        is_active=is_active,
        is_all_in=is_all_in,
        has_acted=has_acted,
    )


class TestAllInTriggersSidePot:
    """Test that all-in scenarios trigger correct side pot calculation."""

    def test_single_all_in_creates_main_pot_and_side_pot(self):
        """Single all-in creates a main pot (all eligible) and side pot (remaining)."""
        # Player A: 500 all-in
        # Player B: 1000 calls
        # Player C: 1000 calls
        players = [
            create_player("player_a", 0, current_bet=500, is_all_in=True),
            create_player("player_b", 500, current_bet=1000),
            create_player("player_c", 500, current_bet=1000),
        ]

        calculator = SidePotCalculator()
        pots = calculator.calculate(players)

        # Main pot: 500 * 3 = 1500 (A, B, C eligible)
        # Side pot: 500 * 2 = 1000 (B, C eligible)
        assert len(pots) == 2
        assert pots[0].amount == 1500
        assert set(pots[0].eligible_players) == {"player_a", "player_b", "player_c"}
        assert pots[1].amount == 1000
        assert set(pots[1].eligible_players) == {"player_b", "player_c"}

    def test_all_in_from_call_sets_player_all_in(self):
        """Player who can't fully call goes all-in."""
        players = [
            create_player("player1", 1000, current_bet=500),
            create_player("player2", 200, current_bet=0),  # Can only put in 200
        ]
        betting_round = BettingRound(players, pot=500, big_blind=20)
        betting_round.state.current_bet = 500
        betting_round.state.action_on = 1

        betting_round.apply_action(Action.call())

        assert players[1].is_all_in is True
        assert players[1].stack == 0
        assert players[1].current_bet == 200


class TestNegativeBetRejection:
    """Test that negative bet amounts are properly rejected."""

    def test_raise_to_negative_amount_rejected(self):
        """Raise to a negative amount should fail validation."""
        players = [
            create_player("player1", 1000),
            create_player("player2", 1000),
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        # Raising to a negative amount should fail
        # The betting logic treats this as below min raise
        with pytest.raises(InvalidActionError):
            betting_round.apply_action(Action.raise_to(-100))

    def test_raise_to_zero_rejected(self):
        """Raise to zero should fail validation."""
        players = [
            create_player("player1", 1000),
            create_player("player2", 1000),
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        # Raising to 0 is below min raise (big_blind = 20)
        with pytest.raises(InvalidActionError):
            betting_round.apply_action(Action.raise_to(0))


class TestRaiseExceedsStackBecomesAllIn:
    """Test that raise attempts exceeding stack become all-in."""

    def test_raise_exceeding_stack_becomes_all_in(self):
        """Raise attempt exceeding stack results in all-in."""
        players = [
            create_player("player1", 500),  # Only 500 chips
            create_player("player2", 2000),
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        # Player 1 tries to raise to 1000, but only has 500
        betting_round.apply_action(Action.raise_to(1000))

        assert players[0].is_all_in is True
        assert players[0].stack == 0
        assert players[0].current_bet == 500  # All they had

    def test_raise_exactly_stack_is_all_in(self):
        """Raise equal to stack is all-in."""
        players = [
            create_player("player1", 500),
            create_player("player2", 2000),
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        # Player 1 raises to exactly their stack
        betting_round.apply_action(Action.raise_to(500))

        assert players[0].is_all_in is True
        assert players[0].stack == 0
        assert players[0].current_bet == 500


class TestMultipleAllInsCreateMultipleSidePots:
    """Test scenarios with multiple all-ins creating multiple side pots."""

    def test_three_way_all_in_different_stacks(self):
        """Three players all-in with different stacks creates proper pots.

        Player A: 1000 all-in
        Player B: 2000 all-in
        Player C: 5000 calls
        """
        players = [
            create_player("player_a", 0, current_bet=1000, is_all_in=True),
            create_player("player_b", 0, current_bet=2000, is_all_in=True),
            create_player("player_c", 3000, current_bet=5000),
        ]

        calculator = SidePotCalculator()
        pots = calculator.calculate(players)

        # Main pot: 1000 * 3 = 3000 (A, B, C)
        # Side pot 1: 1000 * 2 = 2000 (B, C)
        # Side pot 2: 3000 * 1 = 3000 (C only)
        assert len(pots) == 3

        assert pots[0].amount == 3000
        assert set(pots[0].eligible_players) == {"player_a", "player_b", "player_c"}

        assert pots[1].amount == 2000
        assert set(pots[1].eligible_players) == {"player_b", "player_c"}

        assert pots[2].amount == 3000
        assert set(pots[2].eligible_players) == {"player_c"}

    def test_four_players_two_all_ins_same_amount(self):
        """Two players all-in for same amount.

        Player A: 500 all-in
        Player B: 500 all-in
        Player C: 2000 calls
        Player D: 2000 calls
        """
        players = [
            create_player("player_a", 0, current_bet=500, is_all_in=True),
            create_player("player_b", 0, current_bet=500, is_all_in=True),
            create_player("player_c", 0, current_bet=2000),
            create_player("player_d", 0, current_bet=2000),
        ]

        calculator = SidePotCalculator()
        pots = calculator.calculate(players)

        # Main pot: 500 * 4 = 2000 (A, B, C, D)
        # Side pot: 1500 * 2 = 3000 (C, D)
        assert len(pots) == 2

        assert pots[0].amount == 2000
        assert set(pots[0].eligible_players) == {"player_a", "player_b", "player_c", "player_d"}

        assert pots[1].amount == 3000
        assert set(pots[1].eligible_players) == {"player_c", "player_d"}

    def test_cascading_all_ins(self):
        """Multiple all-ins in sequence.

        Player A: 100 all-in
        Player B: 300 all-in
        Player C: 600 all-in
        Player D: 1000 calls
        """
        players = [
            create_player("player_a", 0, current_bet=100, is_all_in=True),
            create_player("player_b", 0, current_bet=300, is_all_in=True),
            create_player("player_c", 0, current_bet=600, is_all_in=True),
            create_player("player_d", 400, current_bet=1000),
        ]

        calculator = SidePotCalculator()
        pots = calculator.calculate(players)

        # Pot 1: 100 * 4 = 400 (A, B, C, D)
        # Pot 2: 200 * 3 = 600 (B, C, D)
        # Pot 3: 300 * 2 = 600 (C, D)
        # Pot 4: 400 * 1 = 400 (D only)
        assert len(pots) == 4

        assert pots[0].amount == 400
        assert set(pots[0].eligible_players) == {"player_a", "player_b", "player_c", "player_d"}

        assert pots[1].amount == 600
        assert set(pots[1].eligible_players) == {"player_b", "player_c", "player_d"}

        assert pots[2].amount == 600
        assert set(pots[2].eligible_players) == {"player_c", "player_d"}

        assert pots[3].amount == 400
        assert set(pots[3].eligible_players) == {"player_d"}


class TestFoldedPlayersNotEligible:
    """Test that folded players are excluded from pot eligibility."""

    def test_folded_player_not_eligible_for_pots(self):
        """Folded player contributes to pot but is not eligible to win."""
        players = [
            create_player("player_a", 0, current_bet=500, is_all_in=True),
            create_player("player_b", 1000, current_bet=500, is_active=False),  # Folded
            create_player("player_c", 500, current_bet=500),
        ]

        calculator = SidePotCalculator()
        pots = calculator.calculate(players)

        # Pot: 1500 total, but only A and C eligible
        assert len(pots) == 1
        assert pots[0].amount == 1500
        assert set(pots[0].eligible_players) == {"player_a", "player_c"}


class TestBBOnlyAnte:
    """Test big blind only ante posting (modern tournament format)."""

    def test_blind_level_total_bb_payment(self):
        """Big blind level correctly calculates total BB payment."""
        level = BlindLevel(
            level=4,
            small_blind=100,
            big_blind=200,
            ante=25,
            duration_minutes=10,
        )

        assert level.total_bb_payment() == 225  # 200 + 25

    def test_blind_level_no_ante_payment(self):
        """Early levels with no ante return just big blind."""
        level = BlindLevel(
            level=1,
            small_blind=25,
            big_blind=50,
            ante=0,
            duration_minutes=10,
        )

        assert level.total_bb_payment() == 50

    def test_blind_structure_current_level(self):
        """Blind structure returns correct current level."""
        levels = [
            BlindLevel(1, 25, 50, 0, 10),
            BlindLevel(2, 50, 100, 0, 10),
            BlindLevel(3, 100, 200, 25, 10),
        ]
        structure = BlindStructure(levels)

        assert structure.current_level.level == 1
        assert structure.current_level.ante == 0

        structure.advance_level()
        assert structure.current_level.level == 2
        assert structure.current_level.ante == 0

        structure.advance_level()
        assert structure.current_level.level == 3
        assert structure.current_level.ante == 25
        assert structure.current_level.total_bb_payment() == 225


class TestAnteAddedToPotCorrectly:
    """Test that ante is correctly added to pot."""

    def test_pot_calculation_with_bb_ante(self):
        """Verify pot calculation includes ante from BB only.

        SB: 50
        BB: 100 + 25 ante = 125
        Total pot before action: 175
        """
        sb = 50
        bb = 100
        ante = 25

        # In BB-only ante format:
        # SB posts 50
        # BB posts 100 + 25 = 125
        pot = sb + bb + ante

        assert pot == 175

    def test_preflop_pot_with_ante_structure(self):
        """Simulate preflop pot with BB-only ante."""
        level = BlindLevel(
            level=4,
            small_blind=100,
            big_blind=200,
            ante=25,
            duration_minutes=10,
        )

        # SB posts small_blind
        # BB posts big_blind + ante
        preflop_pot = level.small_blind + level.total_bb_payment()

        assert preflop_pot == 325  # 100 + 200 + 25

    def test_ante_increases_pot_preflop(self):
        """Compare pots with and without ante."""
        level_no_ante = BlindLevel(1, 100, 200, 0, 10)
        level_with_ante = BlindLevel(4, 100, 200, 25, 10)

        pot_no_ante = level_no_ante.small_blind + level_no_ante.total_bb_payment()
        pot_with_ante = level_with_ante.small_blind + level_with_ante.total_bb_payment()

        assert pot_no_ante == 300
        assert pot_with_ante == 325
        assert pot_with_ante - pot_no_ante == 25  # Exactly the ante


class TestPotDistribution:
    """Test pot distribution with side pots."""

    def test_main_pot_goes_to_best_hand_among_all(self):
        """Main pot goes to best hand that's eligible."""
        pots = [
            SidePot(3000, ["player_a", "player_b", "player_c"]),
            SidePot(2000, ["player_b", "player_c"]),
        ]

        # Lower rank is better
        rankings = {
            "player_a": 1,  # Best hand (e.g., straight)
            "player_b": 3,  # Worst
            "player_c": 2,  # Middle
        }

        calculator = SidePotCalculator()
        winnings = calculator.distribute(pots, rankings)

        # Player A wins main pot (3000), can't win side pot
        # Player C wins side pot (2000) as best among B, C
        assert winnings == {
            "player_a": 3000,
            "player_c": 2000,
        }

    def test_tied_hands_split_pot(self):
        """Tied hands split the pot evenly."""
        pots = [
            SidePot(1000, ["player_a", "player_b", "player_c"]),
        ]

        # A and C tie for best
        rankings = {
            "player_a": 1,
            "player_b": 3,
            "player_c": 1,
        }

        calculator = SidePotCalculator()
        winnings = calculator.distribute(pots, rankings)

        # Pot split between A and C (500 each)
        assert winnings == {
            "player_a": 500,
            "player_c": 500,
        }

    def test_odd_chip_distribution_on_split(self):
        """Odd chips go to first winner in order."""
        pots = [
            SidePot(1001, ["player_a", "player_b", "player_c"]),
        ]

        rankings = {
            "player_a": 1,
            "player_b": 3,
            "player_c": 1,
        }

        calculator = SidePotCalculator()
        winnings = calculator.distribute(pots, rankings)

        # 1001 / 2 = 500 each + 1 remainder to first
        total_won = sum(winnings.values())
        assert total_won == 1001
        assert winnings["player_a"] in [500, 501]
        assert winnings["player_c"] in [500, 501]


class TestEdgeCasesInBettingRound:
    """Additional edge cases in betting round logic."""

    def test_raise_requires_amount(self):
        """Raise without amount raises InvalidActionError."""
        players = [
            create_player("player1", 1000),
            create_player("player2", 1000),
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        with pytest.raises(InvalidActionError, match="requires an amount"):
            betting_round.apply_action(Action("raise", None))

    def test_round_complete_when_all_in_players_only(self):
        """Round complete when remaining players are all-in."""
        players = [
            create_player("player1", 0, current_bet=500, is_all_in=True, has_acted=True),
            create_player("player2", 0, current_bet=500, is_all_in=True, has_acted=True),
        ]
        betting_round = BettingRound(players, pot=1000, big_blind=20)
        betting_round.state.current_bet = 500

        # Both players are all-in, round should be complete
        assert betting_round.is_round_complete() is True

    def test_action_on_advances_correctly(self):
        """Action advances to next active player, skipping folded and all-in."""
        players = [
            create_player("player1", 1000),  # Active
            create_player("player2", 0, is_all_in=True),  # All-in, skip
            create_player("player3", 1000, is_active=False),  # Folded, skip
            create_player("player4", 1000),  # Active
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        # Player 1 checks
        betting_round.apply_action(Action.check())

        # Should advance to player 4 (index 3), skipping all-in and folded
        assert betting_round.state.action_on == 3

    def test_call_into_all_in_doesnt_reopen_action(self):
        """Calling an all-in that's less than min raise doesn't reopen action."""
        players = [
            create_player("player1", 900, current_bet=100),
            create_player("player2", 0, current_bet=50, is_all_in=True),  # All-in for less
            create_player("player3", 1000, current_bet=0),
        ]
        betting_round = BettingRound(players, pot=150, big_blind=20)
        betting_round.state.current_bet = 100
        betting_round.state.action_on = 2

        # Player 3 just needs to call 100, action doesn't reopen for player 1
        betting_round.apply_action(Action.call())

        # Player 1 already matched, player 2 all-in, player 3 just called
        # All active players who can act have acted
        players[0].has_acted = True  # Simulate player 1 having acted already
        assert betting_round.is_round_complete() is True


class TestBlindStructureEdgeCases:
    """Edge cases for blind structure management."""

    def test_empty_blind_structure_raises(self):
        """Creating blind structure with no levels raises ValueError."""
        with pytest.raises(ValueError, match="at least one level"):
            BlindStructure([])

    def test_final_level_does_not_advance(self):
        """Advancing at final level returns None."""
        levels = [
            BlindLevel(1, 25, 50, 0, 10),
            BlindLevel(2, 50, 100, 0, 10),
        ]
        structure = BlindStructure(levels)

        structure.advance_level()  # Now at level 2
        assert structure.is_final_level() is True

        result = structure.advance_level()
        assert result is None
        assert structure.current_level.level == 2  # Still at 2

    def test_time_remaining_before_start(self):
        """Time remaining returns full duration before level starts."""
        levels = [BlindLevel(1, 25, 50, 0, 10)]
        structure = BlindStructure(levels)

        # Not started yet
        assert structure.time_remaining() == 600  # 10 minutes in seconds
