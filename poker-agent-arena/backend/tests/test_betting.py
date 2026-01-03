"""Tests for betting logic."""
import pytest

from core.poker.betting import (
    Action,
    BettingRound,
    BettingState,
    InvalidActionError,
    PlayerInHand,
)


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


class TestValidActions:
    """Tests for get_valid_actions."""

    def test_valid_actions_no_bet(self):
        """Can check or raise when there's no bet."""
        players = [
            create_player("player1", 1000),
            create_player("player2", 1000),
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        valid_actions = betting_round.get_valid_actions()

        assert "check" in valid_actions
        assert "raise" in valid_actions
        assert "fold" not in valid_actions
        assert "call" not in valid_actions

    def test_valid_actions_with_bet(self):
        """Can fold, call, or raise when there's a bet."""
        players = [
            create_player("player1", 1000, current_bet=100),
            create_player("player2", 1000, current_bet=0),
        ]
        betting_round = BettingRound(players, pot=100, big_blind=20)
        betting_round.state.current_bet = 100
        betting_round.state.action_on = 1

        valid_actions = betting_round.get_valid_actions()

        assert "fold" in valid_actions
        assert "call" in valid_actions
        assert "raise" in valid_actions
        assert "check" not in valid_actions


class TestFold:
    """Tests for fold action."""

    def test_fold_removes_player_from_active(self):
        """Folding sets is_active to False and decreases num_active."""
        players = [
            create_player("player1", 1000, current_bet=100),
            create_player("player2", 1000, current_bet=0),
        ]
        betting_round = BettingRound(players, pot=100, big_blind=20)
        betting_round.state.current_bet = 100
        betting_round.state.action_on = 1

        initial_active = betting_round.state.num_active
        betting_round.apply_action(Action.fold())

        assert players[1].is_active is False
        assert betting_round.state.num_active == initial_active - 1


class TestCheck:
    """Tests for check action."""

    def test_check_when_no_bet(self):
        """Check is valid when there's no bet to call."""
        players = [
            create_player("player1", 1000),
            create_player("player2", 1000),
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        # Should not raise an exception
        betting_round.apply_action(Action.check())

        assert players[0].has_acted is True

    def test_check_invalid_with_bet(self):
        """Check raises InvalidActionError when there's a bet to call."""
        players = [
            create_player("player1", 1000, current_bet=100),
            create_player("player2", 1000, current_bet=0),
        ]
        betting_round = BettingRound(players, pot=100, big_blind=20)
        betting_round.state.current_bet = 100
        betting_round.state.action_on = 1

        with pytest.raises(InvalidActionError):
            betting_round.apply_action(Action.check())


class TestCall:
    """Tests for call action."""

    def test_call_matches_current_bet(self):
        """Call matches the current bet."""
        players = [
            create_player("player1", 1000, current_bet=100),
            create_player("player2", 1000, current_bet=0),
        ]
        betting_round = BettingRound(players, pot=100, big_blind=20)
        betting_round.state.current_bet = 100
        betting_round.state.action_on = 1

        betting_round.apply_action(Action.call())

        assert players[1].current_bet == 100
        assert players[1].stack == 900
        assert betting_round.state.pot == 200


class TestRaise:
    """Tests for raise action."""

    def test_raise_increases_bet(self):
        """Raise increases the current bet."""
        players = [
            create_player("player1", 1000),
            create_player("player2", 1000),
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        betting_round.apply_action(Action.raise_to(100))

        assert betting_round.state.current_bet == 100
        assert players[0].current_bet == 100
        assert players[0].stack == 900
        assert betting_round.state.pot == 100

    def test_raise_below_min_invalid(self):
        """Raise below minimum raises InvalidActionError."""
        players = [
            create_player("player1", 1000, current_bet=100),
            create_player("player2", 1000, current_bet=0),
        ]
        betting_round = BettingRound(players, pot=100, big_blind=20)
        betting_round.state.current_bet = 100
        betting_round.state.min_raise = 100
        betting_round.state.last_raise_amount = 100
        betting_round.state.action_on = 1

        # Min raise should be to 200 (100 + 100)
        # Trying to raise to 150 should fail
        with pytest.raises(InvalidActionError):
            betting_round.apply_action(Action.raise_to(150))

    def test_min_raise_calculation(self):
        """Min raise equals the last raise amount."""
        players = [
            create_player("player1", 2000),
            create_player("player2", 2000),
            create_player("player3", 2000),
        ]
        betting_round = BettingRound(players, pot=0, big_blind=20)

        # Player 1 raises to 100 (raise of 100)
        betting_round.apply_action(Action.raise_to(100))
        assert betting_round.state.min_raise == 100

        # Player 2 raises to 300 (raise of 200)
        betting_round.apply_action(Action.raise_to(300))
        assert betting_round.state.min_raise == 200

        # Player 3's min raise should be to 500 (300 + 200)
        # Raising to 400 should fail
        with pytest.raises(InvalidActionError):
            betting_round.apply_action(Action.raise_to(400))

        # Raising to 500 should succeed
        betting_round.apply_action(Action.raise_to(500))
        assert betting_round.state.current_bet == 500


class TestAllIn:
    """Tests for all-in scenarios."""

    def test_all_in_always_valid(self):
        """All-in is always valid even below min raise."""
        players = [
            create_player("player1", 1000, current_bet=500),
            create_player("player2", 100, current_bet=0),  # Short stack
        ]
        betting_round = BettingRound(players, pot=500, big_blind=20)
        betting_round.state.current_bet = 500
        betting_round.state.min_raise = 500
        betting_round.state.action_on = 1

        # Player 2 has only 100, but should be able to go all-in
        betting_round.apply_action(Action.raise_to(100))

        assert players[1].is_all_in is True
        assert players[1].stack == 0
        assert players[1].current_bet == 100


class TestRoundComplete:
    """Tests for round completion."""

    def test_round_complete_all_matched(self):
        """Round is complete when all have matched and acted."""
        players = [
            create_player("player1", 900, current_bet=100, has_acted=True),
            create_player("player2", 900, current_bet=100, has_acted=True),
        ]
        betting_round = BettingRound(players, pot=200, big_blind=20)
        betting_round.state.current_bet = 100

        # Manually set has_acted back since constructor resets it
        for p in players:
            p.has_acted = True

        assert betting_round.is_round_complete() is True

    def test_round_complete_all_folded_but_one(self):
        """Round is complete when all but one player folded."""
        players = [
            create_player("player1", 1000, is_active=True),
            create_player("player2", 1000, is_active=False),  # Folded
            create_player("player3", 1000, is_active=False),  # Folded
        ]
        betting_round = BettingRound(players, pot=100, big_blind=20)

        assert betting_round.is_round_complete() is True


class TestActionFactory:
    """Tests for Action class factory methods."""

    def test_fold_factory(self):
        """Action.fold() creates a fold action."""
        action = Action.fold()
        assert action.action_type == "fold"
        assert action.amount is None

    def test_check_factory(self):
        """Action.check() creates a check action."""
        action = Action.check()
        assert action.action_type == "check"
        assert action.amount is None

    def test_call_factory(self):
        """Action.call() creates a call action."""
        action = Action.call()
        assert action.action_type == "call"
        assert action.amount is None

    def test_raise_to_factory(self):
        """Action.raise_to(amount) creates a raise action with amount."""
        action = Action.raise_to(500)
        assert action.action_type == "raise"
        assert action.amount == 500
